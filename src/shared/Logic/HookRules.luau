--!strict
--[[
	Regras puras do gancho, usadas pelo cliente e pelo servidor (RNF-04: sem acesso a `game`).
	RF-12 (gruda em tudo no plano menos roxo), RF-13 (verde uma vez), RF-17 (limite de velocidade),
	RF-18 (corda recolhível); ADR 0016, 0036, 0039, 0042 (puxão).
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

-- Velocidade pedida no puxão (ADR 0042), a `remaining` studs de chegar. Com `braking` (botão ainda
-- apertado, vai ficar preso no ponto), diminui para parar em cima do ponto com desaceleração `accel`;
-- sem frear, segue na velocidade de cruzeiro até chegar. A frenagem não desce de `minSpeed`.
function HookRules.pullSpeed(
	remaining: number,
	cruiseSpeed: number,
	accel: number,
	minSpeed: number,
	braking: boolean
): number
	if not braking then
		return cruiseSpeed
	end
	local brakingSpeed = math.sqrt(2 * accel * math.max(remaining, 0))
	return math.clamp(brakingSpeed, math.min(minSpeed, cruiseSpeed), cruiseSpeed)
end

-- Leva `current` em direção a `target`, mudando no máximo `maxDelta` (aceleração suave).
function HookRules.moveToward(current: Vector3, target: Vector3, maxDelta: number): Vector3
	local delta = target - current
	local size = delta.Magnitude
	if size <= maxDelta or size == 0 then
		return target
	end
	return current + delta * (maxDelta / size)
end

export type DragSettings = {
	accelPerTick: number, -- studs/s somados à velocidade a cada tick
	maxSpeed: number, -- studs/s: acima disso o puxão só pode desviar ou frear
	minDistance: number, -- studs: mais perto que isso não puxa
	downFactor: number, -- multiplica o puxão para baixo (para cima puxa mais)
	assistFactor: number, -- multiplica o X do puxão quando A/D vão no mesmo sentido
	resistFactor: number, -- multiplica o X do puxão nos outros casos
}

-- Puxão do gancho preso, como o HOOK_GRABBED do CCharacterCore do DDNet/Teeworlds. Só soma uma
-- aceleração à velocidade atual (no plano): gravidade, velocidade tangencial e embalo continuam.
-- `ticks`: quantos ticks do DDNet aplicar (fração = um quadro; padrão 1).
-- O puxão não leva a velocidade além de max(`maxSpeed`, velocidade atual): acima do limite ele só
-- curva a trajetória ou freia. (O DDNet descarta o tick inteiro nesse caso; aqui o módulo é limitado
-- para o puxão não ligar e desligar a cada quadro, o que dava trancos no balanço.)
-- `moveDirection`: -1 (A), 0, 1 (D).
function HookRules.hookDrag(
	velocity: Vector3,
	toHook: Vector3,
	moveDirection: number,
	settings: DragSettings,
	ticks: number?
): Vector3
	local planar = Vector3.new(toHook.X, toHook.Y, 0)
	local distance = planar.Magnitude
	if distance <= settings.minDistance then
		return velocity
	end
	local current = Vector3.new(velocity.X, velocity.Y, 0)
	local speed = current.Magnitude
	local strength = settings.accelPerTick * (ticks or 1)
	if speed > settings.maxSpeed then
		-- Acima do limite o gancho curva cada vez menos (no DDNet quase não curva): parábola aberta.
		strength *= (settings.maxSpeed / speed) ^ 2
	end
	local pull = planar * (strength / distance)
	local pullY = if pull.Y < 0 then pull.Y * settings.downFactor else pull.Y
	local assisted = (pull.X < 0 and moveDirection < 0) or (pull.X > 0 and moveDirection > 0)
	local pullX = pull.X * (if assisted then settings.assistFactor else settings.resistFactor)

	local nextVelocity = current + Vector3.new(pullX, pullY, 0)
	local limit = math.max(settings.maxSpeed, speed)
	if nextVelocity.Magnitude > limit then
		nextVelocity = nextVelocity.Unit * limit
	end
	return Vector3.new(nextVelocity.X, nextVelocity.Y, velocity.Z)
end

-- `SaturatedAdd` do DDNet: soma `modifier` sem passar dos limites, mas não corta um valor que já
-- está além do limite no sentido da soma (o embalo acima do controle normal é preservado).
function HookRules.saturatedAdd(min: number, max: number, current: number, modifier: number): number
	if modifier < 0 then
		if current < min then
			return current
		end
		return math.max(current + modifier, min)
	end
	if current > max then
		return current
	end
	return math.min(current + modifier, max)
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
