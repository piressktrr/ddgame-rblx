--!strict
--[[
	Retículo do gancho (RF-12, IMPLEMENTATION_PLAN Fase 1 item 5): um anel em volta do cursor com três
	estados (sem alvo, alvo válido, alvo proibido) e um ponto no mundo onde o gancho prenderia.
	Ao tentar prender em superfície proibida, o anel pisca (retorno visual do roxo / verde já usado).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

export type Reticle = {
	update: (
		self: Reticle,
		cursor: Vector2?,
		state: HookRules.TargetState,
		markerPoint: Vector3?,
		camera: Camera
	) -> (),
	flashForbidden: (self: Reticle) -> (),
	destroy: (self: Reticle) -> (),
}

local settings = Config.Hook

local COLORS: { [HookRules.TargetState]: Color3 } = {
	None = settings.ReticleNoTargetColor,
	Valid = settings.ReticleValidColor,
	Forbidden = settings.ReticleForbiddenColor,
}

local Reticle = {}

local function makeCircle(name: string, size: number, parent: Instance): Frame
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Size = UDim2.fromOffset(size, size)
	frame.BorderSizePixel = 0
	frame.Active = false
	frame.Visible = false
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.5, 0)
	corner.Parent = frame
	frame.Parent = parent
	return frame
end

function Reticle.new(playerGui: Instance): Reticle
	local trove = Trove.new()

	local gui = Instance.new("ScreenGui")
	gui.Name = "HookReticle"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true -- posição da GUI = posição do mouse (GetMouseLocation)
	gui.DisplayOrder = 10
	trove:Add(gui)

	local ring = makeCircle("Ring", settings.ReticleSize, gui)
	ring.BackgroundTransparency = 1
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2
	stroke.Parent = ring

	local marker = makeCircle("Marker", settings.ReticleMarkerSize, gui)

	gui.Parent = playerGui

	local flashUntil = 0

	local reticle = {} :: Reticle

	function reticle.update(
		_self: Reticle,
		cursor: Vector2?,
		state: HookRules.TargetState,
		markerPoint: Vector3?,
		camera: Camera
	)
		local flashing = os.clock() < flashUntil
		local color = if flashing then COLORS.Forbidden else COLORS[state]

		if cursor then
			ring.Visible = true
			ring.Position = UDim2.fromOffset(cursor.X, cursor.Y)
			local size = if flashing
				then settings.ReticleSize * settings.ForbiddenFlashScale
				else settings.ReticleSize
			ring.Size = UDim2.fromOffset(size, size)
			stroke.Color = color
		else
			ring.Visible = false
		end

		if markerPoint then
			local screenPoint, onScreen = camera:WorldToViewportPoint(markerPoint)
			marker.Visible = onScreen
			marker.Position = UDim2.fromOffset(screenPoint.X, screenPoint.Y)
			marker.BackgroundColor3 = color
			-- Sem alvo, o ponto só mostra até onde o gancho alcança (mais apagado).
			marker.BackgroundTransparency = if state == "None" and not flashing then 0.6 else 0
		else
			marker.Visible = false
		end
	end

	function reticle.flashForbidden(_self: Reticle)
		flashUntil = os.clock() + settings.ForbiddenFlashTime
	end

	function reticle.destroy(_self: Reticle)
		trove:Destroy()
	end

	return reticle
end

return Reticle
