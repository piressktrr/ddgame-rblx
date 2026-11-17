--!strict
--[[
	Movimento base do jogador local (RF-03, ADR 0043).

	- Velocidade de andar `Config.Movement.WalkSpeed`, aplicada a cada personagem novo.
	- Pulo duplo: um segundo pulo no ar (Espaço de novo), uma vez até tocar o chão ou prender o gancho.
	  A queda é zerada e a velocidade vertical vira `DoubleJumpVelocity`; X fica como estava e Z em 0
	  (a trava do plano continua no CharacterController).
	- Com a corda presa, o pulo duplo não dispara. No embalo (corda já solta) ele vale e mantém o
	  embalo horizontal (Q42). O
	  HookController avisa pelo atributo local `Config.Movement.HookActiveAttribute` no personagem;
	  quando ele liga (prendeu), a carga volta.
	- Regras puras em `Shared.Logic.DoubleJump`.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Config = require(ReplicatedStorage.Shared.Config)
local DoubleJump = require(ReplicatedStorage.Shared.Logic.DoubleJump)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local HookController = require(script.Parent.HookController)

local settings = Config.Movement
local planeZ = Config.Plane.Z
local player = Players.LocalPlayer

local RULES: DoubleJump.Settings = table.freeze({
	minAirTime = settings.DoubleJumpMinAirTime,
	repeatGap = settings.JumpRequestRepeatGap,
})

-- Estados em que o Humanoid está no ar por conta própria.
local AIR_STATES: { [Enum.HumanoidStateType]: boolean } = {
	[Enum.HumanoidStateType.Jumping] = true,
	[Enum.HumanoidStateType.Freefall] = true,
}
-- Estados que contam como apoiado mesmo sem chão embaixo.
local SUPPORTED_STATES: { [Enum.HumanoidStateType]: boolean } = {
	[Enum.HumanoidStateType.Climbing] = true,
	[Enum.HumanoidStateType.Swimming] = true,
	[Enum.HumanoidStateType.Seated] = true,
}

type CharacterContext = {
	character: Model,
	humanoid: Humanoid,
	root: BasePart,
	connections: { RBXScriptConnection },
}

local MovementController = {}

local context: CharacterContext? = nil
local jumpState: DoubleJump.State = DoubleJump.new()
local doubleJumpCount = 0 -- quantos pulos duplos já aconteceram (para testes)

local function isHookActive(ctx: CharacterContext): boolean
	return ctx.character:GetAttribute(settings.HookActiveAttribute) == true
end

local function isGrounded(humanoid: Humanoid): boolean
	local state = humanoid:GetState()
	if SUPPORTED_STATES[state] then
		return true
	end
	-- FloorMaterial demora um quadro para virar Air depois do pulo: o estado manda primeiro.
	return not AIR_STATES[state] and humanoid.FloorMaterial ~= Enum.Material.Air
end

local function onStep()
	local ctx = context
	if not ctx then
		return
	end
	DoubleJump.setGrounded(jumpState, isGrounded(ctx.humanoid), os.clock())
end

local function applyDoubleJump(ctx: CharacterContext)
	-- Só a velocidade: `ChangeState(Jumping)` faria o Humanoid aplicar o próprio impulso (JumpHeight)
	-- um quadro depois, por cima do `DoubleJumpVelocity` (medido no playtest). Fica na animação de queda.
	local vel = ctx.root.AssemblyLinearVelocity
	ctx.root.AssemblyLinearVelocity = Vector3.new(vel.X, settings.DoubleJumpVelocity, 0)
	local pos = ctx.root.Position
	if pos.Z ~= planeZ then
		ctx.root.CFrame += Vector3.new(0, 0, planeZ - pos.Z)
	end
	doubleJumpCount += 1
end

local function onJumpRequest()
	local ctx = context
	if not ctx or ctx.humanoid.Health <= 0 then
		return
	end
	-- Congelado (RF-20) não pula: nem o pulo normal (FreezeController) nem o duplo.
	if Zones.isFrozen(ctx.character:GetAttribute(Config.Attributes.FrozenUntil)) then
		return
	end
	-- Atualiza antes de decidir: o pedido pode chegar antes do passo deste quadro.
	DoubleJump.setGrounded(jumpState, isGrounded(ctx.humanoid), os.clock())
	-- No embalo (corda já solta) o pulo duplo vale (Q42). Com a corda presa, não.
	local inMomentum = HookController.isInMomentum()
	local hookActive = not inMomentum
		and (isHookActive(ctx) or ctx.humanoid:GetState() == Enum.HumanoidStateType.Physics)
	if DoubleJump.request(jumpState, os.clock(), hookActive, RULES) then
		-- Não encerra o embalo: o AirBody segura a velocidade horizontal até pousar. Encerrar devolvia o
		-- corpo ao Humanoid, que freava o X no ar (medido: 14 -> 0 studs/s em 0,15 s).
		applyDoubleJump(ctx)
	end
end

local function cleanupCharacter()
	local ctx = context
	context = nil
	if ctx then
		for _, connection in ctx.connections do
			connection:Disconnect()
		end
	end
end

local function onCharacterAdded(character: Model)
	cleanupCharacter()
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	local root = character:WaitForChild("HumanoidRootPart") :: BasePart
	if player.Character ~= character then
		return -- trocou de personagem enquanto esperava
	end

	humanoid.WalkSpeed = settings.WalkSpeed
	jumpState = DoubleJump.new()

	local ctx: CharacterContext = {
		character = character,
		humanoid = humanoid,
		root = root,
		connections = {},
	}
	-- Prendeu o gancho (atributo ligou): devolve o pulo duplo.
	table.insert(
		ctx.connections,
		character:GetAttributeChangedSignal(settings.HookActiveAttribute):Connect(function()
			if isHookActive(ctx) then
				DoubleJump.recharge(jumpState)
			end
		end)
	)
	context = ctx
end

-- API pequena para testes no Studio (playtest pelo MCP, sem teclado de verdade).
MovementController.debug = {
	-- Simula um aperto de Espaço (o mesmo caminho do JumpRequest).
	requestJump = function()
		onJumpRequest()
	end,
	getState = function(): { [string]: any }
		local ctx = context
		return {
			charged = jumpState.charged,
			airborne = jumpState.airborneSince ~= nil,
			doubleJumpCount = doubleJumpCount,
			hookActive = if ctx then isHookActive(ctx) else nil,
			frozen = if ctx
				then Zones.isFrozen(ctx.character:GetAttribute(Config.Attributes.FrozenUntil))
				else nil,
			walkSpeed = if ctx then ctx.humanoid.WalkSpeed else nil,
			humanoidState = if ctx then ctx.humanoid:GetState().Name else nil,
			rootPosition = if ctx then ctx.root.Position else nil,
			velocity = if ctx then ctx.root.AssemblyLinearVelocity else nil,
		}
	end,
}

-- No Studio, a API de teste fica acessível de outro contexto: `MovementController.MovementDebug:Invoke(...)`.
local function createDebugBindable()
	local bindable = Instance.new("BindableFunction")
	bindable.Name = "MovementDebug"
	bindable.OnInvoke = function(command: string, ...: any): any
		local fn = (MovementController.debug :: any)[command]
		if typeof(fn) ~= "function" then
			error(`[Movement] comando de teste desconhecido: {command}`)
		end
		return fn(...)
	end
	bindable.Parent = script
end

function MovementController.Start()
	player.CharacterRemoving:Connect(cleanupCharacter)
	player.CharacterAdded:Connect(onCharacterAdded)
	if player.Character then
		task.spawn(onCharacterAdded, player.Character)
	end

	UserInputService.JumpRequest:Connect(onJumpRequest)
	RunService.PreSimulation:Connect(onStep)

	if RunService:IsStudio() then
		createDebugBindable()
	end
end

return MovementController
