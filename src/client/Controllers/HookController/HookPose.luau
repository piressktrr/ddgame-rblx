--!strict
--[[
	Pose procedural de "voo" enquanto o gancho puxa o personagem (ADR 0042). Sem asset novo: mexe direto
	nos `Transform` das juntas do rig (R15 ou R6; `Motor6D` ou `AnimationConstraint`).

	- Braço do gancho estendido para o ponto preso (o braço do lado da câmera, para aparecer).
	- O outro braço (ou os dois, sem alvo) vai para trás e para baixo.
	- Corpo inclinado na direção da velocidade (mais rápido = mais inclinado), cabeça compensa um pouco.
	- Pernas para trás, joelhos dobrados, balançando de leve (mais rápido = balança mais).
	- Entra e sai em ~0,15 s (`FADE_TIME`), e cada junta segue a pose com uma mola exponencial.

	Ordem do quadro: o Animator escreve os `Transform` antes de `PreSimulation`; este módulo escreve
	depois, em `PreSimulation`, e por isso não é sobrescrito. Na entrada e na saída mistura com o valor
	que o Animator acabou de escrever (a animação que estiver tocando), então não há tranco.

	Os `Transform` não replicam: só o próprio jogador vê esta pose. Os outros veem a animação que o
	Animator estiver tocando (o `AirBody` mantém a de queda tocando por isso).
]]

local RunService = game:GetService("RunService")

export type AimTarget = Vector3 | Attachment

export type HookPose = {
	-- Ponto (ou Attachment, que acompanha peça que se move) para onde o braço aponta; nil = sem alvo.
	setTarget: (self: HookPose, target: AimTarget?) -> (),
	-- Sai da pose suavemente (~0,15 s) e se desliga sozinho depois.
	destroy: (self: HookPose) -> (),
}

-- Ajustes da pose (só visual, por isso ficam aqui e não no Config).
local FADE_TIME = 0.2 -- segundos para entrar/sair da pose
local POSE_SHARPNESS = 14 -- 1/s: quão rápido cada junta segue a pose (mola exponencial)
local VELOCITY_SHARPNESS = 8 -- 1/s: filtro da velocidade que guia inclinação e pernas
local MIN_SPEED = 1 -- studs/s: abaixo disso não inclina
local FULL_SPEED = 50 -- studs/s: velocidade em que a inclinação e o balanço das pernas chegam ao máximo
local LEAN_MAX_ANGLE = math.rad(50)
local LEAN_ROOT_SHARE = 0.7 -- R15: parte da inclinação no quadril (Root); o resto vai para a cintura
local NECK_COUNTER = 0.45 -- quanto a cabeça desfaz a inclinação (olhar para frente)
local LEG_BACK_MIN = math.rad(12) -- pernas para trás, parado
local LEG_BACK_MAX = math.rad(30) -- pernas para trás, rápido
local LEG_SPREAD = 0.08 -- abertura lateral das pernas
local LEG_SWING_ANGLE = math.rad(10)
local LEG_SWING_FREQ = 5 -- rad/s parado
local LEG_SWING_FREQ_PER_SPEED = 0.08 -- rad/s a mais por stud/s
local KNEE_BEND = math.rad(35)
local ANKLE_POINT = math.rad(30) -- ponta do pé para baixo
local FREE_ARM_DIRECTION = Vector3.new(0.35, -0.7, 0.6) -- braço livre no espaço do tronco (X troca de sinal)
local FREE_ARM_SWAY = 0.08
local AIM_ELBOW_BEND = math.rad(6)
local FREE_ELBOW_BEND = math.rad(25)

local DOWN = Vector3.new(0, -1, 0)
local UP = Vector3.new(0, 1, 0)
local IDENTITY = CFrame.new()

-- Junta do rig: `Motor6D` (clássico) ou `AnimationConstraint` (juntas novas do avatar, que o Studio já
-- usa). Nos dois, Part1 * C1 = Part0 * C0 * Transform; no constraint, C0/C1 são os CFrame dos attachments.
type Joint = {
	instance: Motor6D | AnimationConstraint,
	motor: Motor6D?,
	constraint: AnimationConstraint?,
	c0: CFrame,
	c1: CFrame,
	base: CFrame, -- último valor escrito pelo Animator
	written: CFrame?, -- último valor escrito por este módulo
	current: CFrame, -- pose suavizada (sem mistura com a animação)
}

type Rig = {
	isR15: boolean,
	root: Joint,
	waist: Joint?,
	neck: Joint?,
	shoulderR: Joint,
	shoulderL: Joint,
	elbowR: Joint?,
	elbowL: Joint?,
	wristR: Joint?,
	wristL: Joint?,
	hipR: Joint,
	hipL: Joint,
	kneeR: Joint?,
	kneeL: Joint?,
	ankleR: Joint?,
	ankleL: Joint?,
}

local HookPose = {}

local function findJoint(character: Model, partName: string, jointName: string): Joint?
	local part = character:FindFirstChild(partName)
	local found = part and part:FindFirstChild(jointName)
	if found and found:IsA("Motor6D") then
		local transform = found.Transform
		return {
			instance = found,
			motor = found,
			constraint = nil,
			c0 = found.C0,
			c1 = found.C1,
			base = transform,
			written = nil,
			current = transform,
		}
	end
	if found and found:IsA("AnimationConstraint") then
		local attachment0, attachment1 = found.Attachment0, found.Attachment1
		if not (attachment0 and attachment1) then
			return nil
		end
		local transform = found.Transform
		return {
			instance = found,
			motor = nil,
			constraint = found,
			c0 = attachment0.CFrame,
			c1 = attachment1.CFrame,
			base = transform,
			written = nil,
			current = transform,
		}
	end
	return nil
end

local function readTransform(joint: Joint): CFrame
	local motor, constraint = joint.motor, joint.constraint
	if motor then
		return motor.Transform
	elseif constraint then
		return constraint.Transform
	end
	return CFrame.identity
end

local function writeTransform(joint: Joint, transform: CFrame)
	local motor, constraint = joint.motor, joint.constraint
	if motor then
		motor.Transform = transform
	elseif constraint then
		constraint.Transform = transform
	end
end

local function buildRig(character: Model, humanoid: Humanoid): Rig?
	if humanoid.RigType == Enum.HumanoidRigType.R15 then
		local root = findJoint(character, "LowerTorso", "Root")
		local shoulderR = findJoint(character, "RightUpperArm", "RightShoulder")
		local shoulderL = findJoint(character, "LeftUpperArm", "LeftShoulder")
		local hipR = findJoint(character, "RightUpperLeg", "RightHip")
		local hipL = findJoint(character, "LeftUpperLeg", "LeftHip")
		if not (root and shoulderR and shoulderL and hipR and hipL) then
			return nil
		end
		return {
			isR15 = true,
			root = root,
			waist = findJoint(character, "UpperTorso", "Waist"),
			neck = findJoint(character, "Head", "Neck"),
			shoulderR = shoulderR,
			shoulderL = shoulderL,
			elbowR = findJoint(character, "RightLowerArm", "RightElbow"),
			elbowL = findJoint(character, "LeftLowerArm", "LeftElbow"),
			wristR = findJoint(character, "RightHand", "RightWrist"),
			wristL = findJoint(character, "LeftHand", "LeftWrist"),
			hipR = hipR,
			hipL = hipL,
			kneeR = findJoint(character, "RightLowerLeg", "RightKnee"),
			kneeL = findJoint(character, "LeftLowerLeg", "LeftKnee"),
			ankleR = findJoint(character, "RightFoot", "RightAnkle"),
			ankleL = findJoint(character, "LeftFoot", "LeftAnkle"),
		}
	end

	local root = findJoint(character, "HumanoidRootPart", "RootJoint")
	local shoulderR = findJoint(character, "Torso", "Right Shoulder")
	local shoulderL = findJoint(character, "Torso", "Left Shoulder")
	local hipR = findJoint(character, "Torso", "Right Hip")
	local hipL = findJoint(character, "Torso", "Left Hip")
	if not (root and shoulderR and shoulderL and hipR and hipL) then
		return nil
	end
	return {
		isR15 = false,
		root = root,
		neck = findJoint(character, "Torso", "Neck"),
		shoulderR = shoulderR,
		shoulderL = shoulderL,
		hipR = hipR,
		hipL = hipL,
	}
end

local function allJoints(rig: Rig): { Joint }
	local list = { rig.root, rig.shoulderR, rig.shoulderL, rig.hipR, rig.hipL }
	local function add(joint: Joint?)
		if joint then
			table.insert(list, joint)
		end
	end
	add(rig.waist)
	add(rig.neck)
	add(rig.elbowR)
	add(rig.elbowL)
	add(rig.wristR)
	add(rig.wristL)
	add(rig.kneeR)
	add(rig.kneeL)
	add(rig.ankleR)
	add(rig.ankleL)
	return list
end

local function nearlyEqual(a: CFrame, b: CFrame): boolean
	return a.Position:FuzzyEq(b.Position, 1e-4)
		and a.LookVector:FuzzyEq(b.LookVector, 1e-4)
		and a.UpVector:FuzzyEq(b.UpVector, 1e-4)
end

-- Rotação mínima que leva o vetor unitário `from` até `to`.
local function rotationBetween(from: Vector3, to: Vector3): CFrame
	local dot = math.clamp(from:Dot(to), -1, 1)
	if dot > 0.9999 then
		return CFrame.identity
	end
	if dot < -0.9999 then
		local axis = from:Cross(Vector3.xAxis)
		if axis.Magnitude < 1e-3 then
			axis = from:Cross(Vector3.zAxis)
		end
		return CFrame.fromAxisAngle(axis.Unit, math.pi)
	end
	return CFrame.fromAxisAngle(from:Cross(to).Unit, math.acos(dot))
end

-- Rotação expressa no espaço da Part0 -> `Transform` (que é expresso no espaço do C0).
local function toTransform(joint: Joint, rotationInPart0: CFrame): CFrame
	local c0 = joint.c0.Rotation
	return c0:Inverse() * rotationInPart0 * c0
end

-- `Transform` que faz o membro (o -Y da Part1) apontar para `direction`, dado no espaço da Part0.
local function aimTransform(joint: Joint, direction: Vector3): CFrame
	if direction.Magnitude < 1e-4 then
		return CFrame.identity
	end
	local inJoint = joint.c0:VectorToObjectSpace(direction).Unit
	local rest = joint.c1:Inverse():VectorToWorldSpace(DOWN)
	return rotationBetween(rest, inJoint)
end

-- CFrame da Part1 a partir da Part0, com um `Transform` dado.
local function childCFrame(part0: CFrame, joint: Joint, transform: CFrame): CFrame
	return part0 * joint.c0 * transform * joint.c1:Inverse()
end

local function smoothstep(x: number): number
	return x * x * (3 - 2 * x)
end

local function bendX(angle: number): CFrame
	return CFrame.Angles(angle, 0, 0)
end

function HookPose.new(character: Model, humanoid: Humanoid): HookPose
	local pose = {} :: HookPose
	local rootPart = humanoid.RootPart
	local maybeRig = if rootPart then buildRig(character, humanoid) else nil
	if not (maybeRig and rootPart) then
		-- Rig desconhecido: pose sem efeito (o personagem só fica com a animação que estiver tocando).
		function pose.setTarget(_self: HookPose, _target: AimTarget?) end
		function pose.destroy(_self: HookPose) end
		return pose
	end
	local rig: Rig = maybeRig
	local root: BasePart = rootPart
	local joints = allJoints(rig)

	local target: AimTarget? = nil
	local aimRight = true
	local alpha = 0
	local goalAlpha = 1
	local phase = 0
	local elapsed = 0
	local smoothedVelocity: Vector3? = nil
	local connection: RBXScriptConnection? = nil

	local function stop()
		if connection then
			connection:Disconnect()
			connection = nil
		end
	end

	local function targetPosition(): Vector3?
		local current = target
		if current == nil then
			return nil
		end
		if typeof(current) == "Vector3" then
			return current
		end
		local attachment = current :: Attachment
		return if attachment.Parent then attachment.WorldPosition else nil
	end

	-- Braço do gancho: o do lado da câmera (no 2.5D o alvo fica quase sempre no plano do personagem).
	local function chooseAimArm()
		local camera = workspace.CurrentCamera
		local right = root.CFrame.RightVector
		local side = 0
		if camera then
			side = (camera.CFrame.Position - root.Position):Dot(right)
		end
		local point = targetPosition()
		if math.abs(side) < 0.5 and point then
			side = (point - root.Position):Dot(right)
		end
		aimRight = side >= 0
	end

	-- Escreve a pose de uma junta e devolve o `Transform` final (para a cadeia do tronco).
	local function apply(joint: Joint, goal: CFrame, follow: number, blend: number): CFrame
		joint.current = joint.current:Lerp(goal, follow)
		local final = joint.base:Lerp(joint.current, blend)
		writeTransform(joint, final)
		joint.written = final
		return final
	end

	local function leanRotation(localVelocity: Vector3, speed: number): CFrame
		if speed < MIN_SPEED then
			return CFrame.identity
		end
		local direction = localVelocity / speed
		local axis = UP:Cross(direction)
		local sine = axis.Magnitude
		if sine < 1e-3 then
			return CFrame.identity -- subindo ou caindo reto: fica em pé
		end
		-- Inclina pela parte horizontal do movimento: vai a 0 aos poucos perto da vertical (subindo ou
		-- caindo), sem o salto de 50° para 0° de quando a queda ficava exatamente reta.
		local angle = math.min(math.asin(math.min(sine, 1)), LEAN_MAX_ANGLE)
		return CFrame.fromAxisAngle(axis / sine, angle * math.clamp(speed / FULL_SPEED, 0, 1))
	end

	local function onStep(dt: number)
		if not character.Parent or not root.Parent or humanoid.Health <= 0 then
			stop()
			return
		end

		alpha = if goalAlpha > alpha
			then math.min(goalAlpha, alpha + dt / FADE_TIME)
			else math.max(goalAlpha, alpha - dt / FADE_TIME)

		-- O que o Animator escreveu neste quadro vira a base da mistura. Se ele não mexeu na junta
		-- (o valor ainda é o nosso), a base anterior continua.
		for _, joint in joints do
			if joint.instance.Parent then
				local transform = readTransform(joint)
				local written = joint.written
				if not (written and nearlyEqual(transform, written)) then
					joint.base = transform
				end
			end
		end

		if alpha <= 0 and goalAlpha <= 0 then
			for _, joint in joints do
				if joint.instance.Parent then
					writeTransform(joint, joint.base)
				end
			end
			stop()
			return
		end

		local blend = smoothstep(alpha)
		local follow = 1 - math.exp(-POSE_SHARPNESS * dt)
		elapsed += dt

		local rootCFrame = root.CFrame
		-- Velocidade filtrada: a pose acompanha a tendência do movimento, não cada puxão do gancho.
		local rawVelocity = root.AssemblyLinearVelocity
		smoothedVelocity = if smoothedVelocity
			then smoothedVelocity:Lerp(rawVelocity, 1 - math.exp(-VELOCITY_SHARPNESS * dt))
			else rawVelocity
		local velocity = smoothedVelocity :: Vector3
		local localVelocity = rootCFrame:VectorToObjectSpace(velocity)
		local speed = localVelocity.Magnitude
		local speedFactor = math.clamp(speed / FULL_SPEED, 0, 1)
		local lean = leanRotation(localVelocity, speed)

		-- Tronco: inclinação dividida entre quadril e cintura (R15) ou toda no RootJoint (R6).
		local waist = rig.waist
		local rootShare = if waist then LEAN_ROOT_SHARE else 1
		local rootTransform =
			apply(rig.root, toTransform(rig.root, IDENTITY:Lerp(lean, rootShare)), follow, blend)
		local lowerTorso = childCFrame(rootCFrame, rig.root, rootTransform)
		local upperTorso = lowerTorso
		if waist then
			local waistTransform =
				apply(waist, toTransform(waist, IDENTITY:Lerp(lean, 1 - rootShare)), follow, blend)
			upperTorso = childCFrame(lowerTorso, waist, waistTransform)
		end
		local neck = rig.neck
		if neck then
			apply(neck, toTransform(neck, IDENTITY:Lerp(lean:Inverse(), NECK_COUNTER)), follow, blend)
		end

		-- Braços.
		local point = targetPosition()
		local sway = math.sin(elapsed * 3) * FREE_ARM_SWAY
		local function armGoal(shoulder: Joint, sign: number, aiming: boolean): CFrame
			if aiming and point then
				local shoulderWorld = upperTorso * shoulder.c0
				local toPoint = upperTorso:VectorToObjectSpace(point - shoulderWorld.Position)
				return aimTransform(shoulder, toPoint)
			end
			local free = FREE_ARM_DIRECTION
			return aimTransform(shoulder, Vector3.new(free.X * sign, free.Y + sway * sign, free.Z))
		end
		local aimingRight = aimRight and point ~= nil
		local aimingLeft = not aimRight and point ~= nil
		apply(rig.shoulderR, armGoal(rig.shoulderR, 1, aimingRight), follow, blend)
		apply(rig.shoulderL, armGoal(rig.shoulderL, -1, aimingLeft), follow, blend)
		local elbowR, elbowL = rig.elbowR, rig.elbowL
		if elbowR then
			local bend = if aimingRight then AIM_ELBOW_BEND else FREE_ELBOW_BEND
			apply(elbowR, toTransform(elbowR, bendX(bend)), follow, blend)
		end
		if elbowL then
			local bend = if aimingLeft then AIM_ELBOW_BEND else FREE_ELBOW_BEND
			apply(elbowL, toTransform(elbowL, bendX(bend)), follow, blend)
		end
		local wristR, wristL = rig.wristR, rig.wristL
		if wristR then
			apply(wristR, CFrame.identity, follow, blend)
		end
		if wristL then
			apply(wristL, CFrame.identity, follow, blend)
		end

		-- Pernas: para trás, joelhos dobrados, balanço alternado (no espaço do tronco de baixo).
		phase += dt * (LEG_SWING_FREQ + speed * LEG_SWING_FREQ_PER_SPEED)
		local back = LEG_BACK_MIN + (LEG_BACK_MAX - LEG_BACK_MIN) * speedFactor
		local amplitude = LEG_SWING_ANGLE * (0.4 + 0.6 * speedFactor)
		local function legGoal(hip: Joint, sign: number, swing: number): CFrame
			local angle = back + swing
			return aimTransform(hip, Vector3.new(LEG_SPREAD * sign, -math.cos(angle), math.sin(angle)))
		end
		local swingR = math.sin(phase) * amplitude
		local swingL = -swingR
		apply(rig.hipR, legGoal(rig.hipR, 1, swingR), follow, blend)
		apply(rig.hipL, legGoal(rig.hipL, -1, swingL), follow, blend)
		local kneeR, kneeL = rig.kneeR, rig.kneeL
		if kneeR then
			apply(kneeR, toTransform(kneeR, bendX(-(KNEE_BEND + swingR))), follow, blend)
		end
		if kneeL then
			apply(kneeL, toTransform(kneeL, bendX(-(KNEE_BEND + swingL))), follow, blend)
		end
		local ankleR, ankleL = rig.ankleR, rig.ankleL
		if ankleR then
			apply(ankleR, toTransform(ankleR, bendX(-ANKLE_POINT)), follow, blend)
		end
		if ankleL then
			apply(ankleL, toTransform(ankleL, bendX(-ANKLE_POINT)), follow, blend)
		end
	end

	connection = RunService.PreSimulation:Connect(onStep)

	function pose.setTarget(_self: HookPose, newTarget: AimTarget?)
		target = newTarget
		if newTarget then
			chooseAimArm()
		end
	end

	function pose.destroy(_self: HookPose)
		goalAlpha = 0
		if alpha <= 0 then
			stop()
		end
	end

	return pose
end

return HookPose
