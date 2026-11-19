--!strict
--[[
	Lobby antes do mapa (ADR 0044).

	- Todo jogador nasce no lobby (peça com a tag `LobbySpawn`, um SpawnLocation).
	- Entrar no portal (`LobbyPortal`) começa uma corrida nova (`RaceService.beginRace`: zera o
	  checkpoint, marca `InRace`, grava `RaceStartedAt`) e leva o personagem ao `RaceStart`.
	- Morrer em corrida: renasce no último checkpoint (CheckpointService) ou, sem checkpoint, no
	  `RaceStart` (aqui). Fora de corrida: renasce no lobby.

	O portal é conferido por zona (como os checkpoints), não por Touched: o Touched falha com peças
	sem colisão e personagens movidos por física/teleporte.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local CheckpointService = require(script.Parent.CheckpointService)
local RaceService = require(script.Parent.RaceService)

local IN_RACE = Config.Attributes.InRace
local CHECKPOINT = Config.Attributes.Checkpoint

local LobbyService = {}

local function firstTagged(tag: string): BasePart?
	for _, instance in CollectionService:GetTagged(tag) do
		if instance:IsA("BasePart") then
			return instance
		end
	end
	return nil
end

local function isInRace(player: Player): boolean
	return player:GetAttribute(IN_RACE) == true
end

local function hasCheckpoint(player: Player): boolean
	local value = player:GetAttribute(CHECKPOINT)
	return typeof(value) == "number" and value > 0
end

-- Põe o personagem em cima da peça, olhando para o lado +X dela (como o CheckpointService).
local function placeOn(character: Model, part: BasePart)
	local position = part.Position + Vector3.new(0, part.Size.Y / 2 + Config.Checkpoint.SpawnHeight, 0)
	character:PivotTo(CFrame.lookAlong(position, part.CFrame.RightVector))
	local root = character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		root.AssemblyLinearVelocity = Vector3.zero
	end
end

-- No Studio, o `EditorSpawn` ligado (`Enabled`) vale para testar a área do MapBuilder.
local function editorSpawn(): BasePart?
	if not RunService:IsStudio() then
		return nil
	end
	local part = firstTagged(Config.Tags.EditorSpawn)
	return if part and part:GetAttribute("Enabled") == true then part else nil
end

-- Volta instantânea (zona de morte, como no DDNet): leva o personagem vivo ao ponto de renascer sem
-- recarregá-lo. Ordem: EditorSpawn (Studio) > último checkpoint > RaceStart (em corrida) > lobby.
-- Muda `Respawns` no Player para cliente e HookService soltarem o gancho e devolverem os verdes.
function LobbyService.respawnInPlace(player: Player)
	local character = player.Character
	if not character then
		return
	end
	local target = editorSpawn()
		or CheckpointService.getCheckpointPart(player)
		or (if isInRace(player) then firstTagged(Config.Tags.RaceStart) else nil)
		or firstTagged(Config.Tags.LobbySpawn)
	if not target then
		return
	end
	character:SetAttribute(Config.Attributes.FrozenUntil, nil)
	placeOn(character, target)
	local count = player:GetAttribute(Config.Attributes.Respawns)
	player:SetAttribute(Config.Attributes.Respawns, (if typeof(count) == "number" then count else 0) + 1)
end

local function onCharacterAdded(player: Player, character: Model)
	-- O Roblox posiciona o personagem no spawn depois do CharacterAdded; esperamos isso acabar.
	if not character:IsDescendantOf(workspace) then
		character.AncestryChanged:Wait()
	end
	character:WaitForChild("HumanoidRootPart", 5)
	task.wait()
	if player.Character ~= character then
		return
	end

	local target: BasePart? = editorSpawn()
	if target then
		placeOn(character, target)
		return
	end
	if not isInRace(player) then
		target = firstTagged(Config.Tags.LobbySpawn)
	elseif not hasCheckpoint(player) then
		target = firstTagged(Config.Tags.RaceStart)
	end
	-- Em corrida com checkpoint: quem recoloca é o CheckpointService.
	if target then
		placeOn(character, target)
	end
end

local function onPlayerAdded(player: Player)
	player:SetAttribute(IN_RACE, false)
	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
	if player.Character then
		task.spawn(onCharacterAdded, player, player.Character)
	end
end

local function startRace(player: Player, character: Model)
	local start = firstTagged(Config.Tags.RaceStart)
	if not start then
		warn("[Lobby] Nenhuma peça com a tag RaceStart; o portal não leva a lugar nenhum")
		return
	end
	placeOn(character, start)
	RaceService.beginRace(player)
	print(`[Lobby] {player.Name} entrou no portal e começou a corrida`)
end

local function checkPortals()
	local portals = CollectionService:GetTagged(Config.Tags.LobbyPortal)
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if not character or not root or not root:IsA("BasePart") or isInRace(player) then
			continue
		end
		for _, portal in portals do
			if
				portal:IsA("BasePart")
				and Zones.isInside(portal.CFrame, portal.Size, Config.Lobby.PortalMargin, root.Position)
			then
				startRace(player, character)
				break
			end
		end
	end
end

function LobbyService.Start()
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)

	local elapsed = 0
	RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		if elapsed < Config.Lobby.CheckInterval then
			return
		end
		elapsed = 0
		checkPortals()
	end)
end

return LobbyService
