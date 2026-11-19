--!strict
--[[
	Zonas do mapa: morte e gelo (RF-20, RF-22, RF-24, RF-25; ADR 0014, 0045).

	A cada `Config.Zones.CheckInterval`, para cada personagem vivo (regras do DDNet):
	- toca peça `KillZone` → volta na hora ao checkpoint (`LobbyService.respawnInPlace`, sem morrer);
	- toca `UnfreezeZone` congelado → descongela (apaga `FrozenUntil`);
	- dentro do `FreezeZone` → congela e renova `FrozenUntil = agora + Config.Freeze.ReleaseDelay`;
	- fora do gelo e o tempo passou → descongela;
	- entra na `StartLine` → começa/recomeça a run (`RaceService.beginRace`);
	- entra na `FinishLine` com a run valendo → salva o tempo (`RaceService.finishRun`).
	A decisão fica em `Shared.Logic.Zones.pickEffect` (pura).

	O estado é o atributo `Config.Attributes.FrozenUntil` no PERSONAGEM, em tempo do servidor
	(`workspace:GetServerTimeNow()`). Personagem novo nasce sem ele; quem recoloca no checkpoint é o
	CheckpointService/LobbyService. O cliente (FreezeController) lê o atributo e trava os controles.

	Conferência por `GetPartBoundsInBox` com `OverlapParams` incluindo só as peças com tag de zona
	(e não por Touched, que falha com peças sem colisão e personagens movidos por física/teleporte).
	Escolhido no lugar de `Zones.isInside` no centro do root porque: as zonas podem ser sólidas (mapas
	antigos: o jogador encosta) ou atravessáveis (MapBuilder), e o toque pede o corpo todo, não um ponto; a consulta do motor é espacial (não percorre todas as zonas do mapa por jogador) e
	trata peças giradas. A caixa do corpo vem de `Config.Zones` com a folga `TouchMargin`.
	Requisito: a peça de zona precisa de `CanQuery = true` (avisamos no Output se não tiver).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local LobbyService = require(script.Parent.LobbyService)
local RaceService = require(script.Parent.RaceService)

local FROZEN_UNTIL = Config.Attributes.FrozenUntil
local ZONE_TAGS = {
	Config.Tags.KillZone,
	Config.Tags.FreezeZone,
	Config.Tags.UnfreezeZone,
	Config.Tags.StartLine,
	Config.Tags.FinishLine,
}

local settings = Config.Zones
local margin = settings.TouchMargin
local boxSize = settings.CharacterBoxSize + Vector3.new(margin, margin, margin) * 2
local boxOffset = CFrame.new(0, settings.CharacterBoxOffsetY, 0)

local ZoneService = {}

local lastPosition: { [Model]: Vector3 } = setmetatable({}, { __mode = "k" }) :: any
-- Linhas que o personagem tocava na conferência anterior: a linha age só ao ENTRAR nela.
local touchingStart: { [Model]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local touchingFinish: { [Model]: boolean } = setmetatable({}, { __mode = "k" }) :: any

local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include
local filterDirty = true

local function refreshFilter()
	local parts: { Instance } = {}
	for _, tag in ZONE_TAGS do
		for _, instance in CollectionService:GetTagged(tag) do
			if instance:IsA("BasePart") then
				table.insert(parts, instance)
			end
		end
	end
	overlapParams.FilterDescendantsInstances = parts
	filterDirty = false
end

local function onZoneTagged(instance: Instance)
	filterDirty = true
	if instance:IsA("BasePart") and not instance.CanQuery then
		warn(`[Zones] {instance:GetFullName()} tem tag de zona mas CanQuery = false; a zona não funciona`)
	end
end

local function checkCharacter(player: Player, character: Model, now: number)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local root = character:FindFirstChild("HumanoidRootPart")
	if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return
	end

	-- Caixa varrida: cobre o caminho desde a última conferência (zona fina atravessada rápido conta).
	local current = (root.CFrame * boxOffset).Position
	local previous = lastPosition[character] or current
	lastPosition[character] = current
	local delta = current - previous
	local sweptSize = boxSize + Vector3.new(math.abs(delta.X), math.abs(delta.Y), math.abs(delta.Z))
	if delta.Magnitude > settings.MaxSweep then
		sweptSize = boxSize -- teleporte (checkpoint, lobby): não varre o caminho
		previous = current
	end
	local inKill, inFreeze, inUnfreeze, inStart, inFinish = false, false, false, false, false
	for _, part in
		workspace:GetPartBoundsInBox(CFrame.new((current + previous) / 2), sweptSize, overlapParams)
	do
		if part:HasTag(Config.Tags.KillZone) then
			inKill = true
		elseif part:HasTag(Config.Tags.UnfreezeZone) then
			inUnfreeze = true
		elseif part:HasTag(Config.Tags.FreezeZone) then
			inFreeze = true
		elseif part:HasTag(Config.Tags.FinishLine) then
			inFinish = true
		elseif part:HasTag(Config.Tags.StartLine) then
			inStart = true
		end
	end

	-- Linhas da run: agem ao entrar. Chegada salva o tempo; largada começa/recomeça a run.
	if inFinish and not touchingFinish[character] then
		RaceService.finishRun(player)
	end
	if inStart and not touchingStart[character] then
		RaceService.beginRace(player)
	end
	touchingFinish[character] = inFinish
	touchingStart[character] = inStart

	local frozenUntil = character:GetAttribute(FROZEN_UNTIL)
	local effect = Zones.pickEffect(inKill, inUnfreeze, inFreeze, frozenUntil, now)
	if effect == "Kill" then
		LobbyService.respawnInPlace(player)
	elseif effect == "Unfreeze" or effect == "Thaw" then
		character:SetAttribute(FROZEN_UNTIL, nil)
	elseif effect == "Freeze" then
		-- Renova só quando precisa (evita replicar o atributo a cada conferência).
		local releaseDelay = Config.Freeze.ReleaseDelay
		if typeof(frozenUntil) ~= "number" or frozenUntil - now < releaseDelay / 2 then
			character:SetAttribute(FROZEN_UNTIL, now + releaseDelay)
		end
	end
end

local function step()
	if filterDirty then
		refreshFilter()
	end
	local now = workspace:GetServerTimeNow()
	for _, player in Players:GetPlayers() do
		local character = player.Character
		if character then
			checkCharacter(player, character, now)
		end
	end
end

function ZoneService.Start()
	for _, tag in ZONE_TAGS do
		for _, instance in CollectionService:GetTagged(tag) do
			onZoneTagged(instance)
		end
		CollectionService:GetInstanceAddedSignal(tag):Connect(onZoneTagged)
		CollectionService:GetInstanceRemovedSignal(tag):Connect(function()
			filterDirty = true
		end)
	end

	local elapsed = 0
	RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		if elapsed < settings.CheckInterval then
			return
		end
		elapsed = 0
		step()
	end)
end

return ZoneService
