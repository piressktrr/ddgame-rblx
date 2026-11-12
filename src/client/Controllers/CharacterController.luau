--!strict
-- Mantém o personagem preso no plano 2.5D (RF-02, RF-03).
-- O cliente é dono da física do próprio personagem, então a trava roda aqui.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)

local player = Players.LocalPlayer

local CharacterController = {}

local function lockToPlane()
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then
		return
	end

	local planeZ = Config.Plane.Z
	local pos = root.Position
	if math.abs(pos.Z - planeZ) > Config.Plane.MaxDrift then
		root.CFrame += Vector3.new(0, 0, planeZ - pos.Z)
	end

	local vel = root.AssemblyLinearVelocity
	if vel.Z ~= 0 then
		root.AssemblyLinearVelocity = Vector3.new(vel.X, vel.Y, 0)
	end
end

function CharacterController.Start()
	-- W/S (e setas cima/baixo) andariam para dentro/fora da tela: desligados no 2.5D.
	ContextActionService:BindActionAtPriority(
		"BlockDepthMovement",
		function()
			return Enum.ContextActionResult.Sink
		end,
		false,
		Enum.ContextActionPriority.High.Value,
		Enum.KeyCode.W,
		Enum.KeyCode.S,
		Enum.KeyCode.Up,
		Enum.KeyCode.Down
	)

	-- Antes da física (Stepped) e depois dela (Heartbeat), para nada escapar do plano.
	RunService.Stepped:Connect(lockToPlane)
	RunService.Heartbeat:Connect(lockToPlane)
end

return CharacterController
