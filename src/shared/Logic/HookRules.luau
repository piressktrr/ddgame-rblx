--!strict
--[[
	Regras puras do gancho, usadas pelo cliente e pelo servidor (RNF-04: sem acesso a `game`).
	RF-12 (gruda em tudo no plano menos roxo), RF-13 (verde uma vez), RF-17 (limite de velocidade),
	RF-18 (corda recolhível); ADR 0016, 0036, 0039.
]]

export type SurfaceKind = "Normal" | "NoHook" | "HookOnce"

-- Estado do alvo sob a mira: nada para prender, pode prender, ou superfície proibida
-- (roxo ou verde já usado).
export type TargetState = "None" | "Valid" | "Forbidden"

export type RopeLimits = {
	minLength: number,
	maxLength: number,
	reelInSpeed: number, -- studs/s
	reelOutSpeed: number, -- studs/s
	maxLead: number, -- studs que o comprimento pode ficar abaixo da distância real ao recolher
}

local HookRules = {}

-- Tipo da superfície a partir das tags. Roxo (`NoHook`) vence se a peça tiver as duas.
function HookRules.surfaceKind(hasNoHookTag: boolean, hasHookOnceTag: boolean): SurfaceKind
	if hasNoHookTag then
		return "NoHook"
	end
	if hasHookOnceTag then
		return "HookOnce"
	end
	return "Normal"
end

-- Pode prender? Roxo nunca; verde só se este jogador ainda não usou.
function HookRules.canAttach(kind: SurfaceKind, hookOnceUsed: boolean): boolean
	if kind == "NoHook" then
		return false
	end
	if kind == "HookOnce" then
		return not hookOnceUsed
	end
	return true
end

-- O ponto está dentro (ou na superfície) da caixa da peça, com folga? Serve para dizer se o
-- ponto levado ao plano ainda está na peça: peça de cenário fora da profundidade do plano falha.
function HookRules.pointOnPart(cframe: CFrame, size: Vector3, point: Vector3, tolerance: number): boolean
	local localPoint = cframe:PointToObjectSpace(point)
	return math.abs(localPoint.X) <= size.X / 2 + tolerance
		and math.abs(localPoint.Y) <= size.Y / 2 + tolerance
		and math.abs(localPoint.Z) <= size.Z / 2 + tolerance
end

function HookRules.isWithinRange(origin: Vector3, point: Vector3, maxDistance: number): boolean
	return (point - origin).Magnitude <= maxDistance
end

function HookRules.cooldownReady(lastTime: number, now: number, cooldown: number): boolean
	return now - lastTime >= cooldown
end

-- Próximo comprimento da corda. `reel` < 0 recolhe (W), > 0 solta (S), 0 mantém.
-- Ao recolher, o comprimento não passa de `maxLead` abaixo da distância real: se uma parede segura o
-- personagem, a corda para de encurtar em vez de forçá-lo através dela.
function HookRules.nextRopeLength(
	current: number,
	reel: number,
	dt: number,
	distance: number,
	limits: RopeLimits
): number
	local nextLength = current
	if reel < 0 then
		nextLength = current + reel * limits.reelInSpeed * dt
		nextLength = math.min(current, math.max(nextLength, distance - limits.maxLead))
	elseif reel > 0 then
		nextLength = current + reel * limits.reelOutSpeed * dt
	end
	return math.clamp(nextLength, limits.minLength, limits.maxLength)
end

-- Comprimento inicial: a distância na hora de prender, dentro dos limites.
function HookRules.initialRopeLength(distance: number, limits: RopeLimits): number
	return math.clamp(distance, limits.minLength, limits.maxLength)
end

-- Limita o módulo da velocidade, mantendo a direção.
function HookRules.clampSpeed(velocity: Vector3, maxSpeed: number): Vector3
	local speed = velocity.Magnitude
	if speed <= maxSpeed then
		return velocity
	end
	return velocity * (maxSpeed / speed)
end

function HookRules.isFiniteNumber(value: number): boolean
	return value == value and math.abs(value) ~= math.huge
end

function HookRules.isFiniteVector(value: Vector3): boolean
	return HookRules.isFiniteNumber(value.X)
		and HookRules.isFiniteNumber(value.Y)
		and HookRules.isFiniteNumber(value.Z)
end

return HookRules
