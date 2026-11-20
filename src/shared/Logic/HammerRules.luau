--!strict
--[[
	Regras do martelo do DDRace (DDNet `CCharacter::FireWeapon`, WEAPON_HAMMER). Lógica pura: não acessa
	`game`. Tudo no plano XY do jogo (Z ignorado).

	- Hitbox: círculo de raio `radius` com centro a `reach` studs do root de quem bate, na direção da
	  mira. Acerta quem tiver o root dentro.
	- Empurrão (somado à velocidade do alvo): `unit(dir + (0, upBias)) * strength + (0, lift)`, onde
	  `dir` vai de quem bate até o alvo. Como o viés é para cima, bater de baixo joga mais alto que de
	  lado, e o empurrão nunca é para baixo.
]]

export type Settings = {
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

-- Centro do círculo de acerto.
function HammerRules.hitCenter(origin: Vector3, aimDirection: Vector3, settings: Settings): Vector3
	return flat(origin) + flat(aimDirection) * settings.Reach
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
	local center = HammerRules.hitCenter(origin, aimDirection, settings)
	return (flat(target) - center).Magnitude <= settings.Radius + (tolerance or 0)
end

-- Velocidade a somar no alvo (studs/s).
function HammerRules.knockback(origin: Vector3, target: Vector3, settings: Settings): Vector3
	local delta = flat(target - origin)
	local direction = if delta.Magnitude > EPSILON then delta.Unit else Vector3.yAxis
	local push = (direction + Vector3.new(0, settings.UpBias, 0)).Unit * settings.Strength
	return push + Vector3.new(0, settings.Lift, 0)
end

return HammerRules
