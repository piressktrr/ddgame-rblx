--!strict
--[[
	Armas equipáveis (como no DDRace). O gancho não é arma: está sempre disponível no botão direito.

	- Botão esquerdo do mouse dispara a arma equipada.
	- Roda do mouse troca de arma (cíclico). Por enquanto só o martelo; novas armas entram em `WEAPONS`.
	- HUD pequena embaixo, no centro, com a arma equipada.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local HammerController = require(script.Parent.HammerController)

type Weapon = {
	name: string,
	fire: () -> (),
}

local WEAPONS: { Weapon } = {
	{ name = "Martelo", fire = HammerController.fire },
}

local player = Players.LocalPlayer

local WeaponController = {}

local current = 1
local label: TextLabel? = nil

local function refreshHud()
	local hud = label
	if hud then
		hud.Text = if #WEAPONS > 1
			then `{WEAPONS[current].name}  (roda do mouse troca)`
			else WEAPONS[current].name
	end
end

local function createHud()
	local gui = Instance.new("ScreenGui")
	gui.Name = "WeaponHud"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	local text = Instance.new("TextLabel")
	text.Name = "Weapon"
	text.AnchorPoint = Vector2.new(0.5, 1)
	text.Position = UDim2.new(0.5, 0, 1, -16)
	text.Size = UDim2.fromOffset(260, 30)
	text.BackgroundColor3 = Color3.fromRGB(20, 22, 30)
	text.BackgroundTransparency = 0.35
	text.TextColor3 = Color3.new(1, 1, 1)
	text.Font = Enum.Font.GothamBold
	text.TextSize = 16
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 8)
	corner.Parent = text
	text.Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	label = text
	refreshHud()
end

-- Troca de arma: `step` +1 próxima, -1 anterior.
function WeaponController.cycle(step: number)
	current = (current - 1 + step) % #WEAPONS + 1
	refreshHud()
end

function WeaponController.getCurrent(): string
	return WEAPONS[current].name
end

function WeaponController.Start()
	createHud()
	UserInputService.InputBegan:Connect(function(input: InputObject, gameProcessed: boolean)
		if input.UserInputType == Enum.UserInputType.MouseButton1 and not gameProcessed then
			WEAPONS[current].fire()
		end
	end)
	UserInputService.InputChanged:Connect(function(input: InputObject, gameProcessed: boolean)
		if input.UserInputType == Enum.UserInputType.MouseWheel and not gameProcessed and #WEAPONS > 1 then
			WeaponController.cycle(if input.Position.Z > 0 then -1 else 1)
		end
	end)

	if RunService:IsStudio() then
		local bindable = Instance.new("BindableFunction")
		bindable.Name = "WeaponDebug"
		bindable.OnInvoke = function(command: string, step: number?): any
			if command == "fire" then
				WEAPONS[current].fire()
			elseif command == "cycle" then
				WeaponController.cycle(step or 1)
			end
			return WeaponController.getCurrent()
		end
		bindable.Parent = script
	end
end

return WeaponController
