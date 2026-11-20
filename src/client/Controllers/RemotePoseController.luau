--!strict
--[[
	Pose de voo nos OUTROS jogadores (só visual, local). Os `Transform` da `HookPose` não replicam: sem
	isto, quem é puxado, martelado ou está no gancho aparece para os outros só com a animação de queda
	(duro). Aqui cada cliente aplica a mesma pose procedural nos personagens dos outros quando eles estão
	no ar e:
	  - com a corda presa (braço aponta para o ponto preso, `RopeReplicaController.getAnchor`), ou
	  - rápidos demais para um pulo normal (puxados, martelados ou no embalo do gancho).
	Sai da pose depois de um tempo no chão.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local HookPose = require(script.Parent.HookController.HookPose)
local RopeReplicaController = require(script.Parent.RopeReplicaController)

local FAST_SPEED = 45 -- studs/s: acima disso no ar não é um pulo normal
local GROUND_MARGIN = 0.6 -- studs abaixo dos pés que ainda contam como chão
local GROUND_EXIT_TIME = 0.12 -- s no chão antes de sair da pose

type Tracked = {
	pose: HookPose.HookPose?,
	groundedSince: number?,
	target: Attachment?,
}

local player = Players.LocalPlayer

local RemotePoseController = {}

local tracked: { [Model]: Tracked } = {}
local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.RespectCanCollide = true

local function isOnGround(character: Model, humanoid: Humanoid, root: BasePart): boolean
	groundParams.FilterDescendantsInstances = { character, workspace.CurrentCamera }
	local reach = humanoid.HipHeight + root.Size.Y / 2 + GROUND_MARGIN
	return workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), groundParams) ~= nil
end

local function stopPose(entry: Tracked)
	local pose = entry.pose
	entry.pose = nil
	entry.target = nil
	if pose then
		pose:destroy()
	end
end

local function step()
	local now = os.clock()
	local seen: { [Model]: boolean } = {}
	for _, other in Players:GetPlayers() do
		local character = other.Character
		if other == player or not character then
			continue
		end
		local humanoid = character:FindFirstChildOfClass("Humanoid")
		local root = character:FindFirstChild("HumanoidRootPart")
		if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
			continue
		end
		seen[character] = true
		local entry = tracked[character]
		if not entry then
			entry = { pose = nil, groundedSince = nil, target = nil }
			tracked[character] = entry
		end
		local anchor = RopeReplicaController.getAnchor(other)
		local grounded = isOnGround(character, humanoid, root)
		local fast = root.AssemblyLinearVelocity.Magnitude > FAST_SPEED
		if not grounded and (anchor or fast) then
			entry.groundedSince = nil
			if not entry.pose then
				entry.pose = HookPose.new(character, humanoid)
			end
		elseif grounded and entry.pose then
			entry.groundedSince = entry.groundedSince or now
			if now - (entry.groundedSince :: number) >= GROUND_EXIT_TIME then
				stopPose(entry)
			end
		end
		local pose = entry.pose
		if pose and entry.target ~= anchor then
			entry.target = anchor
			pose:setTarget(anchor)
		end
	end
	for character, entry in tracked do
		if not seen[character] then
			stopPose(entry)
			tracked[character] = nil
		end
	end
end

function RemotePoseController.Start()
	RunService.Heartbeat:Connect(step)
end

return RemotePoseController
