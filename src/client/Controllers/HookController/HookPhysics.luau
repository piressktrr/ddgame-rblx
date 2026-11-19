--!strict
--[[
	Interface comum dos módulos de física do gancho, um por `Config.Hook.Mode` (ADR 0036, 0042):
	`PullPhysics` (puxão, padrão) e `SwingPhysics` (balanço, referência). Também a sonda do corpo
	contra atravessar paredes, usada pelos dois.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)

local AirBody = require(script.Parent.AirBody)

export type Input = {
	horizontal: number, -- -1 (A) .. 1 (D)
	reel: number, -- -1 recolhe (W), 1 solta (S); só o balanço usa
	held: boolean, -- botão do gancho ainda apertado
}

-- "Release": a física pede para soltar o gancho (chegou ao ponto, bateu em algo ou soltou o botão).
export type StepResult = "Continue" | "Release"

export type Params = {
	character: Model,
	root: BasePart,
	rootAttachment: Attachment,
	anchor: Attachment,
	body: AirBody.AirBody,
}

export type Physics = {
	step: (self: Physics, dt: number, input: Input) -> StepResult,
	getLength: (self: Physics) -> number, -- corda (balanço) ou distância até o ponto (puxão)
	getPhase: (self: Physics) -> string, -- para testes
	destroy: (self: Physics) -> (),
}

export type Mode = {
	new: (params: Params) -> Physics,
	releaseOnButtonUp: boolean, -- soltar o botão solta o gancho na hora
	retargetWhileAttached: boolean, -- clicar em outro alvo enquanto preso troca de alvo
	usesReel: boolean, -- W/S recolhem e soltam corda
}

local BOX_CORNERS = {
	Vector3.new(-1, -1, -1),
	Vector3.new(-1, -1, 1),
	Vector3.new(-1, 1, -1),
	Vector3.new(-1, 1, 1),
	Vector3.new(1, -1, -1),
	Vector3.new(1, -1, 1),
	Vector3.new(1, 1, -1),
	Vector3.new(1, 1, 1),
}

local HookPhysics = {}

-- Corda visível (só visual, sem física) entre dois Attachments.
function HookPhysics.createRope(from: Attachment, to: Attachment, parent: Instance): Beam
	local rope = Instance.new("Beam")
	rope.Name = "HookRope"
	rope.Attachment0 = from
	rope.Attachment1 = to
	rope.Width0 = Config.Hook.RopeThickness
	rope.Width1 = Config.Hook.RopeThickness
	rope.FaceCamera = true
	rope.Segments = 1
	rope.LightInfluence = 0
	rope.Color = ColorSequence.new(Config.Hook.RopeColor)
	rope.Transparency = NumberSequence.new(0)
	rope.Parent = parent
	return rope
end

-- Caixa do corpo no espaço do root (centro e tamanho), a partir das peças diretas do personagem
-- (tronco, membros, cabeça; acessórios ficam de fora).
local function measureBody(character: Model, root: BasePart): (Vector3, Vector3)
	local minCorner = Vector3.one * math.huge
	local maxCorner = -Vector3.one * math.huge
	for _, child in character:GetChildren() do
		if child:IsA("BasePart") then
			local relative = root.CFrame:ToObjectSpace(child.CFrame)
			local half = child.Size / 2
			for _, corner in BOX_CORNERS do
				local point = relative * (half * corner)
				minCorner = minCorner:Min(point)
				maxCorner = maxCorner:Max(point)
			end
		end
	end
	return (minCorner + maxCorner) / 2, maxCorner - minCorner
end

-- Sonda: a caixa do corpo, encolhida `inset` studs de cada lado (para não acusar o chão em que pisa),
-- deslocada `distance` studs numa direção. Devolve uma função que diz se ela toca algo colidível
-- (fora `ignore`, se for passada).
function HookPhysics.createBodyProbe(
	character: Model,
	root: BasePart,
	inset: number,
	distance: number
): (direction: Vector3, ignore: BasePart?) -> boolean
	local probeCenter, probeSize = measureBody(character, root)
	probeSize -= Vector3.one * (2 * inset)
	local overlapParams = OverlapParams.new()
	overlapParams.FilterType = Enum.RaycastFilterType.Exclude
	overlapParams.FilterDescendantsInstances = { character }
	overlapParams.RespectCanCollide = true

	return function(direction: Vector3, ignore: BasePart?): boolean
		local center = root.CFrame:PointToWorldSpace(probeCenter) + direction * distance
		local probe = CFrame.new(center) * root.CFrame.Rotation
		for _, part in workspace:GetPartBoundsInBox(probe, probeSize, overlapParams) do
			if part ~= ignore then
				return true
			end
		end
		return false
	end
end

return HookPhysics
