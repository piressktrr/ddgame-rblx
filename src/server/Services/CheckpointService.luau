--!strict
--[[
	Checkpoints pessoais e em ordem (RF-26, ADR 0018). Versão mínima, para o mapa em estágios
	ser jogável: guarda o último checkpoint de cada jogador e o recoloca lá quando renasce.

	No mapa, um checkpoint é uma peça com a tag `Checkpoint` e o atributo numérico `Order`
	(1, 2, 3...). Só conta o próximo da sequência: pular um checkpoint não vale.
	O jogador renasce em cima da peça, olhando para o lado +X dela (RightVector).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)

local ORDER_ATTRIBUTE = "Order" -- na peça do mapa
local PLAYER_ATTRIBUTE = "Checkpoint" -- no Player: número do último checkpoint alcançado

local CheckpointService = {}

local checkpoints: { [number]: BasePart } = {}

local function register(instance: Instance)
	if not instance:IsA("BasePart") then
		return
	end
	local order = instance:GetAttribute(ORDER_ATTRIBUTE)
	if typeof(order) ~= "number" then
		warn(`[Checkpoint] {instance:GetFullName()} tem a tag mas não tem o atributo numérico "Order"`)
		return
	end
	checkpoints[order] = instance
end

local function unregister(instance: Instance)
	for order, part in checkpoints do
		if part == instance then
			checkpoints[order] = nil
		end
	end
end

local function getReached(player: Player): number
	local value = player:GetAttribute(PLAYER_ATTRIBUTE)
	return if typeof(value) == "number" then value else 0
end

local function placeAtCheckpoint(player: Player, character: Model)
	local part = checkpoints[getReached(player)]
	if not part then
		return -- ainda sem checkpoint: nasce no spawn normal do mapa
	end
	-- O Roblox posiciona o personagem no spawn depois do CharacterAdded; esperamos isso acabar.
	if not character:IsDescendantOf(workspace) then
		character.AncestryChanged:Wait()
	end
	character:WaitForChild("HumanoidRootPart", 5)
	task.wait()
	local position = part.Position + Vector3.new(0, part.Size.Y / 2 + Config.Checkpoint.SpawnHeight, 0)
	character:PivotTo(CFrame.lookAlong(position, part.CFrame.RightVector))
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		placeAtCheckpoint(player, character)
	end)
end

local function step()
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if not root or not root:IsA("BasePart") then
			continue
		end
		local reached = getReached(player)
		local nextPart = checkpoints[reached + 1]
		if
			nextPart
			and Zones.isAbove(nextPart.CFrame, nextPart.Size, Config.Checkpoint.ZoneHeight, root.Position)
		then
			player:SetAttribute(PLAYER_ATTRIBUTE, reached + 1)
			print(`[Checkpoint] {player.Name} alcançou o checkpoint {reached + 1}`)
		end
	end
end

function CheckpointService.Start()
	Players.RespawnTime = Config.Race.RespawnTime

	local tag = Config.Tags.Checkpoint
	for _, instance in CollectionService:GetTagged(tag) do
		register(instance)
	end
	CollectionService:GetInstanceAddedSignal(tag):Connect(register)
	CollectionService:GetInstanceRemovedSignal(tag):Connect(unregister)

	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)

	RunService.Heartbeat:Connect(step)
end

return CheckpointService
