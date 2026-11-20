--!strict
--[[
	Regras do martelo do DDRace (DDNet `CCharacter::FireWeapon`, WEAPON_HAMMER). Lógica pura: não acessa
	`game`. Tudo no plano XY do jogo (Z ignorado).

	- Hitbox: o próprio martelo. Um segmento do ombro (`PivotHeight` acima do root) até a cabeça do
	  martelo (`Reach` studs na direção da mira); acerta quem tiver o root a até `Radius` dele. Só bate
	  quem está colado no martelo, não à distância.
	- Empurrão (somado à velocidade do alvo): `unit(dir + (0, upBias)) * strength + (0, lift)`, onde
	  `dir` vai de quem bate até o alvo. Como o viés é para cima, bater de baixo joga mais alto que de
	  lado, e o empurrão nunca é para baixo.
]]

export type Settings = {
	PivotHeight: number,
	Reach: number,
	Radius: number,
	Strength: number,
	UpBias: number,
	Lift: number,
}

local EPSILON = 1e-6

local HammerRules = {}

local function flat(vector: Vector3): Vector3
	return Vector3.new(vector.X, vector.Y, 0)
end

-- Direção da mira no plano (unitária). Sem direção válida, para cima.
function HammerRules.aimDirection(origin: Vector3, aimPoint: Vector3): Vector3
	local delta = flat(aimPoint - origin)
	if delta.Magnitude < EPSILON then
		return Vector3.yAxis
	end
	return delta.Unit
end

-- Ombro (onde o martelo gira) e cabeça do martelo no fim da batida.
function HammerRules.segment(origin: Vector3, aimDirection: Vector3, settings: Settings): (Vector3, Vector3)
	local pivot = flat(origin) + Vector3.new(0, settings.PivotHeight, 0)
	return pivot, pivot + flat(aimDirection) * settings.Reach
end

-- Centro da cabeça do martelo no fim da batida (ponto de referência para a checagem de parede).
function HammerRules.hitCenter(origin: Vector3, aimDirection: Vector3, settings: Settings): Vector3
	local _, head = HammerRules.segment(origin, aimDirection, settings)
	return head
end

-- Distância de `point` ao segmento `a`-`b`.
local function distanceToSegment(point: Vector3, a: Vector3, b: Vector3): number
	local ab = b - a
	local lengthSquared = ab:Dot(ab)
	local t = if lengthSquared > EPSILON then math.clamp((point - a):Dot(ab) / lengthSquared, 0, 1) else 0
	return (point - (a + ab * t)).Magnitude
end

-- O martelo de quem está em `origin`, mirando em `aimDirection`, acerta o root em `target`?
-- `tolerance` aumenta o raio (folga do servidor).
function HammerRules.isHit(
	origin: Vector3,
	aimDirection: Vector3,
	target: Vector3,
	settings: Settings,
	tolerance: number?
): boolean
	local pivot, head = HammerRules.segment(origin, aimDirection, settings)
	return distanceToSegment(flat(target), pivot, head) <= settings.Radius + (tolerance or 0)
end

-- Velocidade a somar no alvo (studs/s).
function HammerRules.knockback(origin: Vector3, target: Vector3, settings: Settings): Vector3
	local delta = flat(target - origin)
	local direction = if delta.Magnitude > EPSILON then delta.Unit else Vector3.yAxis
	local push = (direction + Vector3.new(0, settings.UpBias, 0)).Unit * settings.Strength
	return push + Vector3.new(0, settings.Lift, 0)
end

return HammerRules
