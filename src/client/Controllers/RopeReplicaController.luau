--!strict
--[[
	Corda dos outros jogadores (RF-16). O servidor manda `HookRope` (jogador, peça, ponto no espaço da
	peça) quando alguém prende e (jogador, nil) quando solta. Aqui só desenhamos: um `Beam` do root do
	outro personagem até um `Attachment` local na peça, com o mesmo visual da corda própria
	(corrente com garra, `HookController.HookChain`). A própria corda é desenhada pelo HookController.

	Se a peça ou o personagem somem, a corda some junto (o Trove limpa).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = require(ReplicatedStorage.Shared.Net)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookChain = require(script.Parent.HookController.HookChain)

local localPlayer = Players.LocalPlayer

local RopeReplicaController = {}

local ropes: { [Player]: Trove.Trove } = {}

local function clearRope(owner: Player)
	local trove = ropes[owner]
	if trove then
		ropes[owner] = nil
		trove:Destroy()
	end
end

local function findRootAttachment(owner: Player): Attachment?
	local character = owner.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root then
		return nil
	end
	local attachment = root:FindFirstChild("RootAttachment")
	if attachment and attachment:IsA("Attachment") then
		return attachment
	end
	return nil
end

local function showRope(owner: Player, part: BasePart, localPoint: Vector3)
	clearRope(owner)
	local rootAttachment = findRootAttachment(owner)
	if not rootAttachment or not part:IsDescendantOf(workspace) then
		return
	end
	local trove = Trove.new()
	ropes[owner] = trove

	local anchor = Instance.new("Attachment")
	anchor.Name = "HookRopeReplicaAnchor"
	anchor.Position = localPoint
	anchor.Parent = part
	trove:Add(anchor)

	trove:Add(HookChain.new(rootAttachment, anchor)) -- mesma corrente com garra do gancho próprio

	trove:Connect(part.AncestryChanged, function()
		if not part:IsDescendantOf(workspace) then
			clearRope(owner)
		end
	end)
	trove:Connect(rootAttachment.AncestryChanged, function()
		if not rootAttachment:IsDescendantOf(workspace) then
			clearRope(owner)
		end
	end)
end

local function onRope(owner: unknown, part: unknown, localPoint: unknown)
	if typeof(owner) ~= "Instance" or not (owner :: Instance):IsA("Player") or owner == localPlayer then
		return
	end
	local player = owner :: Player
	if
		typeof(part) == "Instance"
		and (part :: Instance):IsA("BasePart")
		and typeof(localPoint) == "Vector3"
	then
		showRope(player, part :: BasePart, localPoint :: Vector3)
	else
		clearRope(player)
	end
end

function RopeReplicaController.Start()
	Net.get("HookRope").OnClientEvent:Connect(onRope)
	Players.PlayerRemoving:Connect(clearRope)
end

return RopeReplicaController
