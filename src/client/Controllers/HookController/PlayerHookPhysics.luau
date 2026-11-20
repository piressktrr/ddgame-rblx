--!strict
--[[
	Gancho preso em OUTRO jogador, lado de quem puxa (DDNet: `m_HookedPlayer`). Quem é puxado aplica a
	parte dele no próprio cliente (HookController lê `Config.Attributes.HookTarget` nos outros).

	- Não puxa o próprio personagem até um ponto (como no DDNet): só recebe 0,25x do puxão, na direção
	  do puxado (`HookRules.playerPull`).
	- Solta ao soltar o botão, depois de `PlayerHookDuration`, se o alvo morrer, sair, entrar em solo
	  ou ficar longe demais.
	- Corda até o root do alvo (Attachment local, que acompanha o alvo).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Trove = require(ReplicatedStorage.Packages.Trove)

local HookPhysics = require(script.Parent.HookPhysics)

local settings = Config.Hook
local TICK = 1 / settings.TickRate
local MAX_TICKS_PER_FRAME = 4
local RELEASE_DISTANCE = settings.Range * 1.5 -- studs: alvo levado longe demais (ex.: teleporte)

local PULL: HookRules.PlayerPullSettings = table.freeze({
	accelPerTick = settings.DragAccel * TICK,
	range = settings.PlayerPullLength,
	maxSpeed = settings.DragSpeed,
	minDistance = settings.PlayerPullMinDistance,
})

local PlayerHookPhysics = {}

PlayerHookPhysics.PULL = PULL

export type Params = HookPhysics.Params & { target: Player }

function PlayerHookPhysics.new(params: Params): HookPhysics.Physics
	local root = params.root
	local anchor = params.anchor
	local target = params.target
	local trove = Trove.new()
	trove:Add(HookPhysics.createRope(params.rootAttachment, anchor, root))
	local elapsed = 0

	local function targetRoot(): BasePart?
		local character = target.Character
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		local targetRootPart = character and character:FindFirstChild("HumanoidRootPart")
		if
			not target.Parent
			or not humanoid
			or humanoid.Health <= 0
			or not targetRootPart
			or not targetRootPart:IsA("BasePart")
			or character:GetAttribute(Config.Attributes.Solo) == true
		then
			return nil
		end
		return targetRootPart
	end

	local physics = {} :: HookPhysics.Physics

	function physics.step(
		_self: HookPhysics.Physics,
		dt: number,
		input: HookPhysics.Input
	): HookPhysics.StepResult
		elapsed += dt
		local other = targetRoot()
		if not input.held or elapsed >= settings.PlayerHookDuration or not other or not anchor.Parent then
			return "Release"
		end
		if (other.Position - root.Position).Magnitude > RELEASE_DISTANCE then
			return "Release"
		end
		local ticks = math.min(dt / TICK, MAX_TICKS_PER_FRAME)
		local velocity = root.AssemblyLinearVelocity
		local pulled = HookRules.playerPull(
			velocity,
			root.Position,
			other.Position,
			settings.PlayerPullHookerFactor,
			PULL,
			ticks
		)
		if pulled ~= velocity then
			root.AssemblyLinearVelocity = pulled
		end
		params.body:step(dt, input.horizontal)
		return "Continue"
	end

	function physics.getLength(_self: HookPhysics.Physics): number
		local other = targetRoot()
		return if other then (other.Position - root.Position).Magnitude else 0
	end

	function physics.getPhase(_self: HookPhysics.Physics): string
		return `Player:{target.Name}`
	end

	function physics.destroy(_self: HookPhysics.Physics)
		trove:Destroy()
	end

	return physics
end

-- Jogador dono do personagem a que a peça pertence (acessórios incluídos), ou nil.
function PlayerHookPhysics.playerFromPart(part: Instance): Player?
	local model = part:FindFirstAncestorOfClass("Model")
	while model do
		local owner = Players:GetPlayerFromCharacter(model)
		if owner then
			return owner
		end
		model = model:FindFirstAncestorOfClass("Model")
	end
	return nil
end

return PlayerHookPhysics
