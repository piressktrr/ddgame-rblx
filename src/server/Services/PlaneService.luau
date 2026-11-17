--!strict
--[[
	Correção do plano 2.5D no servidor (ADR 0039, RF-02).

	O cliente já trava o próprio personagem em Z (CharacterController), porque é dono da física dele.
	Aqui fica a rede de segurança: a cada `Config.Plane.ServerCheckInterval` segundos o servidor confere o
	Z de cada personagem e, se passou de `Config.Plane.ServerMaxDrift`, devolve o personagem ao plano.
	Jogadores colidem entre si (padrão do Roblox, ADR 0039): nada aqui desliga isso.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)

local PlaneService = {}

local elapsed = 0

local function correct(player: Player)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not character or not root or not root:IsA("BasePart") then
		return
	end
	local offset = Config.Plane.Z - root.Position.Z
	if math.abs(offset) > Config.Plane.ServerMaxDrift then
		character:PivotTo(character:GetPivot() + Vector3.new(0, 0, offset))
		warn(`[Plane] {player.Name} estava {string.format("%.2f", -offset)} studs fora do plano; corrigido`)
	end
end

local function step(dt: number)
	elapsed += dt
	if elapsed < Config.Plane.ServerCheckInterval then
		return
	end
	elapsed = 0
	for _, player in Players:GetPlayers() do
		correct(player)
	end
end

function PlaneService.Start()
	RunService.Heartbeat:Connect(step)
end

return PlaneService
