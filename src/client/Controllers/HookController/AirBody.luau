--!strict
--[[
	Controle do corpo enquanto o gancho está preso e logo depois de soltar (RF-17, RF-19).

	O Humanoid briga com forças externas. Medido em playtest (2026-11-16): em `Freefall`, sem tecla
	apertada, ele freia a velocidade horizontal (76 -> 31 studs/s em 0,3 s), o que mataria o impulso do
	balanço ao soltar. Por isso, enquanto este corpo existe, o Humanoid fica no estado `Physics` (sem
	controle próprio) e:
	  - um `VectorForce` horizontal aplica A/D (dirige o balanço e dá controle no ar);
	  - um `AlignOrientation` mantém o personagem em pé, virado para ±X;
	  - a velocidade horizontal tem limite (`Config.Hook.MaxSwingSpeed`); a queda não.

	Se o gancho prende com o personagem no chão, o Humanoid continua andando normalmente (no estado
	`Physics` o A/D mal vence o atrito do chão); o corpo só assume quando o personagem sai do chão
	(`FloorMaterial` vira `Air`) ou quando alguém chama `takeOff()`, e daí em diante não devolve até o
	fim (troca de mão única, sem piscar).

	Depois de soltar vem o "embalo": no ar, só termina ao passar `Config.Hook.MomentumMaxTime`; ao pousar
	com embalo, desliza e freia com `Config.Hook.LandingSlideDecel` e termina quando a velocidade
	horizontal cai até a de andar (`Humanoid.WalkSpeed`).
	Aí o Humanoid volta a `Freefall` e retoma o controle normal.

	Pose: enquanto o corpo controla (no ar), `HookPose` põe uma pose procedural de voo (braço para o ponto
	do gancho, corpo inclinado, pernas para trás), entrando e saindo em ~0,15 s. Quem prende chama
	`setAimPoint(anchor)` e, ao soltar, `beginMomentum()` já tira o alvo (o braço volta para trás).
	A animação de queda do `Animate` continua tocando por baixo só porque os `Transform` da pose não
	replicam: é ela que os outros jogadores veem (no `Physics` o boneco deles ficaria duro).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookPose = require(script.Parent.HookPose)

export type AirBody = {
	step: (self: AirBody, dt: number, horizontal: number) -> (),
	-- Para onde o braço da pose aponta: o Attachment do ponto preso (acompanha peça que se move),
	-- uma posição, ou nil (sem alvo).
	setAimPoint: (self: AirBody, target: HookPose.AimTarget?) -> (),
	-- Assume o corpo agora (estado `Physics`), mesmo com o personagem no chão.
	takeOff: (self: AirBody) -> (),
	beginMomentum: (self: AirBody) -> (),
	cancelMomentum: (self: AirBody) -> (),
	isMomentumOver: (self: AirBody) -> boolean,
	destroy: (self: AirBody) -> (),
}

local settings = Config.Hook

local AirBody = {}

local function facingCFrame(facing: number): CFrame
	return CFrame.lookAlong(Vector3.zero, Vector3.new(facing, 0, 0))
end

function AirBody.new(
	character: Model,
	humanoid: Humanoid,
	root: BasePart,
	rootAttachment: Attachment
): AirBody
	local trove = Trove.new()

	local force = Instance.new("VectorForce")
	force.Name = "HookAirForce"
	force.Attachment0 = rootAttachment
	force.RelativeTo = Enum.ActuatorRelativeTo.World
	force.ApplyAtCenterOfMass = true
	force.Force = Vector3.zero
	force.Parent = root
	trove:Add(force)

	local facing = if root.CFrame.LookVector.X < 0 then -1 else 1
	local upright = Instance.new("AlignOrientation")
	upright.Name = "HookUpright"
	upright.Mode = Enum.OrientationAlignmentMode.OneAttachment
	upright.Attachment0 = rootAttachment
	upright.CFrame = facingCFrame(facing)
	upright.MaxTorque = math.huge
	upright.Responsiveness = settings.UprightResponsiveness
	upright.Enabled = false
	upright.Parent = root
	trove:Add(upright)

	-- Animação de queda do próprio Animate (nada de asset novo): no estado `Physics` o script Animate
	-- para e o boneco ficaria duro. Localmente a `HookPose` a cobre; ela fica para os outros jogadores.
	local poseTrack: AnimationTrack? = nil
	local animator = humanoid:FindFirstChildOfClass("Animator")
	local animate = character:FindFirstChild("Animate")
	local fallFolder = animate and animate:FindFirstChild("fall")
	local fallAnimation = fallFolder and fallFolder:FindFirstChildOfClass("Animation")
	if animator and fallAnimation then
		local ok, track = pcall(function()
			return animator:LoadAnimation(fallAnimation)
		end)
		if ok and track then
			track.Looped = true
			track.Priority = Enum.AnimationPriority.Action
			poseTrack = track
			trove:Add(function()
				track:Stop(0.15)
			end)
		end
	end

	-- true quando o corpo assumiu (Humanoid em `Physics`); false enquanto o personagem está no chão.
	local airborne = false
	local aimTarget: HookPose.AimTarget? = nil
	local pose: HookPose.HookPose? = nil
	trove:Add(function()
		if pose then
			pose:destroy() -- sai da pose suavemente, sozinha
			pose = nil
		end
	end)

	local function enterAir()
		airborne = true
		if poseTrack then
			poseTrack:Play(0.1)
		end
		local newPose = HookPose.new(character, humanoid)
		newPose:setTarget(aimTarget)
		pose = newPose
		facing = if root.CFrame.LookVector.X < 0 then -1 else 1
		upright.CFrame = facingCFrame(facing)
		upright.Enabled = true
		humanoid:ChangeState(Enum.HumanoidStateType.Physics)
	end
	if humanoid.FloorMaterial == Enum.Material.Air then
		enterAir()
	end

	trove:Add(function()
		-- Devolve o controle ao Humanoid (se ainda estiver vivo e no estado que colocamos).
		if humanoid.Health > 0 and humanoid:GetState() == Enum.HumanoidStateType.Physics then
			humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
		end
	end)

	local groundParams = RaycastParams.new()
	groundParams.FilterType = Enum.RaycastFilterType.Exclude
	groundParams.FilterDescendantsInstances = { character }
	groundParams.RespectCanCollide = true

	local momentumStart: number? = nil

	local function isGrounded(): boolean
		if root.AssemblyLinearVelocity.Y > 0 then
			return false -- subindo: ainda não pousou
		end
		local reach = humanoid.HipHeight + root.Size.Y / 2 + settings.GroundCheckMargin
		return workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), groundParams) ~= nil
	end

	local body = {} :: AirBody

	function body.step(_self: AirBody, _dt: number, horizontal: number)
		if not airborne then
			if humanoid.FloorMaterial ~= Enum.Material.Air then
				return -- ainda no chão: o Humanoid anda e pula normalmente, a corda só limita a distância
			end
			enterAir()
		end

		local velocity = root.AssemblyLinearVelocity
		local push = horizontal * settings.SwingAcceleration
		if momentumStart and isGrounded() and math.abs(velocity.X) > 0.5 then
			-- Pousou com embalo: desliza e freia aos poucos, em vez de parar seco.
			push -= math.sign(velocity.X) * settings.LandingSlideDecel
		end
		force.Force = Vector3.new(push * root.AssemblyMass, 0, 0)
		if math.abs(velocity.X) > settings.FaceFlipSpeed then
			local newFacing = if velocity.X < 0 then -1 else 1
			if newFacing ~= facing then
				facing = newFacing
				upright.CFrame = facingCFrame(facing)
			end
		end

		-- Limite só na horizontal: a queda continua livre (a gravidade não é cortada).
		local horizontalVelocity = Vector3.new(velocity.X, 0, velocity.Z)
		local limited = HookRules.clampSpeed(horizontalVelocity, settings.MaxSwingSpeed)
		if limited ~= horizontalVelocity then
			root.AssemblyLinearVelocity = Vector3.new(limited.X, velocity.Y, limited.Z)
		end
	end

	function body.takeOff(_self: AirBody)
		if not airborne then
			enterAir() -- assume o corpo mesmo no chão (o puxão tira o personagem do chão)
		end
	end

	function body.setAimPoint(_self: AirBody, target: HookPose.AimTarget?)
		aimTarget = target
		if pose then
			pose:setTarget(target)
		end
	end

	function body.beginMomentum(_self: AirBody)
		momentumStart = os.clock()
		body:setAimPoint(nil) -- soltou: sem corda, o braço volta para trás
	end

	function body.cancelMomentum(_self: AirBody)
		momentumStart = nil
	end

	function body.isMomentumOver(_self: AirBody): boolean
		local start = momentumStart
		if not start then
			return false
		end
		if not airborne then
			return true -- soltou sem ter saído do chão: não há embalo
		end
		if os.clock() - start >= settings.MomentumMaxTime then
			return true
		end
		if not isGrounded() then
			return false -- no ar só o tempo encerra (num puxão quase vertical a velocidade X é ~0)
		end
		-- Pousou: o embalo termina quando o deslize chega à velocidade de andar.
		return math.abs(root.AssemblyLinearVelocity.X) <= humanoid.WalkSpeed
	end

	function body.destroy(_self: AirBody)
		trove:Destroy()
	end

	return body
end

return AirBody
