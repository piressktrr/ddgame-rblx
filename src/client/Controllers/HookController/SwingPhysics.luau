--!strict
--[[
	Física do gancho tipo B, balanço (ADR 0036, RF-17, RF-18): uma `RopeConstraint` entre o root e o
	ponto atingido (a engine resolve o pêndulo). O controle do corpo (estado do Humanoid, A/D, ficar em
	pé, limite de velocidade) fica no `AirBody`, que este módulo recebe pronto.

	W/S mudam o `Length` aos poucos (HookRules.nextRopeLength). Ao recolher, uma sonda do tamanho do
	corpo, deslocada um pouco na direção da corda, procura obstáculos: se achar, a corda para de
	encurtar. Medido em playtest: sem a sonda, recolher com uma plataforma no caminho arrastava o
	personagem para dentro dela aos poucos (a corda vence o contato).

	O plano B (puxão, tipo A) seria outro módulo com a mesma interface (`step`, `getLength`, `destroy`).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local AirBody = require(script.Parent.AirBody)

export type Input = {
	horizontal: number, -- -1 (A) .. 1 (D)
	reel: number, -- -1 recolhe (W), 1 solta (S)
}

export type Params = {
	character: Model,
	root: BasePart,
	rootAttachment: Attachment,
	anchor: Attachment,
	body: AirBody.AirBody,
}

export type Physics = {
	step: (self: Physics, dt: number, input: Input) -> (),
	getLength: (self: Physics) -> number,
	destroy: (self: Physics) -> (),
}

local settings = Config.Hook

local LIMITS: HookRules.RopeLimits = {
	minLength = settings.MinRopeLength,
	maxLength = settings.MaxRopeLength,
	reelInSpeed = settings.ReelInSpeed,
	reelOutSpeed = settings.ReelOutSpeed,
	maxLead = settings.ReelMaxLead,
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

local SwingPhysics = {}

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

function SwingPhysics.new(params: Params): Physics
	local root = params.root
	local anchor = params.anchor
	local rootAttachment = params.rootAttachment
	local body = params.body
	local trove = Trove.new()

	local rope = Instance.new("RopeConstraint")
	rope.Name = "HookRope"
	rope.Attachment0 = rootAttachment
	rope.Attachment1 = anchor
	rope.Length =
		HookRules.initialRopeLength((anchor.WorldPosition - rootAttachment.WorldPosition).Magnitude, LIMITS)
	rope.Restitution = 0
	rope.Visible = true
	rope.Thickness = settings.RopeThickness
	rope.Color = BrickColor.new(settings.RopeColor)
	rope.Parent = root
	trove:Add(rope)

	local probeCenter, probeSize = measureBody(params.character, root)
	probeSize -= Vector3.one * (2 * settings.ReelProbeInset)
	local overlapParams = OverlapParams.new()
	overlapParams.FilterType = Enum.RaycastFilterType.Exclude
	overlapParams.FilterDescendantsInstances = { params.character }
	overlapParams.RespectCanCollide = true

	-- Algo colidível logo à frente do corpo, na direção da corda?
	local function isPullBlocked(pullDirection: Vector3): boolean
		local center = root.CFrame:PointToWorldSpace(probeCenter) + pullDirection * settings.ReelProbeDistance
		local probe = CFrame.new(center) * root.CFrame.Rotation
		return #workspace:GetPartBoundsInBox(probe, probeSize, overlapParams) > 0
	end

	local physics = {} :: Physics

	function physics.step(_self: Physics, dt: number, input: Input)
		local toAnchor = anchor.WorldPosition - rootAttachment.WorldPosition
		local distance = toAnchor.Magnitude
		if input.reel < 0 and distance > 0 and isPullBlocked(toAnchor.Unit) then
			-- Bloqueado: não encurta e alivia a tensão extra, para não empurrar o corpo para dentro da peça.
			rope.Length = math.max(rope.Length, math.min(distance, LIMITS.maxLength))
		else
			rope.Length = HookRules.nextRopeLength(rope.Length, input.reel, dt, distance, LIMITS)
		end
		body:step(dt, input.horizontal)
	end

	function physics.getLength(_self: Physics): number
		return rope.Length
	end

	function physics.destroy(_self: Physics)
		trove:Destroy()
	end

	return physics
end

return SwingPhysics
