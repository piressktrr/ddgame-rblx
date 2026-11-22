--!strict
--[[
	Corrida de cada jogador: timer, chegada e botões da tela de fim (RF-61, RF-62, RF-63).

	- Começar a corrida (`RaceService.beginRace`, chamado pelo portal do LobbyService ou pelo "Again"):
	  zera o checkpoint, marca `InRace`, grava `RaceStartedAt` (tempo do servidor) e limpa
	  `RaceFinishTime`.
	- Chegada: o jogador em corrida que está sobre a peça com a tag `RaceFinish` (conferido por zona,
	  como o CheckpointService, não por Touched) termina. O tempo vai para `RaceFinishTime`, o melhor
	  da sessão para `BestTime`, e o cliente recebe `RaceFinished(time, best)`. Uma vez por corrida:
	  só termina quem tem `RaceStartedAt` e ainda não tem `RaceFinishTime`.
	- `RaceAction` (cliente -> servidor):
	    "Again": recomeça do `RaceStart` com timer novo.
	    "Lobby": sai da corrida e volta ao `LobbySpawn`.
	    "Play": do menu principal (fora de corrida), começa a corrida no `RaceStart` (como o portal).
	  Os dois recarregam o personagem (`LoadCharacter`): isso solta o gancho, devolve os verdes
	  (`HookOnceEpoch` muda no HookService ao renascer), tira o gelo e quem posiciona é o LobbyService
	  (RaceStart se em corrida e sem checkpoint, lobby se fora de corrida).
	  O servidor confere o tipo do argumento e limita a frequência por jogador.

	O placar da sessão (RF-63) é o próprio atributo `BestTime` de cada Player: fica só em memória e
	some quando o servidor fecha. Quem desenha é o UIController.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Net = require(ReplicatedStorage.Shared.Net)
local Zones = require(ReplicatedStorage.Shared.Logic.Zones)

local Attributes = Config.Attributes
local settings = Config.Race

local RaceService = {}

local finishedRemote: RemoteEvent? = nil
local lastActionAt: { [Player]: number } = {}
local busy: { [Player]: boolean } = {}

local function getNumber(player: Player, name: string): number?
	local value = player:GetAttribute(name)
	return if typeof(value) == "number" then value else nil
end

-- Começa uma corrida nova para o jogador (não move o personagem: quem chama decide onde ele fica).
function RaceService.beginRace(player: Player)
	player:SetAttribute(Attributes.Checkpoint, 0)
	player:SetAttribute(Attributes.InRace, true)
	player:SetAttribute(Attributes.RaceFinishTime, nil)
	player:SetAttribute(Attributes.RaceStartedAt, workspace:GetServerTimeNow())
end

local function finish(player: Player, startedAt: number)
	local time = workspace:GetServerTimeNow() - startedAt
	local best = getNumber(player, Attributes.BestTime)
	if not best or time < best then
		best = time
		player:SetAttribute(Attributes.BestTime, time)
	end
	player:SetAttribute(Attributes.RaceFinishTime, time)
	print(
		`[Race] {player.Name} terminou em {string.format("%.2f", time)} s (melhor {string.format("%.2f", best)} s)`
	)
	local remote = finishedRemote
	if remote then
		remote:FireClient(player, time, best)
	end
end

-- Linha de chegada (ZoneService): termina a run se ela está valendo e ainda não terminou.
function RaceService.finishRun(player: Player)
	if player:GetAttribute(Attributes.InRace) ~= true or busy[player] then
		return
	end
	local startedAt = getNumber(player, Attributes.RaceStartedAt)
	if startedAt and player:GetAttribute(Attributes.RaceFinishTime) == nil then
		finish(player, startedAt)
	end
end

local function checkFinish()
	local finishes = CollectionService:GetTagged(Config.Tags.RaceFinish)
	if #finishes == 0 then
		return
	end
	for _, player in Players:GetPlayers() do
		if player:GetAttribute(Attributes.InRace) ~= true or busy[player] then
			continue
		end
		local startedAt = getNumber(player, Attributes.RaceStartedAt)
		if not startedAt or player:GetAttribute(Attributes.RaceFinishTime) ~= nil then
			continue
		end
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
			continue
		end
		local reached = getNumber(player, Attributes.Checkpoint) or 0
		for _, part in finishes do
			-- A chegada que também é checkpoint (`Order`) só vale depois de passar pelos anteriores.
			local order = part:GetAttribute("Order")
			if typeof(order) == "number" and reached < order - 1 then
				continue
			end
			if
				part:IsA("BasePart")
				and Zones.isAbove(part.CFrame, part.Size, settings.FinishZoneHeight, root.Position)
			then
				finish(player, startedAt)
				break
			end
		end
	end
end

-- Recarrega o personagem; o LobbyService o põe no RaceStart ou no lobby conforme `InRace`.
local function respawn(player: Player)
	busy[player] = true
	local ok, err = pcall(function()
		player:LoadCharacter()
	end)
	busy[player] = nil
	if not ok then
		warn(`[Race] LoadCharacter falhou para {player.Name}: {err}`)
	end
end

local function again(player: Player)
	-- Sem timer enquanto renasce; o tempo começa quando o personagem novo já existe.
	player:SetAttribute(Attributes.RaceStartedAt, nil)
	player:SetAttribute(Attributes.RaceFinishTime, nil)
	player:SetAttribute(Attributes.Checkpoint, 0)
	player:SetAttribute(Attributes.InRace, true)
	respawn(player)
	if player.Parent then
		RaceService.beginRace(player)
		print(`[Race] {player.Name} recomeçou a corrida`)
	end
end

local function backToLobby(player: Player)
	player:SetAttribute(Attributes.InRace, false)
	player:SetAttribute(Attributes.RaceStartedAt, nil)
	player:SetAttribute(Attributes.RaceFinishTime, nil)
	player:SetAttribute(Attributes.Checkpoint, 0)
	respawn(player)
	print(`[Race] {player.Name} voltou ao lobby`)
end

local function onAction(player: Player, action: unknown)
	if action ~= "Again" and action ~= "Lobby" and action ~= "Play" then
		return
	end
	local now = os.clock()
	local last = lastActionAt[player]
	if busy[player] or (last and now - last < settings.ActionCooldown) then
		return
	end
	-- "De novo" só existe dentro da corrida; "Jogar" (menu) só fora dela.
	local inRace = player:GetAttribute(Attributes.InRace) == true
	if (action == "Again" and not inRace) or (action == "Play" and inRace) then
		return
	end
	lastActionAt[player] = now
	if action == "Again" or action == "Play" then
		again(player)
	else
		backToLobby(player)
	end
end

function RaceService.Start()
	finishedRemote = Net.get("RaceFinished")
	Net.get("RaceAction").OnServerEvent:Connect(onAction)

	Players.PlayerRemoving:Connect(function(player)
		lastActionAt[player] = nil
		busy[player] = nil
	end)

	-- A chegada é conferida a cada frame: o tempo é mostrado em centésimos (RF-61).
	RunService.Heartbeat:Connect(checkFinish)
end

return RaceService
