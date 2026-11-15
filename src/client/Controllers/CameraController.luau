--!strict
-- Câmera lateral 2.5D (ADR 0011, RF-01). Olha o plano Z do jogo de frente:
-- +X fica à direita da tela e +Y para cima.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local settings = Config.Camera

local CameraController = {}

local focus: Vector3? = nil
local lookAhead = 0

local function getRoot(): BasePart?
	local character = player.Character
	return character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
end

local function update(dt: number)
	local root = getRoot()
	if not root then
		return
	end

	-- Adianta a câmera para o lado em que o personagem está indo.
	local vx = root.AssemblyLinearVelocity.X
	local targetAhead = if math.abs(vx) > 1 then math.sign(vx) * settings.LookAhead else lookAhead
	local alpha = 1 - math.exp(-settings.Smoothing * dt)
	lookAhead += (targetAhead - lookAhead) * alpha * 0.5

	local target = Vector3.new(root.Position.X + lookAhead, root.Position.Y + settings.Height, Config.Plane.Z)
	focus = if focus then focus:Lerp(target, alpha) else target

	local f = focus :: Vector3
	camera.CameraType = Enum.CameraType.Scriptable
	camera.FieldOfView = settings.FieldOfView
	camera.CFrame = CFrame.lookAt(f + Vector3.new(0, 0, settings.Distance), f)
end

function CameraController.Start()
	if Config.Camera.Mode ~= "SideView" then
		return -- 3ª pessoa: usa a câmera padrão do Roblox
	end
	player.CharacterAdded:Connect(function()
		focus = nil -- ao renascer, pula direto para o personagem sem "voar" pelo mapa
	end)
	RunService:BindToRenderStep("CameraController", Enum.RenderPriority.Camera.Value + 1, update)
end

return CameraController
