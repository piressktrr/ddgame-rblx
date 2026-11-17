--!strict
--[[
	Física do gancho tipo B, balanço (ADR 0036, RF-17, RF-18): uma `RopeConstraint` entre o root e o
	ponto atingido (a engine resolve o pêndulo). O controle do corpo (estado do Humanoid, A/D, ficar em
	pé, limite de velocidade) fica no `AirBody`, que este módulo recebe pronto.

	Desde o ADR 0042 não é o modo padrão (`Config.Hook.Mode = "Swing"` para usar): fica como referência.

	W/S mudam o `Length` aos poucos (HookRules.nextRopeLength). Ao recolher, uma sonda do tamanho do
	corpo, deslocada um pouco na direção da corda, procura obstáculos: se achar, a corda para de
	encurtar. Medido em playtest: sem a sonda, recolher com uma plataforma no caminho arrastava o
	personagem para dentro dela aos poucos (a corda vence o contato).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookPhysics = require(script.Parent.HookPhysics)

local settings = Config.Hook

local LIMITS: HookRules.RopeLimits = {
	minLength = settings.MinRopeLength,
	maxLength = settings.MaxRopeLength,
	reelInSpeed = settings.ReelInSpeed,
	reelOutSpeed = settings.ReelOutSpeed,
	maxLead = settings.ReelMaxLead,
}

local SwingPhysics = {}

function SwingPhysics.new(params: HookPhysics.Params): HookPhysics.Physics
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

	-- Algo colidível logo à frente do corpo, na direção da corda?
	local isPullBlocked = HookPhysics.createBodyProbe(
		params.character,
		root,
		settings.ReelProbeInset,
		settings.ReelProbeDistance
	)

	local physics = {} :: HookPhysics.Physics

	function physics.step(
		_self: HookPhysics.Physics,
		dt: number,
		input: HookPhysics.Input
	): HookPhysics.StepResult
		local toAnchor = anchor.WorldPosition - rootAttachment.WorldPosition
		local distance = toAnchor.Magnitude
		if input.reel < 0 and distance > 0 and isPullBlocked(toAnchor.Unit) then
			-- Bloqueado: não encurta e alivia a tensão extra, para não empurrar o corpo para dentro da peça.
			rope.Length = math.max(rope.Length, math.min(distance, LIMITS.maxLength))
		else
			rope.Length = HookRules.nextRopeLength(rope.Length, input.reel, dt, distance, LIMITS)
		end
		body:step(dt, input.horizontal)
		return "Continue"
	end

	function physics.getLength(_self: HookPhysics.Physics): number
		return rope.Length
	end

	function physics.getPhase(_self: HookPhysics.Physics): string
		return "Swing"
	end

	function physics.destroy(_self: HookPhysics.Physics)
		trove:Destroy()
	end

	return physics
end

SwingPhysics.mode = table.freeze({
	new = SwingPhysics.new,
	releaseOnButtonUp = true,
	retargetWhileAttached = false,
	usesReel = true,
}) :: HookPhysics.Mode

return SwingPhysics
