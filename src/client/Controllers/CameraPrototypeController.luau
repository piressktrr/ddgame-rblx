--!strict
-- PROTÓTIPO (Q2): compara câmera em 3ª pessoa e 2.5D. Tecla C alterna os modos.
-- Código descartável: quando a câmera for decidida, vira um CameraController definitivo.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

type Mode = "ThirdPerson" | "SideView"

local SIDE_DISTANCE = 28 -- distância da câmera lateral
local SIDE_HEIGHT = 4 -- altura extra da câmera lateral
local SIDE_FOV = 50
local THIRD_ZOOM = 14

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera

local CameraPrototypeController = {}

local mode: Mode = "ThirdPerson"
local planeZ: number? = nil -- plano onde o personagem fica preso no 2.5D
local label: TextLabel? = nil

local function getRoot(): BasePart?
	local character = player.Character
	return character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
end

local function updateLabel()
	if label then
		label.Text = if mode == "SideView"
			then "Câmera: 2.5D (lateral)  —  C para trocar"
			else "Câmera: 3ª pessoa  —  C para trocar"
	end
end

local function applyMode()
	if mode == "SideView" then
		local root = getRoot()
		planeZ = root and root.Position.Z or 0
		camera.CameraType = Enum.CameraType.Scriptable
		camera.FieldOfView = SIDE_FOV
	else
		planeZ = nil
		camera.CameraType = Enum.CameraType.Custom
		camera.FieldOfView = 70
		player.CameraMinZoomDistance = THIRD_ZOOM
		player.CameraMaxZoomDistance = THIRD_ZOOM
		task.defer(function()
			player.CameraMinZoomDistance = 0.5
			player.CameraMaxZoomDistance = 40
		end)
	end
	updateLabel()
	print("[Camera] Modo:", mode)
end

local function createLabel()
	local gui = Instance.new("ScreenGui")
	gui.Name = "CameraPrototypeHud"
	gui.ResetOnSpawn = false
	local text = Instance.new("TextLabel")
	text.Size = UDim2.fromOffset(360, 32)
	text.Position = UDim2.fromOffset(12, 12)
	text.BackgroundTransparency = 0.4
	text.BackgroundColor3 = Color3.new(0, 0, 0)
	text.TextColor3 = Color3.new(1, 1, 1)
	text.TextSize = 18
	text.Font = Enum.Font.GothamBold
	text.Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	label = text
end

function CameraPrototypeController.Start()
	createLabel()
	applyMode()

	UserInputService.InputBegan:Connect(function(input, processed)
		if processed or input.KeyCode ~= Enum.KeyCode.C then
			return
		end
		mode = if mode == "ThirdPerson" then "SideView" else "ThirdPerson"
		applyMode()
	end)

	player.CharacterAdded:Connect(function()
		task.wait()
		applyMode()
	end)

	-- 2.5D: prende o personagem no plano Z e posiciona a câmera de lado.
	RunService:BindToRenderStep("CameraPrototype", Enum.RenderPriority.Camera.Value + 1, function()
		if mode ~= "SideView" then
			return
		end
		local root = getRoot()
		if not root or not planeZ then
			return
		end
		local pos = root.Position
		if math.abs(pos.Z - planeZ) > 0.01 then
			root.CFrame = root.CFrame + Vector3.new(0, 0, planeZ - pos.Z)
		end
		local vel = root.AssemblyLinearVelocity
		root.AssemblyLinearVelocity = Vector3.new(vel.X, vel.Y, 0)

		local focus = Vector3.new(pos.X, pos.Y + SIDE_HEIGHT, planeZ)
		camera.CFrame = CFrame.lookAt(focus + Vector3.new(0, 0, SIDE_DISTANCE), focus)
	end)
end

return CameraPrototypeController
