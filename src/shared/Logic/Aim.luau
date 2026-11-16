--!strict
--[[
	Mira do gancho no plano 2.5D (RF-10, ADR 0039). Lógica pura: não acessa `game`.

	O cursor vira um ponto do plano (raio da câmera cruzando Z = plano); o gancho sai do
	HumanoidRootPart na direção desse ponto, em 360°, e o alcance conta a partir do root.
]]

local EPSILON = 1e-6

local Aim = {}

-- Leva um ponto para o plano do jogo (mesmo X e Y, Z do plano).
function Aim.toPlane(point: Vector3, planeZ: number): Vector3
	return Vector3.new(point.X, point.Y, planeZ)
end

-- Onde o raio `origin + t * direction` (t >= 0) cruza o plano Z = planeZ. nil se o raio for
-- paralelo ao plano ou apontar para longe dele.
function Aim.intersectPlane(origin: Vector3, direction: Vector3, planeZ: number): Vector3?
	if math.abs(direction.Z) < EPSILON then
		return nil
	end
	local t = (planeZ - origin.Z) / direction.Z
	if t < 0 then
		return nil
	end
	return Aim.toPlane(origin + direction * t, planeZ)
end

-- Direção unitária, no plano (Z = 0), de `from` até `target`. nil se forem o mesmo ponto em X/Y.
function Aim.planarDirection(from: Vector3, target: Vector3): Vector3?
	local delta = Vector3.new(target.X - from.X, target.Y - from.Y, 0)
	if delta.Magnitude < EPSILON then
		return nil
	end
	return delta.Unit
end

-- Limita o ponto mirado ao alcance, na mesma direção (cursor além do alcance, ADR 0039).
-- Os dois pontos devem estar no plano.
function Aim.clampToRange(from: Vector3, target: Vector3, range: number): Vector3
	local delta = target - from
	if delta.Magnitude <= range then
		return target
	end
	return from + delta.Unit * range
end

-- Vetor do lançamento: da origem, na direção do ponto mirado, com o comprimento do alcance.
-- O gancho sempre vai até o alcance máximo na direção do cursor (o cursor só dá a direção).
function Aim.castVector(from: Vector3, target: Vector3, range: number): Vector3?
	local direction = Aim.planarDirection(from, target)
	if not direction then
		return nil
	end
	return direction * range
end

return Aim
