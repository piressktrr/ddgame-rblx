--!strict
--[[
	Gelo no jogador local (RF-20; ADR 0014, 0045).

	O servidor (ZoneService) marca o atributo `Config.Attributes.FrozenUntil` no personagem. Enquanto
	ele existe, este controller trava os controles próprios do personagem:
	- não anda (WalkSpeed 0);
	- não pula (estado Jumping desligado no Humanoid);
	- o pulo duplo (MovementController) e o gancho (HookController) conferem o mesmo atributo.
	Física externa não é bloqueada (RF-21, ser puxado/empurrado por outro, é da Fase 4).

	Visual local simples: um Highlight azul-gelo no personagem. A contagem regressiva (RF-27) é da HUD
	de corrida, que lê o mesmo atributo.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)

local FROZEN_UNTIL = Config.Attributes.FrozenUntil
local player = Players.LocalPlayer

type FrozenState = {
	walkSpeed: number, -- velocidade de antes, para devolver ao descongelar
	highlight: Highlight,
}

type CharacterContext = {
	character: Model,
	humanoid: Humanoid,
	connections: { RBXScriptConnection },
	frozen: FrozenState?,
}

local FreezeController = {}

local context: CharacterContext? = nil

local function freeze(ctx: CharacterContext)
	if ctx.frozen then
		return
	end
	local highlight = Instance.new("Highlight")
	highlight.Name = "FrozenHighlight"
	highlight.FillColor = Config.Freeze.HighlightColor
	highlight.OutlineColor = Config.Freeze.HighlightColor
	highlight.FillTransparency = Config.Freeze.HighlightFillTransparency
	highlight.DepthMode = Enum.HighlightDepthMode.Occluded
	highlight.Adornee = ctx.character
	highlight.Parent = ctx.character

	ctx.frozen = { walkSpeed = ctx.humanoid.WalkSpeed, highlight = highlight }
	ctx.humanoid.WalkSpeed = 0
	ctx.humanoid.Jump = false
	ctx.humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
end

local function unfreeze(ctx: CharacterContext)
	local frozen = ctx.frozen
	if not frozen then
		return
	end
	ctx.frozen = nil
	frozen.highlight:Destroy()
	ctx.humanoid.WalkSpeed = frozen.walkSpeed
	ctx.humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
end

local function sync(ctx: CharacterContext)
	if ctx.humanoid.Health > 0 and Zones.isFrozen(ctx.character:GetAttribute(FROZEN_UNTIL)) then
		freeze(ctx)
	else
		unfreeze(ctx)
	end
end

local function cleanupCharacter()
	local ctx = context
	context = nil
	if ctx then
		for _, connection in ctx.connections do
			connection:Disconnect()
		end
		unfreeze(ctx)
	end
end

local function onCharacterAdded(character: Model)
	cleanupCharacter()
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	if player.Character ~= character then
		return -- trocou de personagem enquanto esperava
	end
	local ctx: CharacterContext = {
		character = character,
		humanoid = humanoid,
		connections = {},
		frozen = nil,
	}
	table.insert(
		ctx.connections,
		character:GetAttributeChangedSignal(FROZEN_UNTIL):Connect(function()
			sync(ctx)
		end)
	)
	-- Algo (ex.: o MovementController ao nascer) pode reescrever o WalkSpeed: congelado, volta a 0.
	table.insert(
		ctx.connections,
		humanoid:GetPropertyChangedSignal("WalkSpeed"):Connect(function()
			if ctx.frozen and humanoid.WalkSpeed ~= 0 then
				ctx.frozen.walkSpeed = humanoid.WalkSpeed
				humanoid.WalkSpeed = 0
			end
		end)
	)
	table.insert(
		ctx.connections,
		humanoid.Died:Connect(function()
			sync(ctx)
		end)
	)
	context = ctx
	sync(ctx)
end

-- Diz se o personagem local está congelado (usado pelos testes).
function FreezeController.isFrozen(): boolean
	local ctx = context
	return ctx ~= nil and ctx.frozen ~= nil
end

function FreezeController.Start()
	player.CharacterRemoving:Connect(cleanupCharacter)
	player.CharacterAdded:Connect(onCharacterAdded)
	if player.Character then
		task.spawn(onCharacterAdded, player.Character)
	end

	if RunService:IsStudio() then
		local bindable = Instance.new("BindableFunction")
		bindable.Name = "FreezeDebug"
		bindable.OnInvoke = function(): { [string]: any }
			local ctx = context
			return {
				frozen = FreezeController.isFrozen(),
				frozenUntil = if ctx then ctx.character:GetAttribute(FROZEN_UNTIL) else nil,
				walkSpeed = if ctx then ctx.humanoid.WalkSpeed else nil,
				jumpEnabled = if ctx
					then ctx.humanoid:GetStateEnabled(Enum.HumanoidStateType.Jumping)
					else nil,
			}
		end
		bindable.Parent = script
	end
end

return FreezeController
