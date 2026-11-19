--!strict
--[[
	Física do gancho tipo C, DDNet (padrão): o HOOK_GRABBED do CCharacterCore do DDNet/Teeworlds.

	- Em ticks fixos (`Config.Hook.TickRate`, independente do FPS) soma à velocidade do root uma
	  aceleração na direção do ponto (`HookRules.hookDrag`). Não há corda rígida nem velocidade imposta:
	  a gravidade do Roblox continua agindo, a velocidade tangencial fica e o embalo se acumula.
	- O puxão só acelera até `DragSpeed`; acima disso só pode desviar ou frear. É isso que dá o balanço
	  e o ganho de impulso do DDNet.
	- Para cima puxa mais que para baixo (`DragDownFactor`); A/D no sentido do puxão o reforçam.
	- Segurar o botão mantém preso; soltar solta na hora e o embalo segue no `AirBody`.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookPhysics = require(script.Parent.HookPhysics)

local settings = Config.Hook
local TICK = 1 / settings.TickRate
local MAX_TICKS_PER_FRAME = 4 -- quadro muito longo não vira uma rajada de puxões

local DRAG: HookRules.DragSettings = table.freeze({
	accelPerTick = settings.DragAccel * TICK,
	maxSpeed = settings.DragSpeed,
	minDistance = settings.DragMinDistance,
	downFactor = settings.DragDownFactor,
	assistFactor = settings.DragAssistFactor,
	resistFactor = settings.DragResistFactor,
})

local DDNetPhysics = {}

function DDNetPhysics.new(params: HookPhysics.Params): HookPhysics.Physics
	local root = params.root
	local anchor = params.anchor
	local body = params.body
	local trove = Trove.new()
	trove:Add(HookPhysics.createRope(params.rootAttachment, anchor, root))

	-- No chão o Humanoid (estado Running) anula o puxão: o AirBody assume se o ponto não estiver
	-- muito para baixo (mesma regra do puxão, ADR 0042).
	local humanoid = params.character:FindFirstChildOfClass("Humanoid")
	local toAnchor = anchor.WorldPosition - root.Position
	if
		humanoid
		and humanoid.FloorMaterial ~= Enum.Material.Air
		and toAnchor.Magnitude > 0
		and toAnchor.Unit.Y > settings.PullTakeOffMinUp
	then
		body:takeOff()
	end

	local accumulator = 0
	local physics = {} :: HookPhysics.Physics

	function physics.step(
		_self: HookPhysics.Physics,
		dt: number,
		input: HookPhysics.Input
	): HookPhysics.StepResult
		if not input.held then
			return "Release"
		end
		accumulator = math.min(accumulator + dt, TICK * MAX_TICKS_PER_FRAME)
		local velocity = root.AssemblyLinearVelocity
		local pulled = velocity
		while accumulator >= TICK do
			accumulator -= TICK
			pulled = HookRules.hookDrag(pulled, anchor.WorldPosition - root.Position, input.horizontal, DRAG)
		end
		if pulled ~= velocity then
			root.AssemblyLinearVelocity = pulled
		end
		body:step(dt, input.horizontal)
		return "Continue"
	end

	function physics.getLength(_self: HookPhysics.Physics): number
		local delta = anchor.WorldPosition - root.Position
		return Vector3.new(delta.X, delta.Y, 0).Magnitude
	end

	function physics.getPhase(_self: HookPhysics.Physics): string
		return "Grabbed"
	end

	function physics.destroy(_self: HookPhysics.Physics)
		trove:Destroy()
	end

	return physics
end

DDNetPhysics.mode = table.freeze({
	new = DDNetPhysics.new,
	releaseOnButtonUp = true,
	retargetWhileAttached = false,
	usesReel = false,
}) :: HookPhysics.Mode

return DDNetPhysics
