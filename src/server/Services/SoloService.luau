--!strict
--[[
	Modo solo (linhas `SoloStart`/`SoloEnd` do MapBuilder). No DDNet o trecho solo leva o jogador a
	um servidor vazio; aqui ele vira "fantasma" para os outros: continua igual, mas não colide com
	nenhum outro personagem (grupos de colisão `Config.Solo`).

	- Todo personagem nasce no grupo `PlayersGroup` (colide com os outros, como antes).
	- Em solo: grupo `SoloGroup`, que não colide com nenhum personagem (nem com outro em solo), e o
	  atributo `Config.Attributes.Solo = true` no personagem, para mecânicas entre jogadores futuras
	  (gancho em jogador) ignorarem quem está em solo. O mapa continua colidindo normalmente.
	- Renascer ou voltar ao checkpoint (zona de morte) sai do solo.
]]

local Players = game:GetService("Players")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)

local settings = Config.Solo
local SOLO_ATTRIBUTE = Config.Attributes.Solo

local SoloService = {}

local function applyGroup(character: Model, group: string)
	for _, descendant in character:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.CollisionGroup = group
		end
	end
end

local function currentGroup(character: Model): string
	return if character:GetAttribute(SOLO_ATTRIBUTE) == true
		then settings.SoloGroup
		else settings.PlayersGroup
end

function SoloService.isSolo(player: Player): boolean
	local character = player.Character
	return character ~= nil and character:GetAttribute(SOLO_ATTRIBUTE) == true
end

function SoloService.setSolo(player: Player, solo: boolean)
	local character = player.Character
	if not character or (character:GetAttribute(SOLO_ATTRIBUTE) == true) == solo then
		return
	end
	character:SetAttribute(SOLO_ATTRIBUTE, if solo then true else nil)
	applyGroup(character, currentGroup(character))
end

local function onCharacterAdded(character: Model)
	applyGroup(character, settings.PlayersGroup)
	-- Peças que chegam depois (acessórios, ferramentas) entram no grupo atual.
	character.DescendantAdded:Connect(function(descendant)
		if descendant:IsA("BasePart") then
			descendant.CollisionGroup = currentGroup(character)
		end
	end)
end

function SoloService.Start()
	PhysicsService:RegisterCollisionGroup(settings.PlayersGroup)
	PhysicsService:RegisterCollisionGroup(settings.SoloGroup)
	PhysicsService:CollisionGroupSetCollidable(settings.SoloGroup, settings.PlayersGroup, false)
	PhysicsService:CollisionGroupSetCollidable(settings.SoloGroup, settings.SoloGroup, false)

	local function onPlayerAdded(player: Player)
		player.CharacterAdded:Connect(onCharacterAdded)
		if player.Character then
			onCharacterAdded(player.Character)
		end
	end
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
end

return SoloService
