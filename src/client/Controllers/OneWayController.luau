--!strict
--[[
	Bloco de mão única (tag `OneWay`, como o stopper do DDNet): passa no sentido do atributo
	`Config.MapElements.DirectionAttribute` ("Up", "Down", "Left", "Right") e é sólido no contrário.

	As peças são `CanCollide = false` no mapa. Como cada cliente simula o próprio personagem, este
	controller liga a colisão LOCALMENTE, a cada quadro, só para as peças perto do personagem e só
	quando ele está todo do lado sólido (ex.: "Up" = passa subindo; vira chão para quem está em cima).
	Movimento de lado dentro da peça fica livre. O gancho atravessa (HookController ignora a tag).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local MapElements = require(ReplicatedStorage.Shared.MapElements)

local settings = Config.MapElements
local HALF_BOX = Config.Zones.CharacterBoxSize / 2
local BOX_OFFSET_Y = Config.Zones.CharacterBoxOffsetY

local player = Players.LocalPlayer

local OneWayController = {}

local parts: { [BasePart]: true } = {}
-- Último estado de colisão de cada peça: dentro dela (ou encostado) o estado não muda, para um
-- personagem rápido que já entrou alguns studs no quadro não ser liberado no meio do caminho.
local solidState: { [BasePart]: boolean } = {}

-- A caixa do personagem toca a peça (no plano, com a folga)?
local function overlaps(part: BasePart, center: Vector3): boolean
	local tolerance = settings.OneWayTolerance
	local delta = center - part.Position
	return math.abs(delta.X) < part.Size.X / 2 + HALF_BOX.X + tolerance
		and math.abs(delta.Y) < part.Size.Y / 2 + HALF_BOX.Y + tolerance
end

local function track(instance: Instance)
	if instance:IsA("BasePart") then
		parts[instance] = true
	end
end

-- O personagem (caixa `CharacterBoxSize`) está todo do lado sólido da peça?
local function isOnSolidSide(part: BasePart, direction: unknown, center: Vector3): boolean
	local tolerance = settings.OneWayTolerance
	local halfPart = part.Size / 2
	local partCenter = part.Position
	if direction == "Down" then -- passa descendo: sólido para quem está embaixo
		return center.Y + HALF_BOX.Y <= partCenter.Y - halfPart.Y + tolerance
	elseif direction == "Right" then -- passa indo para a direita: sólido para quem está à direita
		return center.X - HALF_BOX.X >= partCenter.X + halfPart.X - tolerance
	elseif direction == "Left" then
		return center.X + HALF_BOX.X <= partCenter.X - halfPart.X + tolerance
	end
	-- "Up" (padrão): passa subindo; sólido para quem está em cima
	return center.Y - HALF_BOX.Y >= partCenter.Y + halfPart.Y - tolerance
end

local function step()
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return
	end
	local center = root.Position + Vector3.new(0, BOX_OFFSET_Y, 0)
	local radius = settings.OneWayCheckRadius
	for part in parts do
		local delta = part.Position - center
		local reach = radius + math.max(part.Size.X, part.Size.Y) / 2
		if math.abs(delta.X) > reach or math.abs(delta.Y) > reach then
			continue
		end
		local direction = part:GetAttribute(settings.DirectionAttribute)
		local solid =
			isOnSolidSide(part, if MapElements.isDirection(direction) then direction else "Up", center)
		if not solid and overlaps(part, center) then
			solid = solidState[part] == true -- encostado/dentro: mantém o lado de onde veio
		end
		solidState[part] = solid
		if part.CanCollide ~= solid then
			part.CanCollide = solid
		end
	end
end

function OneWayController.Start()
	local tag = Config.Tags.OneWay
	for _, instance in CollectionService:GetTagged(tag) do
		track(instance)
	end
	CollectionService:GetInstanceAddedSignal(tag):Connect(track)
	CollectionService:GetInstanceRemovedSignal(tag):Connect(function(instance)
		parts[instance :: BasePart] = nil
		solidState[instance :: BasePart] = nil
	end)
	-- Antes da física: a colisão deste quadro já vale para o passo do motor.
	RunService.PreSimulation:Connect(step)
end

return OneWayController
