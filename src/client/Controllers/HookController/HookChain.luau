--!strict
--[[
	Visual do gancho no estilo do DDNet: corrente de elos (um de frente, um de lado, alternados) e uma
	garra de metal na ponta. Só visual e só local: peças ancoradas, sem colisão nem consulta de raio,
	dentro da câmera, atualizadas a cada quadro entre dois Attachments.

	`HookChain.new(from, to)` devolve um Model; destruir o Model (ou um dos Attachments sumir) encerra.
	Usado pelo gancho próprio (HookPhysics.createRope) e pela corda dos outros (RopeReplicaController).
]]

local RunService = game:GetService("RunService")

local HookChain = {}

local LINK_LENGTH = 0.85 -- studs por elo
local LINK_WIDTH = 0.62 -- elo de frente: largura no plano
local LINK_THICKNESS = 0.22 -- elo de lado: espessura no plano
local LINK_OVERLAP = 1.15 -- elos se encaixam um no outro
local MAX_LINKS = 80

local DARK = Color3.fromRGB(95, 98, 108)
local LIGHT = Color3.fromRGB(150, 153, 162)
local CLAW = Color3.fromRGB(175, 178, 186)

local function newPart(name: string, color: Color3): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.SmoothPlastic
	part.Color = color
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	return part
end

function HookChain.new(from: Attachment, to: Attachment): Model
	local model = Instance.new("Model")
	model.Name = "HookChain"

	local links: { Part } = {}
	-- Garra: base + duas pontas abertas em V, apontando para a frente.
	local clawBase = newPart("ClawBase", CLAW)
	clawBase.Size = Vector3.new(0.7, 0.42, 0.6)
	clawBase.Parent = model
	local prongs: { Part } = {}
	for index = 1, 2 do
		local prong = newPart("ClawProng", CLAW)
		prong.Size = Vector3.new(0.18, 0.42, 0.8)
		prong.Parent = model
		prongs[index] = prong
	end

	local function update()
		if not from.Parent or not to.Parent then
			return
		end
		local a = from.WorldPosition
		local b = to.WorldPosition
		local delta = b - a
		local length = delta.Magnitude
		if length < 0.1 then
			return
		end
		local direction = delta / length
		-- Eixo de "cima" = profundidade (Z): o -Z local segue a corda e o X local fica no plano.
		local up = if math.abs(direction.Z) > 0.99 then Vector3.yAxis else Vector3.zAxis
		local count = math.clamp(math.floor(length / LINK_LENGTH), 1, MAX_LINKS)
		local step = length / count
		for index = 1, count do
			local link = links[index]
			if not link then
				link = newPart("Link", if index % 2 == 0 then LIGHT else DARK)
				links[index] = link
			end
			local center = a + direction * (step * (index - 0.5))
			local frame = CFrame.lookAlong(center, direction, up)
			if index % 2 == 0 then
				frame *= CFrame.Angles(0, 0, math.rad(90)) -- elo de lado
			end
			link.Size = Vector3.new(LINK_WIDTH, LINK_THICKNESS, step * LINK_OVERLAP)
			link.CFrame = frame
			link.Parent = model
		end
		for index = count + 1, #links do
			links[index].Parent = nil
		end

		local tip = CFrame.lookAlong(b, direction, up)
		clawBase.CFrame = tip * CFrame.new(0, 0, 0.14)
		prongs[1].CFrame = tip * CFrame.new(0.24, 0, -0.33) * CFrame.Angles(0, math.rad(-35), 0)
		prongs[2].CFrame = tip * CFrame.new(-0.24, 0, -0.33) * CFrame.Angles(0, math.rad(35), 0)
	end

	update()
	local connection = RunService.RenderStepped:Connect(update)
	model.Destroying:Connect(function()
		connection:Disconnect()
	end)
	model.Parent = workspace.CurrentCamera
	return model
end

return HookChain
