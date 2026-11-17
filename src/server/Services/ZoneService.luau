--!strict
--[[
	Zonas do mapa: morte e gelo (RF-20, RF-22, RF-24, RF-25; ADR 0014, 0045).

	A cada `Config.Zones.CheckInterval`, para cada personagem vivo:
	- toca peça `KillZone` → morre na hora;
	- toca `UnfreezeZone` congelado → descongela (apaga `FrozenUntil`);
	- congelado e o tempo acabou → morre;
	- toca `FreezeZone` e não está congelado → `FrozenUntil = agora + Config.Freeze.Duration`.
	A decisão fica em `Shared.Logic.Zones.pickEffect` (pura).

	O estado é o atributo `Config.Attributes.FrozenUntil` no PERSONAGEM, em tempo do servidor
	(`workspace:GetServerTimeNow()`). Personagem novo nasce sem ele; quem recoloca no checkpoint é o
	CheckpointService/LobbyService. O cliente (FreezeController) lê o atributo e trava os controles.

	Conferência por `GetPartBoundsInBox` com `OverlapParams` incluindo só as peças com tag de zona
	(e não por Touched, que falha com peças sem colisão e personagens movidos por física/teleporte).
	Escolhido no lugar de `Zones.isInside` no centro do root porque: o gelo e o descongelar são peças
	SÓLIDAS (o jogador encosta, nunca fica "dentro"), e matar no toque (RF-25) pede o corpo todo, não
	um ponto; a consulta do motor é espacial (não percorre todas as zonas do mapa por jogador) e
	trata peças giradas. A caixa do corpo vem de `Config.Zones` com a folga `TouchMargin`.
	Requisito: a peça de zona precisa de `CanQuery = true` (avisamos no Output se não tiver).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)

local FROZEN_UNTIL = Config.Attributes.FrozenUntil
local ZONE_TAGS = { Config.Tags.KillZone, Config.Tags.FreezeZone, Config.Tags.UnfreezeZone }

local settings = Config.Zones
local margin = settings.TouchMargin
local boxSize = settings.CharacterBoxSize + Vector3.new(margin, margin, margin) * 2
local boxOffset = CFrame.new(0, settings.CharacterBoxOffsetY, 0)

local ZoneService = {}

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

local function kill(player: Player, humanoid: Humanoid, reason: string)
	humanoid.Health = 0
	print(`[Zones] {player.Name} morreu ({reason})`)
end

local function checkCharacter(player: Player, character: Model, now: number)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local root = character:FindFirstChild("HumanoidRootPart")
	if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return
	end

	local inKill, inFreeze, inUnfreeze = false, false, false
	for _, part in workspace:GetPartBoundsInBox(root.CFrame * boxOffset, boxSize, overlapParams) do
		if part:HasTag(Config.Tags.KillZone) then
			inKill = true
		elseif part:HasTag(Config.Tags.UnfreezeZone) then
			inUnfreeze = true
		elseif part:HasTag(Config.Tags.FreezeZone) then
			inFreeze = true
		end
	end

	local effect = Zones.pickEffect(inKill, inUnfreeze, inFreeze, character:GetAttribute(FROZEN_UNTIL), now)
	if effect == "Kill" then
		kill(player, humanoid, "KillZone")
	elseif effect == "Expire" then
		kill(player, humanoid, "gelo")
	elseif effect == "Unfreeze" then
		character:SetAttribute(FROZEN_UNTIL, nil)
		print(`[Zones] {player.Name} descongelou`)
	elseif effect == "Freeze" then
		character:SetAttribute(FROZEN_UNTIL, now + Config.Freeze.Duration)
		print(`[Zones] {player.Name} congelou por {Config.Freeze.Duration} s`)
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
