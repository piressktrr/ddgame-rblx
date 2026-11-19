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
-- Regra do DDNet: o puxão vale se a nova velocidade ficar abaixo de `maxSpeed` ou for menor que a
-- atual; senão é descartado (acima do limite o gancho só freia, não curva). Única diferença: se o
-- puxão inteiro passaria do limite vindo de baixo, aplica só a parte que chega nele (o descarte do
-- tick inteiro ligava e desligava o puxão a cada quadro e dava trancos).
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
	local pull = planar * (settings.accelPerTick * (ticks or 1) / distance)
	local pullY = if pull.Y < 0 then pull.Y * settings.downFactor else pull.Y
	local assisted = (pull.X < 0 and moveDirection < 0) or (pull.X > 0 and moveDirection > 0)
	pull = Vector3.new(pull.X * (if assisted then settings.assistFactor else settings.resistFactor), pullY, 0)

	local nextVelocity = current + pull
	local nextSpeed = nextVelocity.Magnitude
	if nextSpeed > settings.maxSpeed and nextSpeed >= speed then
		if speed >= settings.maxSpeed then
			return velocity -- acima do limite e o puxão aceleraria: descartado (DDNet)
		end
		-- Vindo de baixo: só a fração t do puxão que leva a velocidade exatamente ao limite
		-- (|current + t * pull| = maxSpeed).
		local a = pull:Dot(pull)
		local b = 2 * current:Dot(pull)
		local c = speed * speed - settings.maxSpeed * settings.maxSpeed
		local t = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
		nextVelocity = current + pull * math.clamp(t, 0, 1)
	end
	return Vector3.new(nextVelocity.X, nextVelocity.Y, velocity.Z)
end

export type PlayerPullSettings = {
	accelPerTick: number, -- studs/s por tick no alcance máximo (DragAccel do gancho)
	range: number, -- studs: alcance do gancho (o puxão cresce com a distância / alcance)
	maxSpeed: number, -- studs/s: limite por eixo (SaturatedAdd), como o DragSpeed
	minDistance: number, -- studs: mais perto que isso não puxa (o puxado não chega ao centro)
}

-- Gancho em jogador, como o DDNet (CCharacterCore, `m_HookedPlayer`): a cada tick, quem é puxado
-- recebe `factor` 1,5 e quem puxa 0,25 da aceleração, cada um na direção do outro. A aceleração
-- cresce com a distância (distância / alcance) e cada eixo usa o SaturatedAdd (não corta embalo).
-- `velocity` é de quem recebe; `from` a posição dele; `to` a posição do outro.
function HookRules.playerPull(
	velocity: Vector3,
	from: Vector3,
	to: Vector3,
	factor: number,
	settings: PlayerPullSettings,
	ticks: number?
): Vector3
	local delta = Vector3.new(to.X - from.X, to.Y - from.Y, 0)
	local distance = delta.Magnitude
	if distance <= settings.minDistance then
		return velocity
	end
	local direction = delta / distance
	local accel = settings.accelPerTick * (ticks or 1) * (distance / settings.range) * factor
	local limit = settings.maxSpeed
	return Vector3.new(
		HookRules.saturatedAdd(-limit, limit, velocity.X, accel * direction.X),
		HookRules.saturatedAdd(-limit, limit, velocity.Y, accel * direction.Y),
		velocity.Z
	)
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
