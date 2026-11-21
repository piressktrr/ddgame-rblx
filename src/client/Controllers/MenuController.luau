--!strict
--[[
	Menu principal: uma tela de jogo "de verdade" antes de entrar (no lugar de cair direto no lobby),
	na mesma ideia do menu do DDNet, com visual próprio.

	- Fundo: céu com raios de sol girando e nuvens passando, e por baixo o PRÓPRIO mapa (cópia local
	  num ViewportFrame) com a câmera andando devagar por ele.
	- Logo no topo e uma coluna de botões grandes, cada um com uma prévia à direita:
	    Jogar      -> lista de mapas (como a lista de servidores): mapa, etapas, quem está correndo,
	                  recorde da sessão; "Entrar" começa a corrida (`RaceAction` "Play").
	    Tutorial   -> fecha o menu e deixa o jogador no lobby/tutorial.
	    Controles  -> teclas do jogo.
	    Novidades  -> o que entrou no jogo.
	- Abre ao entrar no jogo e ao voltar ao lobby (`InRace` vira false). Fora da corrida, o botão
	  "Menu" (canto superior direito) ou a tecla M reabrem.
	- Enquanto aberto, os controles do personagem ficam desligados e o fundo engole os cliques (o
	  gancho e o martelo não disparam).
]]

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Config = require(ReplicatedStorage.Shared.Config)
local Net = require(ReplicatedStorage.Shared.Net)

local menu = Config.Menu
local Attributes = Config.Attributes
local player = Players.LocalPlayer

local MenuController = {}

local BLOCK_ACTION = "MainMenuBlockControls"
local BLOCKED_KEYS: { Enum.KeyCode } = {
	Enum.KeyCode.W,
	Enum.KeyCode.A,
	Enum.KeyCode.S,
	Enum.KeyCode.D,
	Enum.KeyCode.Up,
	Enum.KeyCode.Down,
	Enum.KeyCode.Left,
	Enum.KeyCode.Right,
	Enum.KeyCode.Space,
}

local gui: ScreenGui
local fadeGui: ScreenGui
local fadeFrame: Frame
local menuButton: TextButton
local mainColumn: Frame
local panels: { [string]: Frame } = {}
local isOpen = false
local entering = false
local actionRemote: RemoteEvent? = nil
local refreshMapList: (() -> ())? = nil

-- Pequenas peças de UI ----------------------------------------------------------------------------

local function corner(parent: GuiObject, radius: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, radius)
	c.Parent = parent
end

local function stroke(parent: GuiObject, color: Color3, thickness: number, transparency: number?)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.Transparency = transparency or 0
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = parent
end

local function newLabel(text: string, size: number, font: Enum.Font, parent: Instance): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Text = text
	label.TextSize = size
	label.Font = font
	label.TextColor3 = menu.ButtonTextColor
	label.Parent = parent
	return label
end

local function tween(instance: Instance, time: number, goal: { [string]: any })
	TweenService:Create(instance, TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), goal)
		:Play()
end

-- Cópia leve do mapa feita pelo servidor (MenuService): com streaming, o workspace do cliente só tem
-- as peças perto do personagem.
local function previewSource(name: string): Instance?
	local folder = ReplicatedStorage:WaitForChild("MenuPreview", 10)
	return if folder then folder:WaitForChild(name, 10) else nil
end

-- Prévia 3D: copia local das peças de `source` dentro da caixa (min..max em X/Y) num ViewportFrame.
local function mapViewport(
	source: Instance?,
	minXY: Vector2,
	maxXY: Vector2,
	parent: GuiObject
): ViewportFrame
	local viewport = Instance.new("ViewportFrame")
	viewport.BackgroundTransparency = 1
	viewport.Size = UDim2.fromScale(1, 1)
	viewport.Ambient = Color3.fromRGB(150, 150, 165)
	viewport.LightColor = Color3.fromRGB(255, 240, 220)
	viewport.LightDirection = Vector3.new(-0.4, -1, -0.6)
	viewport.Parent = parent
	local world = Instance.new("WorldModel")
	world.Parent = viewport
	if source then
		for _, part in source:GetDescendants() do
			if not part:IsA("BasePart") or part.Transparency >= 1 then
				continue
			end
			local p = part.Position
			if p.X < minXY.X or p.X > maxXY.X or p.Y < minXY.Y or p.Y > maxXY.Y then
				continue
			end
			local copy = part:Clone()
			for _, child in copy:GetChildren() do
				if not child:IsA("DataModelMesh") and not child:IsA("Decal") then
					child:Destroy()
				end
			end
			copy.Anchored = true
			copy.Parent = world
		end
	end
	local camera = Instance.new("Camera")
	camera.FieldOfView = 40
	local center = (minXY + maxXY) / 2
	local height = maxXY.Y - minXY.Y
	local width = maxXY.X - minXY.X
	-- Enquadra a caixa toda conforme o formato do quadro (o tamanho só existe depois do layout).
	local function frame()
		local size = parent.AbsoluteSize
		local aspect = if size.Y > 0 then size.X / size.Y else 1
		local distance = math.max(height, width / aspect) / 2 / math.tan(math.rad(20)) * 1.05
		camera.CFrame =
			CFrame.lookAt(Vector3.new(center.X, center.Y, distance), Vector3.new(center.X, center.Y, 0))
	end
	frame()
	parent:GetPropertyChangedSignal("AbsoluteSize"):Connect(frame)
	camera.Parent = viewport
	viewport.CurrentCamera = camera
	return viewport
end

-- Fundo --------------------------------------------------------------------------------------------

local function buildBackground(root: Frame)
	local sky = Instance.new("Frame")
	sky.Name = "Sky"
	sky.Size = UDim2.fromScale(1, 1)
	sky.BackgroundColor3 = Color3.new(1, 1, 1)
	sky.BorderSizePixel = 0
	sky.Active = true -- engole os cliques (gancho/martelo não disparam com o menu aberto)
	sky.Parent = root
	local gradient = Instance.new("UIGradient")
	gradient.Rotation = 90
	gradient.Color = ColorSequence.new(menu.SkyTop, menu.SkyBottom)
	gradient.Parent = sky

	-- Raios de sol: pares de faixas atravessando o sol, girando devagar.
	local sunCenter = UDim2.fromScale(0.5, 0.36)
	local rays = Instance.new("Frame")
	rays.Name = "Rays"
	rays.AnchorPoint = Vector2.new(0.5, 0.5)
	rays.Position = sunCenter
	rays.Size = UDim2.fromOffset(10, 10)
	rays.BackgroundTransparency = 1
	rays.Parent = sky
	local pairsCount = math.max(1, math.floor(menu.RayCount / 2))
	for index = 1, pairsCount do
		local ray = Instance.new("Frame")
		ray.AnchorPoint = Vector2.new(0.5, 0.5)
		ray.Position = UDim2.fromScale(0.5, 0.5)
		ray.Size = UDim2.fromOffset(140, 3200)
		ray.Rotation = (index - 1) * 180 / pairsCount
		ray.BackgroundColor3 = menu.RayColor
		ray.BorderSizePixel = 0
		ray.Parent = rays
		local fade = Instance.new("UIGradient")
		fade.Rotation = 90
		fade.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.5, 0.55),
			NumberSequenceKeypoint.new(1, 1),
		})
		fade.Parent = ray
	end

	-- O mapa de verdade, com a câmera passeando (só a faixa de baixo, onde começam as etapas).
	local mapFrame = Instance.new("Frame")
	mapFrame.Name = "MapView"
	mapFrame.Size = UDim2.fromScale(1, 1)
	mapFrame.BackgroundTransparency = 1
	mapFrame.Parent = sky
	local map01 = previewSource("Map01")
	local viewport = mapViewport(map01, Vector2.new(-50, -20), Vector2.new(2000, 240), mapFrame)
	viewport.ImageTransparency = 0.15
	local camera = viewport.CurrentCamera :: Camera
	camera.FieldOfView = 50
	local started = os.clock()
	RunService.RenderStepped:Connect(function()
		if not gui.Enabled then
			return
		end
		local t = os.clock() - started
		local x = 900 + 820 * math.sin(t * menu.BackgroundPanSpeed / 820)
		camera.CFrame = CFrame.lookAt(Vector3.new(x, 70, 150), Vector3.new(x, 70, 0))
		rays.Rotation = (t * menu.RaySpeed) % 360
	end)

	-- Véu escuro embaixo (dá contraste aos botões) e o sol por cima do mapa.
	local veil = Instance.new("Frame")
	veil.Size = UDim2.fromScale(1, 1)
	veil.BackgroundColor3 = Color3.fromRGB(10, 12, 20)
	veil.BorderSizePixel = 0
	veil.Parent = sky
	local veilGradient = Instance.new("UIGradient")
	veilGradient.Rotation = 90
	veilGradient.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.45, 0.85),
		NumberSequenceKeypoint.new(1, menu.BackgroundOverlay),
	})
	veilGradient.Parent = veil

	local sun = Instance.new("Frame")
	sun.Name = "Sun"
	sun.AnchorPoint = Vector2.new(0.5, 0.5)
	sun.Position = sunCenter
	sun.Size = UDim2.fromOffset(220, 220)
	sun.BackgroundColor3 = menu.RayColor
	sun.BackgroundTransparency = 0.15
	sun.BorderSizePixel = 0
	sun.Parent = sky
	corner(sun, 110)
	stroke(sun, Color3.new(1, 1, 1), 10, 0.75)

	-- Nuvens: três bolas brancas cada, atravessando a tela devagar.
	local clouds: { { frame: Frame, speed: number } } = {}
	local random = Random.new(7)
	for index = 1, menu.CloudCount do
		local cloud = Instance.new("Frame")
		cloud.BackgroundTransparency = 1
		local scale = random:NextNumber(0.6, 1.3)
		cloud.Size = UDim2.fromOffset(160 * scale, 70 * scale)
		cloud.Position = UDim2.fromScale(random:NextNumber(0, 1), random:NextNumber(0.04, 0.5))
		cloud.Parent = sky
		for _, ball in { { 0, 0.35, 0.45 }, { 0.28, 0, 0.6 }, { 0.6, 0.25, 0.42 } } do
			local puff = Instance.new("Frame")
			puff.BackgroundColor3 = Color3.new(1, 1, 1)
			puff.BackgroundTransparency = 0.12
			puff.BorderSizePixel = 0
			puff.Position = UDim2.fromScale(ball[1], ball[2])
			puff.Size = UDim2.fromScale(ball[3], ball[3])
			puff.SizeConstraint = Enum.SizeConstraint.RelativeXX
			puff.Parent = cloud
			corner(puff, 999)
		end
		table.insert(
			clouds,
			{ frame = cloud, speed = random:NextNumber(0.006, 0.018) * (if index % 2 == 0 then 1 else 0.7) }
		)
	end
	RunService.RenderStepped:Connect(function(dt)
		if not gui.Enabled then
			return
		end
		for _, cloud in clouds do
			local position = cloud.frame.Position
			local x = position.X.Scale + cloud.speed * dt
			if x > 1.1 then
				x = -0.2
			end
			cloud.frame.Position = UDim2.fromScale(x, position.Y.Scale)
		end
	end)
end

local function buildLogo(root: Frame)
	local logo = Instance.new("Frame")
	logo.Name = "Logo"
	logo.AnchorPoint = Vector2.new(0.5, 0)
	logo.Position = UDim2.new(0.5, 0, 0, 30)
	logo.Size = UDim2.fromOffset(900, 150)
	logo.BackgroundTransparency = 1
	logo.Parent = root
	local title = newLabel(menu.Title, 86, menu.Font, logo)
	title.Size = UDim2.new(1, 0, 0, 100)
	title.TextColor3 = Color3.new(1, 1, 1)
	local titleStroke = Instance.new("UIStroke")
	titleStroke.Color = Color3.fromRGB(30, 34, 52)
	titleStroke.Thickness = 5
	titleStroke.Parent = title
	local titleGradient = Instance.new("UIGradient")
	titleGradient.Rotation = 90
	titleGradient.Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), menu.AccentColor)
	titleGradient.Parent = title
	local subtitle = newLabel(menu.Subtitle, 24, menu.Font, logo)
	subtitle.Position = UDim2.fromOffset(0, 100)
	subtitle.Size = UDim2.new(1, 0, 0, 30)
	subtitle.TextColor3 = Color3.fromRGB(255, 244, 220)
	local subStroke = Instance.new("UIStroke")
	subStroke.Color = Color3.fromRGB(30, 34, 52)
	subStroke.Thickness = 2
	subStroke.Parent = subtitle
	local started = os.clock()
	RunService.RenderStepped:Connect(function()
		if gui.Enabled then
			local t = os.clock() - started
			logo.Position = UDim2.new(0.5, 0, 0, 30 + math.sin(t * 1.6) * 5)
			logo.Rotation = math.sin(t * 0.8) * 1.2
		end
	end)
end

-- Painéis ------------------------------------------------------------------------------------------

local function showPanel(name: string?)
	for panelName, panel in panels do
		panel.Visible = panelName == name
	end
	mainColumn.Visible = name == nil
	if name == "Jogar" and refreshMapList then
		refreshMapList()
	end
end

local function newPanel(root: Frame, name: string, title: string): Frame
	local panel = Instance.new("Frame")
	panel.Name = name
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.Position = UDim2.fromScale(0.5, 0.58)
	panel.Size = UDim2.fromOffset(820, 470)
	panel.BackgroundColor3 = menu.PanelColor
	panel.BackgroundTransparency = 0.08
	panel.Visible = false
	panel.Parent = root
	corner(panel, 14)
	stroke(panel, menu.AccentColor, 2, 0.4)
	local header = newLabel(title, 30, menu.Font, panel)
	header.Position = UDim2.fromOffset(24, 12)
	header.Size = UDim2.new(1, -140, 0, 40)
	header.TextXAlignment = Enum.TextXAlignment.Left
	local back = Instance.new("TextButton")
	back.Name = "Back"
	back.AnchorPoint = Vector2.new(1, 0)
	back.Position = UDim2.new(1, -16, 0, 14)
	back.Size = UDim2.fromOffset(110, 36)
	back.BackgroundColor3 = menu.ButtonColor
	back.Font = menu.Font
	back.TextSize = 20
	back.TextColor3 = menu.ButtonTextColor
	back.Text = "Voltar"
	back.Parent = panel
	corner(back, 8)
	back.Activated:Connect(function()
		showPanel(nil)
	end)
	panels[name] = panel
	return panel
end

local function textLines(panel: Frame, lines: { { string } })
	local list = Instance.new("Frame")
	list.Position = UDim2.fromOffset(24, 70)
	list.Size = UDim2.new(1, -48, 1, -90)
	list.BackgroundTransparency = 1
	list.Parent = panel
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.Parent = list
	for _, line in lines do
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, 0, 0, 38)
		row.BackgroundColor3 = menu.ButtonColor
		row.Parent = list
		corner(row, 8)
		local left = newLabel(line[1], 20, menu.Font, row)
		left.Position = UDim2.fromOffset(14, 0)
		left.Size = UDim2.new(0, 230, 1, 0)
		left.TextXAlignment = Enum.TextXAlignment.Left
		left.TextColor3 = menu.AccentColor
		local right = newLabel(line[2], 18, menu.BodyFont, row)
		right.Position = UDim2.fromOffset(250, 0)
		right.Size = UDim2.new(1, -264, 1, 0)
		right.TextXAlignment = Enum.TextXAlignment.Left
	end
end

local function formatTime(seconds: number): string
	local minutes = math.floor(seconds / 60)
	local rest = seconds - minutes * 60
	return if minutes > 0 then string.format("%d:%05.2f", minutes, rest) else string.format("%.2f s", rest)
end

local function sessionStats(): (number, number, number?)
	local racing, inLobby, best = 0, 0, nil :: number?
	for _, other in Players:GetPlayers() do
		if other:GetAttribute(Attributes.InRace) == true then
			racing += 1
		else
			inLobby += 1
		end
		local value = other:GetAttribute(Attributes.BestTime)
		if typeof(value) == "number" and (best == nil or value < best) then
			best = value
		end
	end
	return racing, inLobby, best
end

local function closeMenu()
	if not isOpen then
		return
	end
	isOpen = false
	tween(fadeFrame, menu.FadeTime, { BackgroundTransparency = 0 })
	task.delay(menu.FadeTime, function()
		if isOpen then
			return
		end
		gui.Enabled = false
		menuButton.Visible = player:GetAttribute(Attributes.InRace) ~= true
		ContextActionService:UnbindAction(BLOCK_ACTION)
		tween(fadeFrame, menu.FadeTime, { BackgroundTransparency = 1 })
	end)
end

local function buildPlayPanel(root: Frame)
	local panel = newPanel(root, "Jogar", "Escolha o mapa")
	-- Lista à esquerda (como a lista de servidores), detalhes e "Entrar" à direita.
	local list = Instance.new("Frame")
	list.Position = UDim2.fromOffset(24, 70)
	list.Size = UDim2.new(0, 470, 1, -94)
	list.BackgroundColor3 = Color3.fromRGB(18, 21, 30)
	list.Parent = panel
	corner(list, 10)
	local headerRow = Instance.new("Frame")
	headerRow.Size = UDim2.new(1, 0, 0, 34)
	headerRow.BackgroundTransparency = 1
	headerRow.Parent = list
	local columns =
		{ { "Mapa", 0, 200 }, { "Etapas", 200, 70 }, { "Correndo", 270, 90 }, { "Recorde", 360, 110 } }
	for _, column in columns do
		local label = newLabel(column[1] :: string, 16, menu.BodyFont, headerRow)
		label.Position = UDim2.fromOffset((column[2] :: number) + 12, 0)
		label.Size = UDim2.fromOffset(column[3] :: number, 34)
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextColor3 = Color3.fromRGB(160, 168, 190)
	end

	local selected = "Map01"
	local rows: { [string]: TextButton } = {}
	local rowCells: { [string]: { TextLabel } } = {}
	local function addRow(key: string, order: number)
		local row = Instance.new("TextButton")
		row.Name = key
		row.Text = ""
		row.AutoButtonColor = false
		row.Position = UDim2.fromOffset(6, 34 + (order - 1) * 46)
		row.Size = UDim2.new(1, -12, 0, 42)
		row.BackgroundColor3 = menu.ButtonColor
		row.Parent = list
		corner(row, 8)
		local cells = {}
		for _, column in columns do
			local cell = newLabel("", 18, menu.BodyFont, row)
			cell.Position = UDim2.fromOffset((column[2] :: number) + 6, 0)
			cell.Size = UDim2.fromOffset(column[3] :: number, 42)
			cell.TextXAlignment = Enum.TextXAlignment.Left
			cell.TextTruncate = Enum.TextTruncate.AtEnd
			table.insert(cells, cell)
		end
		rows[key] = row
		rowCells[key] = cells
	end
	addRow("Map01", 1)
	addRow("Tutorial", 2)

	local details = Instance.new("Frame")
	details.Position = UDim2.fromOffset(510, 70)
	details.Size = UDim2.new(1, -534, 1, -94)
	details.BackgroundTransparency = 1
	details.Parent = panel
	local preview = Instance.new("Frame")
	preview.Size = UDim2.new(1, 0, 0, 160)
	preview.BackgroundColor3 = Color3.fromRGB(18, 21, 30)
	preview.ClipsDescendants = true
	preview.Parent = details
	corner(preview, 10)
	local description = newLabel("", 17, menu.BodyFont, details)
	description.Position = UDim2.fromOffset(0, 170)
	description.Size = UDim2.new(1, 0, 0, 120)
	description.TextWrapped = true
	description.TextXAlignment = Enum.TextXAlignment.Left
	description.TextYAlignment = Enum.TextYAlignment.Top
	local enter = Instance.new("TextButton")
	enter.Name = "Enter"
	enter.AnchorPoint = Vector2.new(0, 1)
	enter.Position = UDim2.fromScale(0, 1)
	enter.Size = UDim2.new(1, 0, 0, 56)
	enter.BackgroundColor3 = menu.AccentColor
	enter.Font = menu.Font
	enter.TextSize = 28
	enter.TextColor3 = Color3.fromRGB(30, 26, 20)
	enter.Text = "ENTRAR"
	enter.Parent = details
	corner(enter, 10)

	local previews: { [string]: Frame } = {}
	local function previewFor(key: string): Frame
		local existing = previews[key]
		if existing then
			return existing
		end
		local holder = Instance.new("Frame")
		holder.Size = UDim2.fromScale(1, 1)
		holder.BackgroundTransparency = 1
		holder.Parent = preview
		if key == "Map01" then
			mapViewport(previewSource("Map01"), Vector2.new(0, -5), Vector2.new(460, 150), holder)
		else
			local tutorial = previewSource("Tutorial")
			local pivot = if tutorial and tutorial:IsA("Model")
				then tutorial:GetPivot().Position
				else Vector3.zero
			mapViewport(
				tutorial,
				Vector2.new(pivot.X - 200, pivot.Y - 80),
				Vector2.new(pivot.X + 200, pivot.Y + 80),
				holder
			)
		end
		previews[key] = holder
		return holder
	end

	local function render()
		local racing, inLobby, best = sessionStats()
		local map = rowCells.Map01
		map[1].Text = menu.MapName
		map[2].Text = tostring(menu.MapStages)
		map[3].Text = `{racing}/{#Players:GetPlayers()}`
		map[4].Text = if best then formatTime(best) else "—"
		local tut = rowCells.Tutorial
		tut[1].Text = "Tutorial · Lobby"
		tut[2].Text = "7"
		tut[3].Text = `{inLobby}/{#Players:GetPlayers()}`
		tut[4].Text = "—"
		for key, row in rows do
			local active = key == selected
			row.BackgroundColor3 = if active then menu.AccentColor else menu.ButtonColor
			for _, cell in rowCells[key] do
				cell.TextColor3 = if active then Color3.fromRGB(30, 26, 20) else menu.ButtonTextColor
			end
		end
		for key, holder in previews do
			holder.Visible = key == selected
		end
		previewFor(selected).Visible = true
		description.Text = if selected == "Map01"
			then `{menu.MapStages} etapas de gancho, gelo e martelo. Melhor com amigos: puxe, martele e passe junto.`
			else "Aprenda o gancho, o pulo duplo e os blocos do mapa no lobby, no seu ritmo."
		enter.Text = if entering
			then "ENTRANDO..."
			elseif selected == "Map01" then "ENTRAR"
			else "IR AO TUTORIAL"
	end
	refreshMapList = render
	for key, row in rows do
		row.Activated:Connect(function()
			selected = key
			render()
		end)
	end
	enter.Activated:Connect(function()
		if entering then
			return
		end
		if selected == "Tutorial" then
			closeMenu()
			return
		end
		local remote = actionRemote
		if remote then
			entering = true
			render()
			remote:FireServer("Play")
			-- O menu fecha quando o servidor aceita (InRace vira true); se não aceitar, libera o botão.
			task.delay(4, function()
				if entering then
					entering = false
					render()
				end
			end)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			if gui.Enabled and panel.Visible then
				render()
			end
		end
	end)
end

-- Botões grandes ----------------------------------------------------------------------------------

local function bigButton(
	parent: Instance,
	name: string,
	order: number,
	onClick: () -> ()
): (TextButton, Frame)
	local size = menu.ButtonSize
	local button = Instance.new("TextButton")
	button.Name = name
	button.Text = ""
	button.AutoButtonColor = false
	button.LayoutOrder = order
	button.Size = UDim2.fromOffset(size.X, size.Y)
	button.BackgroundColor3 = menu.ButtonColor
	button.BackgroundTransparency = 0.08
	button.Parent = parent
	corner(button, 12)
	stroke(button, Color3.new(1, 1, 1), 2, 0.85)
	local scale = Instance.new("UIScale")
	scale.Parent = button
	local label = newLabel(name, 30, menu.Font, button)
	label.Position = UDim2.fromOffset(24, 0)
	label.Size = UDim2.new(0, 200, 1, 0)
	label.TextXAlignment = Enum.TextXAlignment.Left
	local art = Instance.new("Frame")
	art.Name = "Art"
	art.AnchorPoint = Vector2.new(1, 0.5)
	art.Position = UDim2.new(1, -8, 0.5, 0)
	art.Size = UDim2.new(0, 190, 1, -12)
	art.BackgroundColor3 = Color3.fromRGB(18, 21, 30)
	art.ClipsDescendants = true
	art.Parent = button
	corner(art, 8)
	button.MouseEnter:Connect(function()
		tween(button, 0.12, { BackgroundColor3 = menu.ButtonHoverColor })
		tween(label, 0.12, { TextColor3 = Color3.fromRGB(30, 26, 20) })
		tween(scale, 0.12, { Scale = menu.HoverScale })
	end)
	button.MouseLeave:Connect(function()
		tween(button, 0.12, { BackgroundColor3 = menu.ButtonColor })
		tween(label, 0.12, { TextColor3 = menu.ButtonTextColor })
		tween(scale, 0.12, { Scale = 1 })
	end)
	button.Activated:Connect(onClick)
	return button, art
end

local function keyArt(art: Frame, keys: { string })
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Padding = UDim.new(0, 6)
	layout.Parent = art
	for _, key in keys do
		local pill = newLabel(key, 15, menu.Font, art)
		pill.AutomaticSize = Enum.AutomaticSize.X
		pill.Size = UDim2.fromOffset(30, 30)
		pill.BackgroundTransparency = 0
		pill.BackgroundColor3 = Color3.fromRGB(240, 240, 245)
		pill.TextColor3 = Color3.fromRGB(30, 34, 52)
		corner(pill, 6)
		local padding = Instance.new("UIPadding")
		padding.PaddingLeft = UDim.new(0, 8)
		padding.PaddingRight = UDim.new(0, 8)
		padding.Parent = pill
	end
end

local function buildMainColumn(root: Frame)
	mainColumn = Instance.new("Frame")
	mainColumn.Name = "Main"
	mainColumn.AnchorPoint = Vector2.new(0.5, 0)
	mainColumn.Position = UDim2.new(0.5, 0, 0, 220)
	mainColumn.Size = UDim2.fromOffset(menu.ButtonSize.X + 40, 400)
	mainColumn.BackgroundTransparency = 1
	mainColumn.Parent = root
	local layout = Instance.new("UIListLayout")
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Padding = UDim.new(0, 12)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = mainColumn

	local _, playArt = bigButton(mainColumn, "Jogar", 1, function()
		showPanel("Jogar")
	end)
	mapViewport(previewSource("Map01"), Vector2.new(0, -5), Vector2.new(460, 150), playArt)
	local _, tutorialArt = bigButton(mainColumn, "Tutorial", 2, function()
		closeMenu()
	end)
	local tutorial = previewSource("Tutorial")
	local pivot = if tutorial and tutorial:IsA("Model") then tutorial:GetPivot().Position else Vector3.zero
	mapViewport(
		tutorial,
		Vector2.new(pivot.X - 200, pivot.Y - 80),
		Vector2.new(pivot.X + 200, pivot.Y + 80),
		tutorialArt
	)
	local _, controlsArt = bigButton(mainColumn, "Controles", 3, function()
		showPanel("Controles")
	end)
	keyArt(controlsArt, { "A", "D", "Espaço", "Mouse" })
	local _, newsArt = bigButton(mainColumn, "Novidades", 4, function()
		showPanel("Novidades")
	end)
	keyArt(newsArt, { "NOVO" })
end

local function buildFooter(root: Frame)
	local version = newLabel(menu.Version, 16, menu.BodyFont, root)
	version.AnchorPoint = Vector2.new(1, 1)
	version.Position = UDim2.new(1, -16, 1, -12)
	version.Size = UDim2.fromOffset(200, 20)
	version.TextXAlignment = Enum.TextXAlignment.Right
	version.TextTransparency = 0.3
	local online = newLabel("", 16, menu.BodyFont, root)
	online.AnchorPoint = Vector2.new(0, 1)
	online.Position = UDim2.new(0, 16, 1, -12)
	online.Size = UDim2.fromOffset(300, 20)
	online.TextXAlignment = Enum.TextXAlignment.Left
	online.TextTransparency = 0.2
	local function update()
		local count = #Players:GetPlayers()
		online.Text = `● {count} {if count == 1 then "jogador" else "jogadores"} neste servidor`
	end
	update()
	Players.PlayerAdded:Connect(update)
	Players.PlayerRemoving:Connect(function()
		task.defer(update)
	end)
end

-- Abrir / fechar -----------------------------------------------------------------------------------

local function openMenu()
	if isOpen then
		return
	end
	isOpen = true
	entering = false
	showPanel(nil)
	menuButton.Visible = false
	-- Trava andar/pular enquanto o menu está aberto (prioridade acima de tudo, engole as teclas).
	ContextActionService:BindActionAtPriority(BLOCK_ACTION, function()
		return Enum.ContextActionResult.Sink
	end, false, Enum.ContextActionPriority.High.Value + 100, table.unpack(BLOCKED_KEYS))
	fadeFrame.BackgroundTransparency = 0
	gui.Enabled = true
	tween(fadeFrame, menu.FadeTime, { BackgroundTransparency = 1 })
end

local function build()
	local playerGui = player:WaitForChild("PlayerGui")
	gui = Instance.new("ScreenGui")
	gui.Name = "MainMenu"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = menu.DisplayOrder
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Enabled = false
	local root = Instance.new("Frame")
	root.Name = "Root"
	root.Size = UDim2.fromScale(1, 1)
	root.BackgroundTransparency = 1
	root.Parent = gui
	local uiScale = Instance.new("UIScale")
	uiScale.Parent = root
	gui.Parent = playerGui
	-- Telas pequenas: tudo encolhe junto (o layout foi feito para ~1280x720).
	local function rescale()
		local size = workspace.CurrentCamera.ViewportSize
		uiScale.Scale = math.clamp(math.min(size.X / 1280, size.Y / 760), 0.5, 1.4)
	end
	rescale()
	workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(rescale)

	buildBackground(root)
	-- O conteúdo fica num quadro do tamanho de referência, centralizado, e é ele que escala.
	local content = Instance.new("Frame")
	content.Name = "Content"
	content.AnchorPoint = Vector2.new(0.5, 0.5)
	content.Position = UDim2.fromScale(0.5, 0.5)
	content.Size = UDim2.fromOffset(1280, 760)
	content.BackgroundTransparency = 1
	content.Parent = gui
	uiScale.Parent = content
	buildLogo(content)
	buildMainColumn(content)
	buildPlayPanel(content)
	textLines(newPanel(content, "Controles", "Controles"), {
		{ "A / D", "andar" },
		{ "Espaço", "pular (de novo no ar: pulo duplo)" },
		{ "Botão direito", "gancho (sempre disponível)" },
		{ "Botão esquerdo", "usar a arma equipada (martelo)" },
		{ "Roda do mouse", "trocar de arma" },
		{ "M", "abrir este menu (fora da corrida)" },
	})
	textLines(newPanel(content, "Novidades", "Novidades"), {
		{ "Martelo", "bata nos amigos para ajudar a passar dos obstáculos" },
		{ "Gancho em jogador", "puxe os amigos; você também é arrastado pelo peso deles" },
		{ "Pulo duplo", "vale até puxando alguém com o gancho" },
		{ "Armas", "martelo no botão esquerdo, troque pela roda do mouse" },
		{ "Menu novo", "esta tela :)" },
	})
	buildFooter(content)

	-- Transição (tela preta que some) e botão "Menu" fora da corrida.
	fadeGui = Instance.new("ScreenGui")
	fadeGui.Name = "MenuFade"
	fadeGui.ResetOnSpawn = false
	fadeGui.IgnoreGuiInset = true
	fadeGui.DisplayOrder = menu.DisplayOrder + 1
	fadeFrame = Instance.new("Frame")
	fadeFrame.Size = UDim2.fromScale(1, 1)
	fadeFrame.BackgroundColor3 = Color3.new(0, 0, 0)
	fadeFrame.BackgroundTransparency = 1
	fadeFrame.BorderSizePixel = 0
	fadeFrame.Parent = fadeGui
	fadeGui.Parent = playerGui

	local hud = Instance.new("ScreenGui")
	hud.Name = "MenuButton"
	hud.ResetOnSpawn = false
	hud.Parent = playerGui
	menuButton = Instance.new("TextButton")
	menuButton.AnchorPoint = Vector2.new(1, 0)
	menuButton.Position = UDim2.new(1, -12, 0, 12)
	menuButton.Size = UDim2.fromOffset(110, 38)
	menuButton.BackgroundColor3 = menu.ButtonColor
	menuButton.Font = menu.Font
	menuButton.TextSize = 20
	menuButton.TextColor3 = menu.ButtonTextColor
	menuButton.Text = "Menu"
	menuButton.Visible = false
	menuButton.Parent = hud
	corner(menuButton, 8)
	menuButton.Activated:Connect(openMenu)
end

function MenuController.Start()
	actionRemote = Net.get("RaceAction")
	build()

	-- Entrou na corrida (servidor aceitou o "Play" ou o portal): fecha. Voltou ao lobby: abre.
	player:GetAttributeChangedSignal(Attributes.InRace):Connect(function()
		if player:GetAttribute(Attributes.InRace) == true then
			entering = false
			menuButton.Visible = false
			closeMenu()
		else
			openMenu()
		end
	end)
	UserInputService.InputBegan:Connect(function(input: InputObject, gameProcessed: boolean)
		if
			not gameProcessed
			and input.KeyCode == Enum.KeyCode.M
			and not isOpen
			and player:GetAttribute(Attributes.InRace) ~= true
		then
			openMenu()
		end
	end)
	if player:GetAttribute(Attributes.InRace) ~= true then
		openMenu()
	end

	if RunService:IsStudio() then
		local bindable = Instance.new("BindableFunction")
		bindable.Name = "MenuDebug"
		bindable.OnInvoke = function(command: string, arg: any): any
			if command == "open" then
				openMenu()
			elseif command == "close" then
				closeMenu()
			elseif command == "panel" then
				showPanel(arg)
			elseif command == "play" then
				local remote = actionRemote
				if remote then
					remote:FireServer("Play")
				end
			end
			return { open = isOpen, enabled = gui.Enabled }
		end
		bindable.Parent = script
	end
end

return MenuController
