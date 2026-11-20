--!strict
--[[
	Martelo do DDRace no servidor (cooperação).

	O cliente de quem bate mira, vê quem acertou e manda `HammerSwing(direção, alvos)`. O servidor não
	confia: confere intervalo, se quem bate está vivo e não congelado, e, para cada alvo, se está vivo,
	fora do solo (os dois), dentro do círculo do martelo (com folga para o atraso da rede) e sem parede
	no meio. Para cada alvo válido:
	  - manda `HammerHit(empurrão)` só para o cliente do alvo (cada cliente é dono do próprio corpo);
	  - descongela (DDNet; dentro do freeze o ZoneService congela de novo, mas o empurrão continua).
	Avisa todos os outros clientes com `HammerFx` para desenharem a batida.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HammerRules = require(ReplicatedStorage.Shared.Logic.HammerRules)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local Net = require(ReplicatedStorage.Shared.Net)

local settings = Config.Hammer
local MAX_TARGETS = 8

local HammerService = {}

local lastSwingAt: { [Player]: number } = {}

local function isSolo(character: Model): boolean
	return character:GetAttribute(Config.Attributes.Solo) == true
end

-- Root do personagem se ele está vivo, ou nil.
local function aliveRoot(player: Player): (Model?, BasePart?)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not character or not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return nil, nil
	end
	return character, root
end

-- Parede (peça colidível fora dos personagens) entre dois pontos?
local function blocked(from: Vector3, to: Vector3): boolean
	local exclude: { Instance } = {}
	for _, other in Players:GetPlayers() do
		if other.Character then
			table.insert(exclude, other.Character)
		end
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = exclude
	params.RespectCanCollide = true
	return workspace:Raycast(from, to - from, params) ~= nil
end

local function onSwing(player: Player, direction: unknown, targets: unknown)
	if typeof(direction) ~= "Vector3" or typeof(targets) ~= "table" then
		return
	end
	local aim = direction :: Vector3
	if not HookRules.isFiniteVector(aim) or Vector3.new(aim.X, aim.Y, 0).Magnitude < 0.5 then
		return
	end
	aim = Vector3.new(aim.X, aim.Y, 0).Unit

	local now = os.clock()
	local last = lastSwingAt[player]
	if last and now - last < settings.Cooldown - settings.ServerCooldownSlack then
		return
	end
	local character, root = aliveRoot(player)
	if not character or not root then
		return
	end
	if Zones.isFrozen(character:GetAttribute(Config.Attributes.FrozenUntil)) then
		return -- congelado não bate (DDNet)
	end
	lastSwingAt[player] = now

	local origin = root.Position
	local center = HammerRules.hitCenter(origin, aim, settings)
	local hits: { Vector3 } = {}
	local hitRemote = Net.get("HammerHit")
	local seen: { [Player]: boolean } = {}
	for index, value in targets :: { any } do
		if index > MAX_TARGETS then
			break
		end
		if typeof(value) ~= "Instance" or not (value :: Instance):IsA("Player") then
			continue
		end
		local target = value :: Player
		if target == player or seen[target] then
			continue
		end
		seen[target] = true
		local targetCharacter, targetRoot = aliveRoot(target)
		if not targetCharacter or not targetRoot or isSolo(character) or isSolo(targetCharacter) then
			continue
		end
		local position = targetRoot.Position
		-- Folga cresce com a velocidade dos dois: no ar o servidor vê posições atrasadas.
		local speeds = targetRoot.AssemblyLinearVelocity.Magnitude + root.AssemblyLinearVelocity.Magnitude
		local tolerance = settings.ServerRadiusTolerance + speeds * settings.ServerLagWindow
		if not HammerRules.isHit(origin, aim, position, settings, tolerance) then
			continue
		end
		if blocked(Vector3.new(center.X, center.Y, position.Z), position) and blocked(origin, position) then
			continue
		end
		if settings.Unfreeze then
			targetCharacter:SetAttribute(Config.Attributes.FrozenUntil, nil)
		end
		hitRemote:FireClient(target, HammerRules.knockback(origin, position, settings))
		table.insert(hits, position)
	end

	local fxRemote = Net.get("HammerFx")
	for _, other in Players:GetPlayers() do
		if other ~= player then
			fxRemote:FireClient(other, player, aim, hits)
		end
	end
end

function HammerService.Start()
	Net.get("HammerSwing").OnServerEvent:Connect(onSwing)
	Players.PlayerRemoving:Connect(function(player: Player)
		lastSwingAt[player] = nil
	end)
end

return HammerService
