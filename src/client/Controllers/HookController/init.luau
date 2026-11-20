--!strict
--[[
	Gancho do jogador local, Fase 1: só em superfícies (RF-10..14, RF-17..19; ADR 0016, 0036, 0039, 0042).

	- Disparo: o gancho voa (`Config.Hook.FireSpeed`) na direção da mira, a partir da posição do disparo;
	  prende no primeiro alvo válido, ou volta ao personagem (proibido, alcance esgotado ou botão solto).
	  Estados: Idle, Flying, Attached, Retracting.
	- Modo "DDNet" (padrão): segurar mantém preso e o puxão segue a física do DDNet (`DDNetPhysics`).
	- Modo "Pull" (referência, ADR 0042): um clique prende e puxa o personagem
	  até o ponto (`PullPhysics`). Segurando ao chegar, fica preso ali até soltar; já solto, o gancho
	  solta ao chegar e sobra parte do embalo. Clicar em outro alvo durante o voo troca de alvo.
	  Modo "Swing" (referência, ADR 0036): segurar mantém preso, soltar solta na hora (`SwingPhysics`).
	  Pressionar durante a recarga (`Config.Hook.Cooldown`) dispara assim que ela acabar, se ainda segurado.
	- Mira: o cursor vira um ponto do plano (raio da câmera ∩ plano Z); o gancho sai do HumanoidRootPart
	  nessa direção, em 360°, até `Config.Hook.Range`. Primeiro um Raycast; se não achar alvo válido, um
	  Spherecast com raio `AimAssistRadius` no mesmo caminho (esfera de ajuda, RF-10b).
	- Só prende em peça na profundidade do plano; roxo (`NoHook`) nunca; verde (`HookOnce`) uma vez por vida
	  ou checkpoint. O cliente decide na hora; o servidor (HookService) confere e pode recusar (`HookRejected`).
	- No puxão, W/S não fazem nada no gancho (o `CharacterController` continua bloqueando a profundidade).
	  No balanço: A/D empurram, W recolhe e S solta corda. Controle do corpo e embalo depois de soltar
	  em `AirBody` (A/D dão controle no ar durante o embalo).
	- Retículo em três estados (sem alvo, válido, proibido) em `Reticle`; corda visível só localmente
	  (para os outros jogadores: Fase 4).
]]

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Aim = require(ReplicatedStorage.Shared.Logic.Aim)
local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local HookSurface = require(ReplicatedStorage.Shared.Util.HookSurface)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local Net = require(ReplicatedStorage.Shared.Net)
local Trove = require(ReplicatedStorage.Packages.Trove)

local AirBody = require(script.AirBody)
local CharacterController = require(script.Parent.CharacterController)
local DDNetPhysics = require(script.DDNetPhysics)
local HookPhysics = require(script.HookPhysics)
local PlayerHookPhysics = require(script.PlayerHookPhysics)
local PullPhysics = require(script.PullPhysics)
local Reticle = require(script.Reticle)
local SwingPhysics = require(script.SwingPhysics)

type Target = {
	state: HookRules.TargetState,
	part: BasePart?,
	point: Vector3?, -- ponto no plano onde o gancho prenderia
	player: Player?, -- gancho em outro jogador: o alvo (part = root dele)
}

type CharacterContext = {
	character: Model,
	humanoid: Humanoid,
	root: BasePart,
	rootAttachment: Attachment,
	trove: Trove.Trove,
}

type Attached = {
	id: number,
	part: BasePart,
	anchor: Attachment,
	hookOnceKey: Instance?,
	physics: HookPhysics.Physics,
	trove: Trove.Trove,
}

-- Gancho no ar: "Flying" indo na direção da mira, "Retracting" voltando ao personagem sem prender.
type Flight = {
	state: "Flying" | "Retracting",
	position: Vector3,
	direction: Vector3,
	traveled: number,
	tip: Attachment,
	trove: Trove.Trove,
}

-- Um módulo de física por tipo de gancho (ADR 0036, 0042).
local MODES: { [string]: HookPhysics.Mode } = {
	DDNet = DDNetPhysics.mode,
	Pull = PullPhysics.mode,
	Swing = SwingPhysics.mode,
}

local MAX_CAST_STEPS = 8 -- peças fora do plano atravessadas num mesmo trecho do voo
local CAST_SKIP = 0.05 -- studs para continuar o raio depois de uma peça fora do plano

local settings = Config.Hook
local planeZ = Config.Plane.Z
local player = Players.LocalPlayer

local NO_TARGET: Target = { state = "None" }

local HookController = {}

local mode: HookPhysics.Mode? = MODES[settings.Mode]
local attachRemote: RemoteEvent? = nil
local detachRemote: RemoteEvent? = nil
local reticle: Reticle.Reticle? = nil

local raycastParams = RaycastParams.new()
raycastParams.FilterType = Enum.RaycastFilterType.Exclude
raycastParams.RespectCanCollide = settings.IgnoreNonCollidable

local context: CharacterContext? = nil
local attached: Attached? = nil
local flight: Flight? = nil
-- Corpo sem controle do Humanoid: existe enquanto preso e durante o embalo depois de soltar.
local airBody: AirBody.AirBody? = nil
local attachCounter = 0
local lastAttachTime = -math.huge
local firePending = false -- botão pressionado esperando a recarga acabar
local buttonHeld = false -- botão do gancho apertado agora
local reelInHeld = false
local reelOutHeld = false
local usedHookOnce: { [Instance]: boolean } = {} -- espelho local; quem manda é o servidor
local lastResult = "None" -- resultado da última tentativa (para testes)
local lastTargetState: HookRules.TargetState = "None"

-- Entradas simuladas para testes no Studio (ver `HookController.debug`). nil = mouse/teclado de verdade.
local aimOverride: Vector3? = nil
local horizontalOverride: number? = nil
local reelOverride: number? = nil

local function isSolo(character: Model?): boolean
	return character ~= nil and character:GetAttribute(Config.Attributes.Solo) == true
end

-- O gancho acerta outros jogadores (DDNet). Ignora o próprio personagem e quem está em solo; em solo,
-- ignora todos (modo fantasma).
local playerTargets: { Instance } = {} -- personagens que o gancho pode acertar (fora o próprio e solo)

local function refreshFilter()
	local exclude: { Instance } = {}
	table.clear(playerTargets)
	local selfSolo = isSolo(player.Character)
	for _, other in Players:GetPlayers() do
		local character = other.Character
		if character then
			-- O raio do mundo nunca acerta personagens; os que valem vão para o raio de jogadores.
			table.insert(exclude, character)
			if other ~= player and not selfSolo and not isSolo(character) then
				table.insert(playerTargets, character)
			end
		end
	end
	raycastParams.FilterDescendantsInstances = exclude
end

local function getOrigin(ctx: CharacterContext): Vector3
	return Aim.toPlane(ctx.root.Position, planeZ)
end

-- Ponto do plano sob o cursor (ou o ponto simulado nos testes).
local function getAimPoint(): Vector3?
	if aimOverride then
		return aimOverride
	end
	local mouse = UserInputService:GetMouseLocation()
	local ray = workspace.CurrentCamera:ViewportPointToRay(mouse.X, mouse.Y)
	return Aim.intersectPlane(ray.Origin, ray.Direction, planeZ)
end

local function isHookOnceUsed(part: BasePart): boolean
	local key = HookSurface.getHookOnceKey(part)
	return key ~= nil and usedHookOnce[key] == true
end

-- Classifica o que o Raycast/Spherecast acertou.
local function evaluateHit(result: RaycastResult?): Target
	if not result then
		return NO_TARGET
	end
	local part = result.Instance
	if not part:IsA("BasePart") then
		return NO_TARGET
	end
	-- Corpo de outro jogador: prende nele (o ponto é o root, que acompanha o jogador).
	local owner = PlayerHookPhysics.playerFromPart(part)
	if owner then
		local character = owner.Character
		local ownerRoot = character and character:FindFirstChild("HumanoidRootPart")
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		if
			owner == player
			or not ownerRoot
			or not ownerRoot:IsA("BasePart")
			or not humanoid
			or humanoid.Health <= 0
		then
			return NO_TARGET
		end
		return { state = "Valid", part = ownerRoot, point = ownerRoot.Position, player = owner }
	end
	-- Hookthrough e mão única: o gancho atravessa (o raio continua depois deles).
	if part:HasTag(Config.Tags.HookThrough) or part:HasTag(Config.Tags.OneWay) then
		return NO_TARGET
	end
	local point = Aim.toPlane(result.Position, planeZ)
	-- Só vale peça na profundidade do plano: o ponto levado ao plano tem de continuar na peça.
	-- (O raio já corre no plano; a esfera alcança alguns studs para fora dele.)
	if
		not part:IsA("Terrain")
		and not HookRules.pointOnPart(part.CFrame, part.Size, point, settings.SurfaceTolerance)
	then
		return NO_TARGET
	end
	local kind = HookSurface.getKind(part)
	local state: HookRules.TargetState = if HookRules.canAttach(kind, isHookOnceUsed(part))
		then "Valid"
		else "Forbidden"
	return { state = state, part = part, point = point }
end

-- Raio no plano de `origin` ao longo de `castVector`. Peças fora da profundidade do plano (cenário de
-- fundo) não param o gancho: o raio continua depois delas.
local function castWorld(origin: Vector3, castVector: Vector3): Target
	local remaining = castVector.Magnitude
	if remaining <= 0 then
		return NO_TARGET
	end
	local direction = castVector / remaining
	local from = origin
	for _ = 1, MAX_CAST_STEPS do
		local result = workspace:Raycast(from, direction * remaining, raycastParams)
		if not result then
			return NO_TARGET
		end
		local target = evaluateHit(result)
		if target.state ~= "None" then
			return target
		end
		local advanced = (result.Position - from):Dot(direction) + CAST_SKIP
		remaining -= advanced
		if remaining <= 0 then
			return NO_TARGET
		end
		from += direction * advanced
	end
	return NO_TARGET
end

-- Jogadores num raio à parte, que não depende de colisão: pendurado no gancho (estado Physics) o corpo
-- do outro fica sem colisão e o raio do mundo o atravessava. Vale o que vier primeiro no caminho.
-- Hitbox do jogador como no DDNet: o gancho acerta se passar a até `PlayerHitRadius` do centro dele
-- (DDNet: raio físico + 2 = 30 unidades), mesmo sem tocar no corpo. Devolve o mais próximo no caminho.
local function nearestPlayerOnSegment(origin: Vector3, castVector: Vector3): (Target?, number)
	local lengthSquared = castVector:Dot(castVector)
	local best: Target? = nil
	local bestDistance = math.huge
	if lengthSquared <= 0 then
		return nil, bestDistance
	end
	for _, character in playerTargets do
		local owner = Players:GetPlayerFromCharacter(character :: Model)
		local otherRoot = (character :: Model):FindFirstChild("HumanoidRootPart")
		local humanoid = (character :: Model):FindFirstChildOfClass("Humanoid")
		if owner and otherRoot and otherRoot:IsA("BasePart") and humanoid and humanoid.Health > 0 then
			local center = Aim.toPlane(otherRoot.Position, planeZ)
			local t = math.clamp((center - origin):Dot(castVector) / lengthSquared, 0, 1)
			local closest = origin + castVector * t
			local along = t * math.sqrt(lengthSquared)
			if (center - closest).Magnitude <= settings.PlayerHitRadius and along < bestDistance then
				bestDistance = along
				best = { state = "Valid", part = otherRoot, point = otherRoot.Position, player = owner }
			end
		end
	end
	return best, bestDistance
end

local function castSegment(origin: Vector3, castVector: Vector3): Target
	local playerTarget, playerDistance = nearestPlayerOnSegment(origin, castVector)
	if not playerTarget then
		return castWorld(origin, castVector)
	end
	if playerDistance > 0 then
		local worldTarget = castWorld(origin, castVector.Unit * playerDistance)
		if worldTarget.state ~= "None" then
			return worldTarget -- parede/bloco antes do jogador
		end
	end
	return playerTarget
end

local function findTarget(origin: Vector3, aimPoint: Vector3): Target
	local castVector = Aim.castVector(origin, aimPoint, settings.Range)
	if not castVector then
		return NO_TARGET
	end
	refreshFilter()

	local rayTarget = castSegment(origin, castVector)
	if rayTarget.state == "Valid" or settings.AimAssistRadius <= 0 then
		return rayTarget
	end
	local sphereTarget =
		evaluateHit(workspace:Spherecast(origin, settings.AimAssistRadius, castVector, raycastParams))
	if sphereTarget.state == "Valid" then
		return sphereTarget
	end
	if rayTarget.state == "Forbidden" then
		return rayTarget
	end
	return sphereTarget
end

-- Atributo local no personagem: true enquanto o gancho controla o corpo (preso ou embalo).
-- O MovementController lê para travar e recarregar o pulo duplo (ADR 0043).
local function publishHookActive()
	local ctx = context
	if ctx then
		ctx.character:SetAttribute(Config.Movement.HookActiveAttribute, attached ~= nil or airBody ~= nil)
	end
end

local function endAirBody()
	local body = airBody
	airBody = nil
	if body then
		body:destroy()
	end
	publishHookActive()
end

-- Solta a corda. O corpo continua no embalo (AirBody) até pousar ou perder velocidade.
local function release(notifyServer: boolean)
	local current = attached
	if not current then
		return
	end
	attached = nil
	current.trove:Destroy()
	if airBody then
		airBody:beginMomentum()
	end
	if notifyServer and detachRemote then
		detachRemote:FireServer(current.id)
	end
	publishHookActive()
end

local function attach(ctx: CharacterContext, part: BasePart, point: Vector3, targetPlayer: Player?)
	local currentMode = mode
	if not currentMode then
		return
	end
	attachCounter += 1
	local trove = Trove.new()

	local anchor = Instance.new("Attachment")
	anchor.Name = "HookAnchor"
	anchor.Position = part.CFrame:PointToObjectSpace(point)
	anchor.Parent = part

	-- Prender de novo durante o embalo reaproveita o mesmo corpo (sem devolver o controle ao Humanoid).
	local body = airBody or AirBody.new(ctx.character, ctx.humanoid, ctx.root, ctx.rootAttachment)
	airBody = body
	body:cancelMomentum()
	body:setAimPoint(anchor) -- braço da pose de voo aponta para o ponto preso (beginMomentum tira)

	local params = {
		character = ctx.character,
		root = ctx.root,
		rootAttachment = ctx.rootAttachment,
		anchor = anchor,
		body = body,
	}
	local physics = if targetPlayer
		then PlayerHookPhysics.new({
			character = params.character,
			root = params.root,
			rootAttachment = params.rootAttachment,
			anchor = params.anchor,
			body = params.body,
			target = targetPlayer,
		})
		else currentMode.new(params)
	trove:Add(function()
		physics:destroy()
	end)
	trove:Add(anchor)

	local hookOnceKey = HookSurface.getHookOnceKey(part)
	if hookOnceKey then
		usedHookOnce[hookOnceKey] = true
	end
	lastAttachTime = os.clock()
	attached = {
		id = attachCounter,
		part = part,
		anchor = anchor,
		hookOnceKey = hookOnceKey,
		physics = physics,
		trove = trove,
	}
	publishHookActive()
	if attachRemote then
		attachRemote:FireServer(attachCounter, part, point)
	end
end

local function endFlight()
	local current = flight
	flight = nil
	if current then
		current.trove:Destroy()
	end
end

local function startRetract()
	local current = flight
	if current then
		current.state = "Retracting"
	end
end

local function startFlight(ctx: CharacterContext, direction: Vector3)
	endFlight()
	local trove = Trove.new()
	local origin = getOrigin(ctx)
	local tip = Instance.new("Attachment")
	tip.Name = "HookTip"
	tip.WorldPosition = origin
	tip.Parent = workspace.Terrain
	trove:Add(tip)
	trove:Add(HookPhysics.createRope(ctx.rootAttachment, tip, ctx.root))
	flight = {
		state = "Flying",
		position = origin,
		direction = direction,
		traveled = 0,
		tip = tip,
		trove = trove,
	}
end

-- Avança o gancho no ar. Voando: anda `FireSpeed` na direção do disparo (independente de onde o
-- personagem vai) e prende no primeiro alvo válido; superfície proibida ou alcance esgotado o fazem
-- voltar. Voltando: segue o personagem até chegar nele.
local function stepFlight(ctx: CharacterContext, dt: number)
	local current = flight
	if not current then
		return
	end
	local step = settings.FireSpeed * dt
	if current.state == "Retracting" then
		local toOrigin = getOrigin(ctx) - current.position
		if toOrigin.Magnitude <= step then
			endFlight()
			return
		end
		current.position += toOrigin.Unit * step
		current.tip.WorldPosition = current.position
		return
	end

	step = math.min(step, settings.Range - current.traveled)
	refreshFilter()
	local target = castSegment(current.position, current.direction * step)
	if target.state == "Valid" and target.part and target.point then
		endFlight()
		release(true) -- troca de alvo (modos que permitem): o corpo continua o mesmo
		attach(ctx, target.part, target.point, target.player)
		lastResult = if target.player then "AttachedPlayer" else "Attached"
		return
	end
	if target.state == "Forbidden" and target.point then
		current.position = target.point
		current.tip.WorldPosition = current.position
		lastResult = "Forbidden"
		if reticle then
			reticle:flashForbidden()
		end
		startRetract()
		return
	end
	current.position += current.direction * step
	current.traveled += step
	current.tip.WorldPosition = current.position
	if current.traveled >= settings.Range then
		lastResult = "NoTarget"
		startRetract()
	end
end

-- Congelado (atributo do ZoneService, RF-20) não usa o gancho.
local function isFrozen(ctx: CharacterContext): boolean
	return Zones.isFrozen(ctx.character:GetAttribute(Config.Attributes.FrozenUntil))
end

local function canRetarget(): boolean
	return mode ~= nil and mode.retargetWhileAttached
end

local function tryFire()
	local ctx = context
	if not ctx or (attached and not canRetarget()) or ctx.humanoid.Health <= 0 then
		lastResult = "Unavailable"
		return
	end
	if isFrozen(ctx) then
		lastResult = "Frozen"
		return
	end
	if flight then
		lastResult = "Unavailable" -- gancho ainda no ar
		return
	end
	local aimPoint = getAimPoint()
	local origin = getOrigin(ctx)
	local direction = aimPoint and Aim.planarDirection(origin, aimPoint)
	if not direction then
		lastResult = "NoAim"
		return
	end
	-- O gancho sai voando; quem prende (ou volta) é o `stepFlight`. Alvo inválido não interrompe o
	-- gancho já preso nos modos que trocam de alvo.
	startFlight(ctx, direction)
	lastResult = "Flying"
end

local function processPendingFire()
	if not firePending or (attached and not canRetarget()) or not context then
		return
	end
	if not HookRules.cooldownReady(lastAttachTime, os.clock(), settings.Cooldown) then
		return -- ainda na recarga: tenta de novo no próximo quadro, se o botão continuar segurado
	end
	firePending = false
	tryFire()
end

local function pressFire()
	buttonHeld = true
	firePending = true
	processPendingFire()
end

local function releaseFire()
	buttonHeld = false
	firePending = false
	-- No puxão, soltar o botão não solta o gancho: ele segue até o ponto (a física decide ao chegar).
	if mode and mode.releaseOnButtonUp then
		startRetract() -- soltou com o gancho ainda voando: ele volta
		release(true)
	end
end

local function getInput(ctx: CharacterContext): HookPhysics.Input
	local horizontal: number = if horizontalOverride ~= nil
		then horizontalOverride
		else math.clamp(ctx.humanoid.MoveDirection.X, -1, 1)
	local keyboardReel = (if reelOutHeld then 1 else 0) - (if reelInHeld then 1 else 0)
	local reel: number = if reelOverride ~= nil then reelOverride else keyboardReel
	return { horizontal = horizontal, reel = reel, held = buttonHeld }
end

-- Puxões que outros jogadores aplicam em mim (DDNet: quem é puxado recebe 1,5x, na direção de quem
-- puxa). O servidor marca `HookTarget` no personagem de quem puxa; cada cliente simula o próprio corpo,
-- então o puxão é aplicado aqui. Enquanto puxado, o AirBody controla o corpo (senão o Humanoid freia).
local beingPulled = false
local INCOMING_TICK = 1 / settings.TickRate

local function applyIncomingPulls(ctx: CharacterContext, dt: number)
	local pulled = false
	local puller: Attachment? = nil
	if not isSolo(ctx.character) and ctx.humanoid.Health > 0 then
		local velocity = ctx.root.AssemblyLinearVelocity
		local ticks = math.min(dt / INCOMING_TICK, 4)
		for _, other in Players:GetPlayers() do
			local character = other.Character
			if
				other ~= player
				and character
				and character:GetAttribute(Config.Attributes.HookTarget) == player.UserId
			then
				local otherRoot = character:FindFirstChild("HumanoidRootPart")
				if otherRoot and otherRoot:IsA("BasePart") then
					local distance = (otherRoot.Position - ctx.root.Position).Magnitude
					-- Começa a puxar fora da distância mínima; já sendo puxado, continua até soltar (sem
					-- ligar/desligar o corpo e a pose a cada quadro quando chega perto de quem puxa).
					if beingPulled or distance > settings.PlayerPullMinDistance then
						pulled = true
						local attachment = otherRoot:FindFirstChild("RootAttachment")
						puller = if attachment and attachment:IsA("Attachment") then attachment else puller
					end
					velocity = HookRules.playerPull(
						velocity,
						ctx.root.Position,
						otherRoot.Position,
						settings.PlayerPullHookedFactor,
						PlayerHookPhysics.PULL,
						ticks
					)
				end
			end
		end
		if pulled then
			if not airBody then
				airBody = AirBody.new(ctx.character, ctx.humanoid, ctx.root, ctx.rootAttachment)
				publishHookActive()
			end
			local body = airBody :: AirBody.AirBody
			body:takeOff() -- no chão o Humanoid anularia o puxão
			body:cancelMomentum()
			if not attached then
				body:setAimPoint(puller) -- pose de voo como no gancho próprio, braço para quem puxa
			end
			ctx.root.AssemblyLinearVelocity = velocity
		end
	end
	if beingPulled and not pulled and airBody and not attached then
		airBody:beginMomentum() -- soltou: segue no embalo até pousar
	end
	beingPulled = pulled
end

local function onPreSimulation(dt: number)
	processPendingFire()
	local ctx = context
	if not ctx then
		return
	end
	stepFlight(ctx, dt)
	applyIncomingPulls(ctx, dt)
	local current = attached
	if current then
		-- A peça sumiu (destruída ou saiu do streaming): solta.
		if not current.anchor.Parent or not current.part:IsDescendantOf(workspace) then
			release(true)
		else
			if current.physics:step(dt, getInput(ctx)) == "Release" then
				release(true) -- chegou, bateu em algo ou soltou o botão: segue no embalo
			end
			return
		end
	end
	local body = airBody
	if body then
		if body:isMomentumOver() then
			endAirBody()
		else
			body:step(dt, getInput(ctx).horizontal)
		end
	end
end

local function onRender()
	local ui = reticle
	if not ui then
		return
	end
	local camera = workspace.CurrentCamera
	local cursor = if aimOverride then nil else UserInputService:GetMouseLocation()
	local ctx = context
	local aimPoint = getAimPoint()
	if not ctx or not aimPoint then
		lastTargetState = "None"
		ui:update(cursor, "None", nil, camera)
		return
	end
	local origin = getOrigin(ctx)
	local target = findTarget(origin, aimPoint)
	lastTargetState = target.state
	-- Sem alvo, o ponto mostra até onde o gancho alcança na direção do cursor.
	local markerPoint = target.point or Aim.clampToRange(origin, aimPoint, settings.Range)
	ui:update(cursor, target.state, markerPoint, camera)
end

local function onReelAction(
	_actionName: string,
	inputState: Enum.UserInputState,
	inputObject: InputObject
): Enum.ContextActionResult
	local isDown = inputState == Enum.UserInputState.Begin
	local keyCode = inputObject.KeyCode
	if keyCode == Enum.KeyCode.W or keyCode == Enum.KeyCode.Up then
		reelInHeld = isDown
	elseif keyCode == Enum.KeyCode.S or keyCode == Enum.KeyCode.Down then
		reelOutHeld = isDown
	end
	-- Pass: o CharacterController (prioridade menor) continua bloqueando o movimento em profundidade.
	return Enum.ContextActionResult.Pass
end

local function cleanupCharacter()
	beingPulled = false
	endFlight()
	release(true)
	endAirBody()
	local ctx = context
	context = nil
	if ctx then
		ctx.trove:Destroy()
	end
end

local function onCharacterAdded(character: Model)
	cleanupCharacter()
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	local root = character:WaitForChild("HumanoidRootPart") :: BasePart
	if player.Character ~= character then
		return -- trocou de personagem enquanto esperava
	end

	local trove = Trove.new()
	local rootAttachment = Instance.new("Attachment")
	rootAttachment.Name = "HookRootAttachment"
	rootAttachment.Parent = root
	trove:Add(rootAttachment)

	context = {
		character = character,
		humanoid = humanoid,
		root = root,
		rootAttachment = rootAttachment,
		trove = trove,
	}
	trove:Connect(humanoid.Died, function()
		endFlight()
		release(true)
		endAirBody()
	end)
	-- Congelou: solta a corda e acaba o embalo (sem A/D no ar); o Humanoid volta a controlar o corpo.
	trove:Connect(character:GetAttributeChangedSignal(Config.Attributes.FrozenUntil), function()
		local ctx = context
		if ctx and ctx.character == character and isFrozen(ctx) then
			firePending = false
			endFlight()
			release(true)
			if not beingPulled then
				endAirBody() -- sendo resgatado por outro jogador, o corpo continua no puxão
			end
		end
	end)
end

local function onRejected(id: number, reason: string)
	lastResult = `Rejected:{reason}`
	local current = attached
	if not current or current.id ~= id then
		return
	end
	-- Recusa por outro motivo não gasta o verde no servidor: desfaz o espelho local.
	if current.hookOnceKey and reason ~= "HookOnceUsed" then
		usedHookOnce[current.hookOnceKey] = nil
	end
	release(false)
end

-- API pequena para testes no Studio (playtest pelo MCP, sem mouse de verdade).
HookController.debug = {
	-- Simula pressionar o botão mirando em `aimPoint` (ponto do plano). Continua "segurado" até
	-- `releaseButton`.
	press = function(aimPoint: Vector3?)
		aimOverride = aimPoint
		pressFire()
	end,
	releaseButton = function()
		releaseFire()
	end,
	setAim = function(aimPoint: Vector3?)
		aimOverride = aimPoint
	end,
	-- horizontal: -1..1 (A/D); reel: -1 recolhe (W), 1 solta (S), só no balanço. nil volta ao teclado.
	setInput = function(horizontal: number?, reel: number?)
		horizontalOverride = horizontal
		reelOverride = reel
	end,
	getState = function(): { [string]: any }
		local ctx = context
		local current = attached
		return {
			attached = current ~= nil,
			hookState = if current then "Attached" elseif flight then flight.state else "Idle",
			hookPosition = if flight then flight.position else nil,
			momentum = current == nil and airBody ~= nil,
			attachId = if current then current.id else nil,
			partName = if current then current.part.Name else nil,
			mode = settings.Mode,
			phase = if current then current.physics:getPhase() else nil,
			buttonHeld = buttonHeld,
			ropeLength = if current then current.physics:getLength() else nil,
			anchor = if current then current.anchor.WorldPosition else nil,
			rootPosition = if ctx then ctx.root.Position else nil,
			velocity = if ctx then ctx.root.AssemblyLinearVelocity else nil,
			humanoidState = if ctx then ctx.humanoid:GetState().Name else nil,
			lastResult = lastResult,
			targetState = lastTargetState,
			firePending = firePending,
		}
	end,
}

-- No Studio, a API de teste também fica acessível de outro contexto (barra de comando/MCP) por um
-- BindableFunction: `HookController.HookDebug:Invoke("press", Vector3.new(...))`.
local function createDebugBindable()
	local bindable = Instance.new("BindableFunction")
	bindable.Name = "HookDebug"
	bindable.OnInvoke = function(command: string, ...: any): any
		local fn = (HookController.debug :: any)[command]
		if typeof(fn) ~= "function" then
			error(`[Hook] comando de teste desconhecido: {command}`)
		end
		return fn(...)
	end
	bindable.Parent = script
end

-- Embalo = corda já solta, mas o AirBody ainda controla o corpo.
function HookController.isInMomentum(): boolean
	return attached == nil and airBody ~= nil
end

function HookController.Start()
	local currentMode = mode
	assert(currentMode, `[Hook] Config.Hook.Mode desconhecido: {settings.Mode}`)

	attachRemote = Net.get("HookAttach")
	detachRemote = Net.get("HookDetach")
	Net.get("HookRejected").OnClientEvent:Connect(onRejected)

	reticle = Reticle.new(player:WaitForChild("PlayerGui"))

	-- Volta instantânea pela zona de morte: solta tudo e para o corpo, como ao renascer.
	player:GetAttributeChangedSignal(Config.Attributes.Respawns):Connect(function()
		firePending = false
		endFlight()
		release(false)
		endAirBody()
		local ctx = context
		if ctx then
			ctx.root.AssemblyLinearVelocity = Vector3.zero
		end
	end)

	-- O servidor muda este atributo quando o uso dos verdes zera (renascer ou checkpoint).
	player:GetAttributeChangedSignal(Config.Attributes.HookOnceEpoch):Connect(function()
		table.clear(usedHookOnce)
	end)

	player.CharacterRemoving:Connect(cleanupCharacter)
	player.CharacterAdded:Connect(onCharacterAdded)
	if player.Character then
		task.spawn(onCharacterAdded, player.Character)
	end

	UserInputService.InputBegan:Connect(function(input: InputObject, gameProcessed: boolean)
		if input.UserInputType == Enum.UserInputType.MouseButton1 and not gameProcessed then
			pressFire()
		end
	end)
	UserInputService.InputEnded:Connect(function(input: InputObject)
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			releaseFire()
		end
	end)
	-- W/S só mexem no gancho no balanço; no puxão ficam só com o CharacterController (bloqueadas).
	if currentMode.usesReel then
		ContextActionService:BindActionAtPriority(
			"HookReel",
			onReelAction,
			false,
			CharacterController.DepthKeysPriority + 1,
			table.unpack(CharacterController.DepthKeys)
		)
	end

	RunService.PreSimulation:Connect(onPreSimulation)
	RunService:BindToRenderStep("HookReticle", Enum.RenderPriority.Camera.Value + 2, onRender)

	if RunService:IsStudio() then
		createDebugBindable()
	end
end

return HookController
