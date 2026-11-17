--!strict
--[[
	Gancho do jogador local, Fase 1: só em superfícies (RF-10..14, RF-17..19; ADR 0016, 0036, 0039, 0042).

	- Botão esquerdo do mouse, modo "Pull" (padrão, ADR 0042): um clique prende e puxa o personagem
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
local HookPhysics = require(script.HookPhysics)
local PullPhysics = require(script.PullPhysics)
local Reticle = require(script.Reticle)
local SwingPhysics = require(script.SwingPhysics)

type Target = {
	state: HookRules.TargetState,
	part: BasePart?,
	point: Vector3?, -- ponto no plano onde o gancho prenderia
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

-- Um módulo de física por tipo de gancho (ADR 0036, 0042).
local MODES: { [string]: HookPhysics.Mode } = {
	Pull = PullPhysics.mode,
	Swing = SwingPhysics.mode,
}

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

-- Ignora todos os personagens: gancho em jogador fica para a Fase 4.
local function refreshFilter()
	local exclude: { Instance } = {}
	for _, other in Players:GetPlayers() do
		local character = other.Character
		if character then
			table.insert(exclude, character)
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

local function findTarget(origin: Vector3, aimPoint: Vector3): Target
	local castVector = Aim.castVector(origin, aimPoint, settings.Range)
	if not castVector then
		return NO_TARGET
	end
	refreshFilter()

	local rayTarget = evaluateHit(workspace:Raycast(origin, castVector, raycastParams))
	if rayTarget.state == "Valid" then
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

local function attach(ctx: CharacterContext, part: BasePart, point: Vector3)
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

	local physics = currentMode.new({
		character = ctx.character,
		root = ctx.root,
		rootAttachment = ctx.rootAttachment,
		anchor = anchor,
		body = body,
	})
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
	local aimPoint = getAimPoint()
	if not aimPoint then
		lastResult = "NoAim"
		return
	end
	local target = findTarget(getOrigin(ctx), aimPoint)
	if target.state == "Valid" and target.part and target.point then
		-- Troca de alvo durante o voo: solta o atual (o corpo continua o mesmo) e prende no novo.
		-- Alvo inválido não interrompe o puxão em andamento.
		release(true)
		attach(ctx, target.part, target.point)
		lastResult = "Attached"
	elseif target.state == "Forbidden" then
		lastResult = "Forbidden"
		if reticle then
			reticle:flashForbidden()
		end
	else
		lastResult = "NoTarget"
	end
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

local function onPreSimulation(dt: number)
	processPendingFire()
	local ctx = context
	if not ctx then
		return
	end
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
		release(true)
		endAirBody()
	end)
	-- Congelou: solta a corda e acaba o embalo (sem A/D no ar); o Humanoid volta a controlar o corpo.
	trove:Connect(character:GetAttributeChangedSignal(Config.Attributes.FrozenUntil), function()
		local ctx = context
		if ctx and ctx.character == character and isFrozen(ctx) then
			firePending = false
			release(true)
			endAirBody()
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
