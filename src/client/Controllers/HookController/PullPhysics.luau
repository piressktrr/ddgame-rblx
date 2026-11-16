--!strict
--[[
	Física do gancho tipo A, puxão direto (ADR 0042), o modo padrão: um clique prende e o personagem é
	levado em linha reta até o ponto, sozinho.

	- Um `LinearVelocity` no root segue uma velocidade pedida que muda aos poucos
	  (`Config.Hook.PullAccel`) até a de cruzeiro (`PullSpeed`): nada de teleporte.
	- Chegou (`ArriveDistance`) com o botão ainda apertado: fica preso parado ali até soltar. Enquanto
	  o botão está apertado, o puxão já freia para parar em cima do ponto.
	- Chegou com o botão já solto: o gancho solta e sobra `ReleaseMomentumFraction` da velocidade.
	- Sonda do corpo na direção do voo (a mesma ideia do recolher do balanço): se tocar algo colidível
	  perto do ponto, conta como chegou; longe do ponto, solta sem empurrar contra o obstáculo.
	- Tudo no plano: a velocidade pedida não tem Z (o `CharacterController` corrige o desvio).
	- O controle do corpo (estado do Humanoid, ficar em pé, embalo depois de soltar) fica no `AirBody`;
	  durante o puxão ele recebe A/D = 0. Corda visível só localmente (um `Beam`, sem física).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookPhysics = require(script.Parent.HookPhysics)

type Phase = "Pull" | "Hold"

local settings = Config.Hook
local planeZ = Config.Plane.Z

local PullPhysics = {}

local function inPlane(vector: Vector3): Vector3
	return Vector3.new(vector.X, vector.Y, 0)
end

function PullPhysics.new(params: HookPhysics.Params): HookPhysics.Physics
	local root = params.root
	local anchor = params.anchor
	local rootAttachment = params.rootAttachment
	local body = params.body
	local trove = Trove.new()

	local rope = Instance.new("Beam")
	rope.Name = "HookRope"
	rope.Attachment0 = rootAttachment
	rope.Attachment1 = anchor
	rope.Width0 = settings.RopeThickness
	rope.Width1 = settings.RopeThickness
	rope.FaceCamera = true
	rope.Segments = 1
	rope.LightInfluence = 0
	rope.Color = ColorSequence.new(settings.RopeColor)
	rope.Transparency = NumberSequence.new(0)
	rope.Parent = root
	trove:Add(rope)

	-- Velocidade pedida: começa na atual (sem tranco) e muda aos poucos.
	local command = inPlane(root.AssemblyLinearVelocity)
	local mover = Instance.new("LinearVelocity")
	mover.Name = "HookPull"
	mover.Attachment0 = rootAttachment
	mover.RelativeTo = Enum.ActuatorRelativeTo.World
	mover.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
	mover.ForceLimitMode = Enum.ForceLimitMode.Magnitude
	mover.MaxForce = root.AssemblyMass * (workspace.Gravity + settings.PullMaxForceAccel)
	mover.VectorVelocity = command
	mover.Parent = root
	trove:Add(mover)

	-- Prendeu com o personagem no chão: no estado `Running` o Humanoid segura o corpo no chão (medido
	-- em playtest: puxão a ~42° ficou preso a 2,6 studs/s). O `AirBody` assume na hora (estado
	-- `Physics`) e o `LinearVelocity` tira o corpo do chão.
	local humanoid = params.character:FindFirstChildOfClass("Humanoid")
	local toTargetAtStart = anchor.WorldPosition - root.Position
	if
		humanoid
		and humanoid.FloorMaterial ~= Enum.Material.Air
		and toTargetAtStart.Magnitude > 0
		and toTargetAtStart.Unit.Y > settings.PullTakeOffMinUp
	then
		params.body:takeOff()
	end

	local isBlocked = HookPhysics.createBodyProbe(
		params.character,
		root,
		settings.ReelProbeInset,
		settings.PullProbeDistance
	)

	local anchorParent = anchor.Parent
	local targetPart: BasePart? = if anchorParent and anchorParent:IsA("BasePart") then anchorParent else nil
	local phase: Phase = "Pull"
	local holdOffset = Vector3.zero -- posição do root em relação ao ponto enquanto preso
	local elapsed = 0

	-- Ponto do gancho no plano (segue a peça se ela se mover).
	local function targetPoint(): Vector3
		local point = anchor.WorldPosition
		return Vector3.new(point.X, point.Y, planeZ)
	end

	local function releaseWithMomentum(): HookPhysics.StepResult
		root.AssemblyLinearVelocity = inPlane(root.AssemblyLinearVelocity) * settings.ReleaseMomentumFraction
		return "Release"
	end

	-- Chegou: segurando, fica preso onde está; senão, solta com parte do embalo.
	local function arrive(held: boolean): HookPhysics.StepResult
		if not held then
			return releaseWithMomentum()
		end
		phase = "Hold"
		holdOffset = inPlane(root.Position - targetPoint())
		return "Continue"
	end

	local physics = {} :: HookPhysics.Physics

	function physics.step(
		_self: HookPhysics.Physics,
		dt: number,
		input: HookPhysics.Input
	): HookPhysics.StepResult
		elapsed += dt
		local target = targetPoint()
		local position = root.Position

		if phase == "Hold" then
			if not input.held then
				return releaseWithMomentum()
			end
			local offset = inPlane(target + holdOffset - position)
			command = HookRules.clampSpeed(offset * settings.HoldGain, settings.PullSpeed)
			mover.VectorVelocity = command
			body:step(dt, 0)
			return "Continue"
		end

		local toTarget = inPlane(target - position)
		local distance = toTarget.Magnitude
		if distance <= settings.ArriveDistance then
			return arrive(input.held)
		end
		local direction = toTarget / distance
		if distance <= settings.PullBlockedArriveDistance and isBlocked(direction) then
			return arrive(input.held) -- encostou perto do ponto (teto/parede do próprio alvo)
		end
		-- A peça-alvo não conta como obstáculo: o corpo pode raspar nela e deslizar até o ponto
		-- (medido em playtest: trocar de alvo rente ao teto soltava a 20 studs do ponto).
		if isBlocked(direction, targetPart) then
			-- Obstáculo no meio do caminho: solta, tirando a parte da velocidade que vai contra ele.
			local velocity = inPlane(root.AssemblyLinearVelocity)
			root.AssemblyLinearVelocity = velocity - direction * math.max(velocity:Dot(direction), 0)
			return "Release"
		end
		if elapsed >= settings.PullMaxTime then
			return releaseWithMomentum() -- algo segurou o personagem no caminho
		end

		local speed = HookRules.pullSpeed(
			distance - settings.ArriveDistance,
			settings.PullSpeed,
			settings.PullAccel,
			settings.PullArriveSpeed,
			input.held
		)
		command = HookRules.moveToward(command, direction * speed, settings.PullAccel * dt)
		mover.VectorVelocity = command
		body:step(dt, 0)
		return "Continue"
	end

	function physics.getLength(_self: HookPhysics.Physics): number
		return inPlane(targetPoint() - root.Position).Magnitude
	end

	function physics.getPhase(_self: HookPhysics.Physics): string
		return phase
	end

	function physics.destroy(_self: HookPhysics.Physics)
		trove:Destroy()
	end

	return physics
end

PullPhysics.mode = table.freeze({
	new = PullPhysics.new,
	releaseOnButtonUp = false,
	retargetWhileAttached = true,
	usesReel = false,
}) :: HookPhysics.Mode

return PullPhysics
