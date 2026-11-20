--!strict
--[[
	Martelo do DDRace no cliente (cooperação). É uma arma: com ela equipada (WeaponController), o botão
	esquerdo do mouse bate na direção do cursor (`HammerController.fire`).

	- Quem bate: confere o intervalo e o gelo, vê quem está no círculo do martelo (`HammerRules`, sem
	  parede no meio) e manda `HammerSwing(direção, alvos)`; o servidor valida (HammerService).
	- Quem apanha: recebe `HammerHit(empurrão)` e soma na própria velocidade
	  (`HookController.applyImpulse`), já que cada cliente é dono do próprio corpo.
	- Visual local (todos veem): o martelo aparece acima da cabeça e desce na direção da mira; no alvo,
	  uma explosão branca rápida (como o "hit" do DDNet).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Aim = require(ReplicatedStorage.Shared.Logic.Aim)
local Config = require(ReplicatedStorage.Shared.Config)
local HammerRules = require(ReplicatedStorage.Shared.Logic.HammerRules)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)
local Net = require(ReplicatedStorage.Shared.Net)

local HookController = require(script.Parent.HookController)

local settings = Config.Hammer
local player = Players.LocalPlayer

local HANDLE_LENGTH = 2.4
local HANDLE_COLOR = Color3.fromRGB(122, 84, 48)
local HEAD_COLOR = Color3.fromRGB(150, 152, 162)
local PIVOT_HEIGHT = 1 -- studs acima do root (o martelo gira em volta deste ponto)
local SWING_ANGLE = math.rad(110) -- de onde a batida começa (por cima), em relação à mira
local FRONT_OFFSET = 1.2 -- studs para o lado da câmera (na frente do corpo)
local HIT_FX_TIME = 0.15
local HIT_FX_SIZE = 2.6

local HammerController = {}

local lastSwingAt = -math.huge
local swingRemote: RemoteEvent? = nil
local lastHits: { Player } = {} -- para testes

local function newPart(name: string, size: Vector3, color: Color3, material: Enum.Material): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.Color = color
	part.Material = material
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	return part
end

local function isSolo(character: Model?): boolean
	return character ~= nil and character:GetAttribute(Config.Attributes.Solo) == true
end

local function aliveRoot(owner: Player): BasePart?
	local character = owner.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
		return nil
	end
	return root
end

-- Explosão branca rápida no ponto da batida.
local function playHitFx(position: Vector3)
	local burst = newPart("HammerHit", Vector3.one * 0.6, Color3.new(1, 1, 1), Enum.Material.Neon)
	burst.Shape = Enum.PartType.Ball
	burst.Position = position
	burst.Parent = workspace.CurrentCamera
	local start = os.clock()
	local connection: RBXScriptConnection
	connection = RunService.RenderStepped:Connect(function()
		local alpha = math.min((os.clock() - start) / HIT_FX_TIME, 1)
		burst.Size = Vector3.one * (0.6 + (HIT_FX_SIZE - 0.6) * alpha)
		burst.Transparency = alpha
		if alpha >= 1 then
			connection:Disconnect()
			burst:Destroy()
		end
	end)
end

-- Martelo que desce por cima até a direção da mira, preso ao personagem enquanto aparece.
local function playSwing(root: BasePart, aimDirection: Vector3)
	local model = Instance.new("Model")
	model.Name = "Hammer"
	local handle =
		newPart("Handle", Vector3.new(0.35, 0.35, HANDLE_LENGTH), HANDLE_COLOR, Enum.Material.WoodPlanks)
	handle.Parent = model
	local head = newPart("Head", Vector3.new(1.5, 0.95, 0.95), HEAD_COLOR, Enum.Material.Metal)
	head.Parent = model
	model.Parent = workspace.CurrentCamera

	local aimAngle = math.atan2(aimDirection.Y, aimDirection.X)
	-- Começa por cima da cabeça: do lado de trás de quem mira para a direita (ou esquerda).
	local startAngle = aimAngle + (if aimDirection.X >= 0 then SWING_ANGLE else -SWING_ANGLE)
	local start = os.clock()
	local connection: RBXScriptConnection
	connection = RunService.RenderStepped:Connect(function()
		local elapsed = os.clock() - start
		if elapsed >= settings.ShowTime or not root.Parent then
			connection:Disconnect()
			model:Destroy()
			return
		end
		local alpha = math.min(elapsed / settings.SwingTime, 1)
		alpha = 1 - (1 - alpha) * (1 - alpha) -- desacelera no fim
		local angle = startAngle + (aimAngle - startAngle) * alpha
		local direction = Vector3.new(math.cos(angle), math.sin(angle), 0)
		local camera = workspace.CurrentCamera
		local toCamera = if camera.CFrame.Position.Z >= root.Position.Z then 1 else -1
		local pivot = root.Position + Vector3.new(0, PIVOT_HEIGHT, FRONT_OFFSET * toCamera)
		local handleCenter = pivot + direction * (HANDLE_LENGTH / 2)
		handle.CFrame = CFrame.lookAlong(handleCenter, direction, Vector3.zAxis)
		head.CFrame = CFrame.lookAlong(pivot + direction * HANDLE_LENGTH, direction, Vector3.zAxis)
	end)
end

local function playEffects(attacker: Player, aimDirection: Vector3, hits: { Vector3 })
	local root = aliveRoot(attacker)
	if root then
		playSwing(root, aimDirection)
	end
	for _, position in hits do
		playHitFx(position - aimDirection * 1)
	end
end

local function getAimPoint(): Vector3?
	local mouse = UserInputService:GetMouseLocation()
	local ray = workspace.CurrentCamera:ViewportPointToRay(mouse.X, mouse.Y)
	return Aim.intersectPlane(ray.Origin, ray.Direction, Config.Plane.Z)
end

local function isBlocked(from: Vector3, to: Vector3): boolean
	local exclude: { Instance } = { workspace.CurrentCamera }
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

-- Bate mirando em `aimPoint` (ponto do plano; nil = cursor). Devolve os jogadores acertados.
local function swing(aimPoint: Vector3?): { Player }
	local character = player.Character
	local root = aliveRoot(player)
	if not character or not root then
		return {}
	end
	if Zones.isFrozen(character:GetAttribute(Config.Attributes.FrozenUntil)) then
		return {} -- congelado não bate
	end
	local now = os.clock()
	if now - lastSwingAt < settings.Cooldown then
		return {}
	end
	lastSwingAt = now

	local target = aimPoint or getAimPoint()
	local aimDirection = if target
		then HammerRules.aimDirection(root.Position, target)
		else Vector3.new(if root.CFrame.LookVector.X < 0 then -1 else 1, 0, 0)
	local center = HammerRules.hitCenter(root.Position, aimDirection, settings)

	local hits: { Player } = {}
	local hitPositions: { Vector3 } = {}
	if not isSolo(character) then
		for _, other in Players:GetPlayers() do
			local otherRoot = if other ~= player then aliveRoot(other) else nil
			if not otherRoot or isSolo(other.Character) then
				continue
			end
			local position = otherRoot.Position
			if
				HammerRules.isHit(root.Position, aimDirection, position, settings)
				and not isBlocked(Vector3.new(center.X, center.Y, position.Z), position)
			then
				table.insert(hits, other)
				table.insert(hitPositions, position)
			end
		end
	end

	playEffects(player, aimDirection, hitPositions)
	local remote = swingRemote
	if remote then
		remote:FireServer(aimDirection, hits)
	end
	lastHits = hits
	return hits
end

-- Disparo da arma (WeaponController): bate mirando no cursor.
function HammerController.fire()
	swing(nil)
end

function HammerController.Start()
	swingRemote = Net.get("HammerSwing")
	Net.get("HammerHit").OnClientEvent:Connect(function(push: unknown)
		if typeof(push) == "Vector3" then
			HookController.applyImpulse(push :: Vector3)
		end
	end)
	Net.get("HammerFx").OnClientEvent:Connect(function(attacker: unknown, direction: unknown, hits: unknown)
		if
			typeof(attacker) == "Instance"
			and (attacker :: Instance):IsA("Player")
			and typeof(direction) == "Vector3"
			and typeof(hits) == "table"
		then
			local positions: { Vector3 } = {}
			for _, value in hits :: { any } do
				if typeof(value) == "Vector3" then
					table.insert(positions, value)
				end
			end
			playEffects(attacker :: Player, direction :: Vector3, positions)
		end
	end)

	-- Testes no Studio (MCP): `HammerDebug:Invoke("swing", aimPoint)` devolve os nomes acertados.
	if RunService:IsStudio() then
		local bindable = Instance.new("BindableFunction")
		bindable.Name = "HammerDebug"
		bindable.OnInvoke = function(command: string, aimPoint: Vector3?): any
			if command == "swing" then
				lastSwingAt = -math.huge
				local names = {}
				for _, hit in swing(aimPoint) do
					table.insert(names, hit.Name)
				end
				return names
			elseif command == "impulse" and aimPoint then
				HookController.applyImpulse(aimPoint) -- aqui `aimPoint` é o empurrão
				return true
			end
			return #lastHits
		end
		bindable.Parent = script
	end
end

return HammerController
