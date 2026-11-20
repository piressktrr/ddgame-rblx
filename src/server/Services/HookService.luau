--!strict
--[[
	Validação do gancho no servidor (RF-12, RF-13, RNF-02, RNF-03; ADR 0016, 0039).

	O cliente simula o gancho (é dono da física do próprio personagem) e avisa "prendi" / "soltei".
	O servidor não confia: confere tipos, alcance (com folga para o atraso da rede), se o ponto está na
	peça e no plano, a tag da peça e o intervalo entre um prender e outro. Se recusar, manda
	`HookRejected` e o cliente solta.

	Guarda o uso do verde (`HookOnce`) por jogador e zera ao renascer ou ao passar checkpoint (o atributo
	`Checkpoint` do Player muda, ver CheckpointService). O cliente espelha esse uso e limpa o espelho
	quando o atributo `HookOnceEpoch` do Player muda.

	Repassa a corda de cada jogador aos outros clientes (`HookRope`, RF-16): quem já está no servidor
	recebe ao prender/soltar; quem entra recebe as cordas que já estão presas.

	Gancho em outro jogador (DDNet): o cliente manda a peça = HumanoidRootPart do alvo. O servidor
	confere (alvo vivo, nenhum dos dois em solo, alcance) e marca `Config.Attributes.HookTarget` no
	personagem de quem puxou; o cliente do alvo lê a marca e aplica o puxão no próprio corpo. Solta
	sozinho depois de `PlayerHookDuration` (+ folga) ou se o alvo ficar inválido, avisando o cliente
	com `HookRejected(id, "PlayerReleased")`.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local HookSurface = require(ReplicatedStorage.Shared.Util.HookSurface)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local Net = require(ReplicatedStorage.Shared.Net)
local Trove = require(ReplicatedStorage.Packages.Trove)

type PlayerState = {
	trove: Trove.Trove,
	usedHookOnce: { [Instance]: boolean },
	lastAttachAt: number,
	attachedId: number?,
	attachedPart: BasePart?,
	attachedPoint: Vector3?,
	targetPlayer: Player?, -- gancho preso em outro jogador
	windowStart: number,
	windowCount: number,
}

local settings = Config.Hook
local EPOCH_ATTRIBUTE = Config.Attributes.HookOnceEpoch

local HookService = {}

local states: { [Player]: PlayerState } = {}
local rejectedRemote: RemoteEvent? = nil
local ropeRemote: RemoteEvent? = nil

-- Avisa todos os outros clientes da corda deste jogador (part nil = soltou).
local function broadcastRope(owner: Player, part: BasePart?, point: Vector3?)
	local remote = ropeRemote
	if not remote then
		return
	end
	local localPoint = if part and point then part.CFrame:PointToObjectSpace(point) else nil
	for _, other in Players:GetPlayers() do
		if other ~= owner then
			remote:FireClient(other, owner, part, localPoint)
		end
	end
end

local function clearAttached(player: Player, state: PlayerState)
	local wasAttached = state.attachedId ~= nil
	state.attachedId = nil
	state.attachedPart = nil
	state.attachedPoint = nil
	if state.targetPlayer then
		state.targetPlayer = nil
		local character = player.Character
		if character then
			character:SetAttribute(Config.Attributes.HookTarget, nil)
		end
	end
	if wasAttached then
		broadcastRope(player, nil, nil)
	end
end

local function resetHookOnce(player: Player, state: PlayerState)
	table.clear(state.usedHookOnce)
	local epoch = player:GetAttribute(EPOCH_ATTRIBUTE)
	player:SetAttribute(EPOCH_ATTRIBUTE, (if typeof(epoch) == "number" then epoch else 0) + 1)
end

-- Limite simples de mensagens por segundo, por jogador (RNF-03).
local function allowMessage(state: PlayerState): boolean
	local now = os.clock()
	if now - state.windowStart >= 1 then
		state.windowStart = now
		state.windowCount = 0
	end
	state.windowCount += 1
	return state.windowCount <= settings.ServerMaxMessagesPerSecond
end

local function playerFromPart(part: Instance): Player?
	local model = part:FindFirstAncestorOfClass("Model")
	while model do
		local owner = Players:GetPlayerFromCharacter(model)
		if owner then
			return owner
		end
		model = model:FindFirstAncestorOfClass("Model")
	end
	return nil
end

local function isSolo(character: Model?): boolean
	return character ~= nil and character:GetAttribute(Config.Attributes.Solo) == true
end

-- Root do alvo se ele ainda pode ser puxado (vivo, fora do solo), ou nil.
local function targetRoot(target: Player): BasePart?
	local character = target.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not target.Parent or not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return nil
	end
	if isSolo(character) then
		return nil
	end
	return root
end

-- Converte os argumentos que vieram da rede. nil se algum tipo estiver errado.
local function parseAttach(part: unknown, point: unknown): (BasePart?, Vector3?)
	if typeof(part) ~= "Instance" or typeof(point) ~= "Vector3" then
		return nil, nil
	end
	local instance = part :: Instance
	local position = point :: Vector3
	if not instance:IsA("BasePart") or not HookRules.isFiniteVector(position) then
		return nil, nil
	end
	return instance :: BasePart, position
end

-- Confere o "prendi" do cliente. Devolve o motivo da recusa, ou nil se valeu.
local function validateAttach(
	player: Player,
	state: PlayerState,
	part: BasePart,
	point: Vector3,
	now: number
): string?
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return "NoCharacter"
	end
	-- Congelado (ZoneService, RF-20) não usa o gancho.
	if character and Zones.isFrozen(character:GetAttribute(Config.Attributes.FrozenUntil)) then
		return "Frozen"
	end
	if not part:IsDescendantOf(workspace) then
		return "InvalidPart"
	end
	if
		not HookRules.cooldownReady(state.lastAttachAt, now, settings.Cooldown - settings.ServerCooldownSlack)
	then
		return "Cooldown"
	end
	local target = playerFromPart(part)
	if target then
		-- Gancho em jogador: alvo válido, nenhum dos dois em solo, dentro do alcance.
		if target == player then
			return "Self"
		end
		local other = targetRoot(target)
		if not other or isSolo(character) then
			return "PlayerUnavailable"
		end
		local maxDistance = settings.Range + settings.ServerRangeTolerance
		if not HookRules.isWithinRange(root.Position, other.Position, maxDistance) then
			return "OutOfRange"
		end
		return nil
	end
	local maxDistance = settings.Range + settings.AimAssistRadius + settings.ServerRangeTolerance
	if not HookRules.isWithinRange(root.Position, point, maxDistance) then
		return "OutOfRange"
	end
	if math.abs(point.Z - Config.Plane.Z) > settings.ServerSurfaceTolerance then
		return "OffPlane"
	end
	if
		not part:IsA("Terrain")
		and not HookRules.pointOnPart(part.CFrame, part.Size, point, settings.ServerSurfaceTolerance)
	then
		return "NotOnPart"
	end
	local kind = HookSurface.getKind(part)
	if kind == "NoHook" then
		return "NoHook"
	end
	local key = HookSurface.getHookOnceKey(part)
	if not HookRules.canAttach(kind, key ~= nil and state.usedHookOnce[key] == true) then
		return "HookOnceUsed"
	end
	return nil
end

local function onAttach(player: Player, id: unknown, part: unknown, point: unknown)
	local state = states[player]
	if not state or not allowMessage(state) then
		return
	end
	if typeof(id) ~= "number" or not HookRules.isFiniteNumber(id :: number) then
		return -- sem um id válido não há como responder ao cliente
	end
	local attachId = id :: number

	local now = os.clock()
	local basePart, position = parseAttach(part, point)
	local reason = if basePart and position
		then validateAttach(player, state, basePart, position, now)
		else "BadArguments"
	if reason or not basePart or not position then
		if rejectedRemote then
			rejectedRemote:FireClient(player, attachId, reason or "BadArguments")
		end
		return
	end

	clearAttached(player, state) -- troca de alvo: a marca anterior sai
	state.lastAttachAt = now
	local target = playerFromPart(basePart)
	local key = if target then nil else HookSurface.getHookOnceKey(basePart)
	if key then
		state.usedHookOnce[key] = true
	end
	state.attachedId = attachId
	state.attachedPart = basePart
	state.attachedPoint = position
	if target then
		state.targetPlayer = target
		local character = player.Character
		if character then
			character:SetAttribute(Config.Attributes.HookTarget, target.UserId)
		end
	end
	broadcastRope(player, basePart, position)
end

local function onDetach(player: Player, id: unknown)
	local state = states[player]
	if not state or not allowMessage(state) then
		return
	end
	if typeof(id) == "number" and state.attachedId == id then
		clearAttached(player, state)
	end
end

local function onPlayerAdded(player: Player)
	local trove = Trove.new()
	local state: PlayerState = {
		trove = trove,
		usedHookOnce = {},
		lastAttachAt = -math.huge,
		attachedId = nil,
		attachedPart = nil,
		attachedPoint = nil,
		targetPlayer = nil,
		windowStart = 0,
		windowCount = 0,
	}
	states[player] = state
	player:SetAttribute(EPOCH_ATTRIBUTE, 0)

	-- Quem entra vê as cordas que já estão presas.
	local remote = ropeRemote
	if remote then
		for other, otherState in states do
			local part, point = otherState.attachedPart, otherState.attachedPoint
			if other ~= player and part and point then
				remote:FireClient(player, other, part, part.CFrame:PointToObjectSpace(point))
			end
		end
	end

	-- Renascer (morte ou reset) e passar checkpoint devolvem o uso dos verdes (RF-13).
	trove:Connect(player.CharacterAdded, function()
		clearAttached(player, state)
		resetHookOnce(player, state)
	end)
	-- Volta instantânea pela zona de morte (LobbyService.respawnInPlace): mesmo efeito de renascer.
	trove:Connect(player:GetAttributeChangedSignal(Config.Attributes.Respawns), function()
		clearAttached(player, state)
		resetHookOnce(player, state)
	end)
	trove:Connect(player:GetAttributeChangedSignal(Config.Attributes.Checkpoint), function()
		resetHookOnce(player, state)
	end)
end

local function onPlayerRemoving(player: Player)
	local state = states[player]
	if state then
		clearAttached(player, state)
		state.trove:Destroy()
		states[player] = nil
	end
end

function HookService.Start()
	rejectedRemote = Net.get("HookRejected")
	ropeRemote = Net.get("HookRope")
	Net.get("HookAttach").OnServerEvent:Connect(onAttach)
	Net.get("HookDetach").OnServerEvent:Connect(onDetach)

	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)

	-- Gancho em jogador: solta sozinho no tempo do DDNet (+ folga) ou se o alvo deixar de valer.
	local maxHold = settings.PlayerHookDuration + settings.PlayerHookServerSlack
	local maxDistance = settings.Range * 1.5 + settings.ServerRangeTolerance
	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for player, state in states do
			local target = state.targetPlayer
			if not target then
				continue
			end
			local other = targetRoot(target)
			local character = player.Character
			local root = character and character:FindFirstChild("HumanoidRootPart")
			local tooFar = other ~= nil
				and root ~= nil
				and root:IsA("BasePart")
				and (other.Position - root.Position).Magnitude > maxDistance
			if now - state.lastAttachAt > maxHold or not other or isSolo(character) or tooFar then
				local id = state.attachedId
				clearAttached(player, state)
				if rejectedRemote and id then
					rejectedRemote:FireClient(player, id, "PlayerReleased")
				end
			end
		end
	end)
end

return HookService
