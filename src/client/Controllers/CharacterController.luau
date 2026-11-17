--!strict
-- Mantém o personagem preso no plano 2.5D (RF-02, RF-03).
-- O cliente é dono da física do próprio personagem, então a trava roda aqui
-- (o servidor também corrige, como rede de segurança: PlaneService, ADR 0039).

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)

local player = Players.LocalPlayer

local CharacterController = {}

-- W/S (e setas cima/baixo) andariam para dentro/fora da tela: o movimento por elas é bloqueado aqui.
-- Quem precisar LER essas teclas (ex.: HookController, para recolher/soltar a corda) faz o bind com
-- prioridade maior que `DepthKeysPriority` e devolve `Pass`: lê a tecla lá e o bloqueio continua aqui.
CharacterController.DepthKeys = table.freeze({
	Enum.KeyCode.W,
	Enum.KeyCode.S,
	Enum.KeyCode.Up,
	Enum.KeyCode.Down,
})
CharacterController.DepthKeysPriority = Enum.ContextActionPriority.High.Value

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
	ContextActionService:BindActionAtPriority("BlockDepthMovement", function()
		return Enum.ContextActionResult.Sink
	end, false, CharacterController.DepthKeysPriority, table.unpack(CharacterController.DepthKeys))

	-- Antes da física (Stepped) e depois dela (Heartbeat), para nada escapar do plano.
	RunService.Stepped:Connect(lockToPlane)
	RunService.Heartbeat:Connect(lockToPlane)
end

return CharacterController
