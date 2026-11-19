--!strict
--[[
	HUD da corrida em Roblox UI direto (IMPLEMENTATION_PLAN Fase 3 item 6; sem React/Fusion).

	- Timer (RF-61): conta enquanto o Player tem `RaceStartedAt` e ainda não tem `RaceFinishTime`;
	  depois de terminar, fica parado no tempo final. Precisão de 0,01 s.
	- Gelo (RF-27): contagem regressiva enquanto o personagem tem `FrozenUntil`.
	- Tela de fim (RF-62): ao receber `RaceFinished`, mostra o tempo, o melhor e os botões
	  "De novo" / "Voltar ao lobby" (mandam `RaceAction` ao servidor).
	- Botão "Lobby" pequeno durante a corrida, para sair a qualquer momento.
	- Placar da sessão (RF-63), só no lobby (`InRace` false): `BestTime` de cada jogador do servidor.

	Os tempos usam `workspace:GetServerTimeNow()`, o mesmo relógio que o servidor grava.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Net = require(ReplicatedStorage.Shared.Net)

local Attributes = Config.Attributes
local ui = Config.RaceUi
local player = Players.LocalPlayer

local UIController = {}

local actionRemote: RemoteEvent? = nil
local timerLabel: TextLabel
local freezeLabel: TextLabel
local lobbyButton: TextButton
local endPanel: Frame
local endTimeLabel: TextLabel
local endBestLabel: TextLabel
local board: Frame
local boardRows: Frame

-- 12.34 -> "12.34"; 75.5 -> "1:15.50".
local function formatTime(seconds: number): string
	local value = math.max(seconds, 0)
	local minutes = math.floor(value / 60)
	local rest = value - minutes * 60
	if minutes > 0 then
		return string.format("%d:%05.2f", minutes, rest)
	end
	return string.format("%.2f", rest)
end

local function getNumber(instance: Instance?, name: string): number?
	if not instance then
		return nil
	end
	local value = instance:GetAttribute(name)
	return if typeof(value) == "number" then value else nil
end

local function addCorner(parent: GuiObject)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, ui.CornerRadius)
	corner.Parent = parent
end

local function newLabel(name: string, textSize: number, parent: Instance): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.Font = ui.Font
	label.TextSize = textSize
	label.TextColor3 = ui.TextColor
	label.TextStrokeColor3 = ui.StrokeColor
	label.TextStrokeTransparency = 0.4
	label.Text = ""
	label.Parent = parent
	return label
end

local function newButton(
	name: string,
	text: string,
	size: Vector2,
	color: Color3,
	parent: Instance
): TextButton
	local button = Instance.new("TextButton")
	button.Name = name
	button.Size = UDim2.fromOffset(size.X, size.Y)
	button.BackgroundColor3 = color
	button.AutoButtonColor = true
	button.Font = ui.Font
	button.TextSize = ui.EndTextSize * 0.8
	button.TextColor3 = ui.TextColor
	button.Text = text
	button.Parent = parent
	addCorner(button)
	return button
end

-- O painel some quando o servidor aceita (InRace ou RaceStartedAt mudam), não no clique: se o pedido
-- for recusado (cooldown), os botões continuam ali.
local function sendAction(action: "Again" | "Lobby")
	local remote = actionRemote
	if remote then
		remote:FireServer(action)
	end
end

local function build()
	local gui = Instance.new("ScreenGui")
	gui.Name = "RaceUi"
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- Timer no topo, no meio.
	timerLabel = newLabel("Timer", ui.TimerTextSize, gui)
	timerLabel.AnchorPoint = Vector2.new(0.5, 0)
	timerLabel.Position = UDim2.new(0.5, 0, 0, ui.TimerTopOffset)
	timerLabel.Size = UDim2.fromOffset(240, ui.TimerTextSize + 8)
	timerLabel.Visible = false

	-- Contador do gelo, acima do personagem (o personagem fica no meio da tela).
	freezeLabel = newLabel("Freeze", ui.FreezeTextSize, gui)
	freezeLabel.AnchorPoint = Vector2.new(0.5, 0.5)
	freezeLabel.Position = UDim2.fromScale(0.5, 0.3)
	freezeLabel.Size = UDim2.fromOffset(400, ui.FreezeTextSize + 8)
	freezeLabel.TextColor3 = ui.FreezeColor
	freezeLabel.Visible = false

	-- Botão pequeno para sair da corrida a qualquer momento.
	lobbyButton = newButton("LobbyButton", "Lobby", ui.LobbyButtonSize, ui.LobbyButtonColor, gui)
	lobbyButton.AnchorPoint = Vector2.new(1, 0)
	lobbyButton.Position = UDim2.new(1, -12, 0, ui.TimerTopOffset)
	lobbyButton.TextSize = 18
	lobbyButton.Visible = false
	lobbyButton.Activated:Connect(function()
		sendAction("Lobby")
	end)

	-- Tela de fim.
	endPanel = Instance.new("Frame")
	endPanel.Name = "EndPanel"
	endPanel.AnchorPoint = Vector2.new(0.5, 0.5)
	endPanel.Position = UDim2.fromScale(0.5, 0.5)
	endPanel.Size = UDim2.fromOffset(ui.EndPanelSize.X, ui.EndPanelSize.Y)
	endPanel.BackgroundColor3 = ui.PanelColor
	endPanel.BackgroundTransparency = ui.PanelTransparency
	endPanel.Visible = false
	endPanel.Parent = gui
	addCorner(endPanel)

	local title = newLabel("Title", ui.EndTitleTextSize, endPanel)
	title.Position = UDim2.fromOffset(0, 14)
	title.Size = UDim2.new(1, 0, 0, ui.EndTitleTextSize + 4)
	title.Text = "Chegou!"

	endTimeLabel = newLabel("Time", ui.EndTextSize, endPanel)
	endTimeLabel.Position = UDim2.fromOffset(0, 66)
	endTimeLabel.Size = UDim2.new(1, 0, 0, ui.EndTextSize + 4)

	endBestLabel = newLabel("Best", ui.EndTextSize, endPanel)
	endBestLabel.Position = UDim2.fromOffset(0, 102)
	endBestLabel.Size = UDim2.new(1, 0, 0, ui.EndTextSize + 4)

	local buttons = Instance.new("Frame")
	buttons.Name = "Buttons"
	buttons.BackgroundTransparency = 1
	buttons.AnchorPoint = Vector2.new(0.5, 1)
	buttons.Position = UDim2.new(0.5, 0, 1, -18)
	buttons.Size = UDim2.new(1, -24, 0, ui.EndButtonSize.Y)
	buttons.Parent = endPanel
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Padding = UDim.new(0, 12)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = buttons

	local againButton = newButton("Again", "De novo", ui.EndButtonSize, ui.AgainButtonColor, buttons)
	againButton.LayoutOrder = 1
	againButton.Activated:Connect(function()
		sendAction("Again")
	end)
	local backButton = newButton("Lobby", "Voltar ao lobby", ui.EndButtonSize, ui.BackButtonColor, buttons)
	backButton.LayoutOrder = 2
	backButton.Activated:Connect(function()
		sendAction("Lobby")
	end)

	-- Placar da sessão, no canto esquerdo.
	board = Instance.new("Frame")
	board.Name = "Leaderboard"
	board.Position = UDim2.fromOffset(12, ui.TimerTopOffset)
	board.Size = UDim2.fromOffset(ui.BoardWidth, 0)
	board.AutomaticSize = Enum.AutomaticSize.Y
	board.BackgroundColor3 = ui.PanelColor
	board.BackgroundTransparency = ui.PanelTransparency
	board.Parent = gui
	addCorner(board)
	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 8)
	padding.PaddingBottom = UDim.new(0, 8)
	padding.PaddingLeft = UDim.new(0, 10)
	padding.PaddingRight = UDim.new(0, 10)
	padding.Parent = board
	local boardLayout = Instance.new("UIListLayout")
	boardLayout.SortOrder = Enum.SortOrder.LayoutOrder
	boardLayout.Parent = board

	local boardTitle = newLabel("Title", ui.BoardTextSize, board)
	boardTitle.Size = UDim2.new(1, 0, 0, ui.BoardRowHeight)
	boardTitle.Text = "Placar da sessão"
	boardTitle.LayoutOrder = 0

	boardRows = Instance.new("Frame")
	boardRows.Name = "Rows"
	boardRows.BackgroundTransparency = 1
	boardRows.Size = UDim2.fromScale(1, 0)
	boardRows.AutomaticSize = Enum.AutomaticSize.Y
	boardRows.LayoutOrder = 1
	boardRows.Parent = board
	local rowsLayout = Instance.new("UIListLayout")
	rowsLayout.SortOrder = Enum.SortOrder.LayoutOrder
	rowsLayout.Parent = boardRows

	gui.Parent = player:WaitForChild("PlayerGui")
end

-- Refaz as linhas do placar: quem tem tempo primeiro (menor primeiro), depois quem ainda não terminou.
local function refreshBoard(leaving: Player?)
	for _, child in boardRows:GetChildren() do
		if child:IsA("TextLabel") then
			child:Destroy()
		end
	end
	local entries: { { name: string, best: number? } } = {}
	for _, other in Players:GetPlayers() do
		if other == leaving then
			continue
		end
		table.insert(entries, { name = other.DisplayName, best = getNumber(other, Attributes.BestTime) })
	end
	table.sort(entries, function(a, b)
		if a.best and b.best then
			return a.best < b.best
		elseif a.best or b.best then
			return a.best ~= nil
		end
		return a.name < b.name
	end)
	for index, entry in entries do
		if index > ui.BoardMaxRows then
			break
		end
		local row = newLabel(`Row{index}`, ui.BoardTextSize, boardRows)
		row.Size = UDim2.new(1, 0, 0, ui.BoardRowHeight)
		row.TextXAlignment = Enum.TextXAlignment.Left
		row.LayoutOrder = index
		local timeText = if entry.best then `{formatTime(entry.best)} s` else "—"
		row.Text = `{index}. {entry.name}  {timeText}`
	end
end

local function watchPlayer(other: Player)
	other:GetAttributeChangedSignal(Attributes.BestTime):Connect(function()
		refreshBoard()
	end)
	refreshBoard()
end

local function refreshRaceState()
	local inRace = player:GetAttribute(Attributes.InRace) == true
	board.Visible = not inRace
	lobbyButton.Visible = inRace
	if not inRace then
		endPanel.Visible = false
	end
end

local function update()
	local now = workspace:GetServerTimeNow()

	local startedAt = getNumber(player, Attributes.RaceStartedAt)
	local finishTime = getNumber(player, Attributes.RaceFinishTime)
	if startedAt and player:GetAttribute(Attributes.InRace) == true then
		timerLabel.Visible = true
		timerLabel.Text = formatTime(if finishTime then finishTime else now - startedAt)
	else
		timerLabel.Visible = false
	end

	local character = player.Character
	local frozenUntil = getNumber(character, Attributes.FrozenUntil)
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	-- Morto (o gelo venceu ou caiu na zona mortal): o contador some enquanto renasce.
	if frozenUntil and humanoid and humanoid.Health > 0 then
		-- Sem contagem: o gelo dura enquanto estiver no freeze (DDNet).
		freezeLabel.Visible = true
		freezeLabel.Text = "Congelado!"
		freezeLabel.TextColor3 = ui.FreezeColor
	else
		freezeLabel.Visible = false
	end
end

local function onFinished(time: unknown, best: unknown)
	if typeof(time) ~= "number" or typeof(best) ~= "number" then
		return
	end
	endTimeLabel.Text = `Tempo: {formatTime(time)} s`
	local isNewBest = time <= best
	endBestLabel.Text = if isNewBest
		then `Novo recorde! {formatTime(best)} s`
		else `Melhor: {formatTime(best)} s`
	endBestLabel.TextColor3 = if isNewBest then ui.NewBestColor else ui.TextColor
	endPanel.Visible = true
end

function UIController.Start()
	build()
	actionRemote = Net.get("RaceAction")
	Net.get("RaceFinished").OnClientEvent:Connect(onFinished)

	player:GetAttributeChangedSignal(Attributes.InRace):Connect(refreshRaceState)
	-- Corrida nova (De novo / portal): some a tela de fim.
	player:GetAttributeChangedSignal(Attributes.RaceStartedAt):Connect(function()
		if player:GetAttribute(Attributes.RaceFinishTime) == nil then
			endPanel.Visible = false
		end
	end)
	refreshRaceState()

	for _, other in Players:GetPlayers() do
		watchPlayer(other)
	end
	Players.PlayerAdded:Connect(watchPlayer)
	Players.PlayerRemoving:Connect(refreshBoard)

	RunService.RenderStepped:Connect(update)
end

return UIController
