--!nonstrict
--[[
	MapBuilder: plugin do Studio para montar mapas 2D pintando blocos numa grade.

	Instalar/atualizar: `rojo build plugin.project.json --plugin MapBuilder.rbxm` (reabra o Studio).
	Uso: botão "MapBuilder" na aba Plugins abre a paleta. Escolha um elemento e clique/arraste no
	plano do jogo (Z = Config.Plane.Z) para pintar; "Apagar" remove o bloco clicado. Ctrl+Z desfaz
	cada traço. Os blocos vão para Workspace.Maps.<Config.MapElements.EditorModelName>.

	Os elementos (cor, tag, colisão) vêm de ReplicatedStorage.Shared.MapElements, os mesmos que o jogo
	usa: o place precisa estar aberto com o código sincronizado pelo Rojo.
]]

local ChangeHistoryService = game:GetService("ChangeHistoryService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

if RunService:IsRunning() then
	return -- não roda durante o playtest
end

local toolbar = plugin:CreateToolbar("Mapa 2D")
local toggleButton = toolbar:CreateButton("MapBuilder", "Paleta para pintar blocos do mapa 2D", "")
toggleButton.ClickableWhenViewportHidden = true

-- selene: allow(deprecated)
local widget = plugin:CreateDockWidgetPluginGui(
	"MapBuilderPalette",
	DockWidgetPluginGuiInfo.new(Enum.InitialDockState.Left, false, false, 240, 520, 220, 400)
)
widget.Title = "MapBuilder"

local function loadShared()
	local shared = ReplicatedStorage:FindFirstChild("Shared")
	local configModule = shared and shared:FindFirstChild("Config")
	local elementsModule = shared and shared:FindFirstChild("MapElements")
	if not configModule or not elementsModule then
		return nil, nil
	end
	return require(configModule), require(elementsModule)
end

local Config, MapElements = loadShared()
if not Config then
	warn(
		"[MapBuilder] ReplicatedStorage.Shared.MapElements não encontrado: abra o place com o Rojo conectado"
	)
	return
end

local settings = Config.MapElements
local planeZ = Config.Plane.Z

local state = {
	tool = "Block", -- id do elemento, "Erase" ou "Spawn"
	direction = "Up",
	grid = settings.DefaultGrid,
	painting = false,
	recording = nil,
}

-- Modelo onde se pinta (cria se não existir).
local function getModel(): Model
	local maps = workspace:FindFirstChild("Maps")
	if not maps then
		maps = Instance.new("Folder")
		maps.Name = "Maps"
		maps.Parent = workspace
	end
	local model = maps:FindFirstChild(settings.EditorModelName)
	if not model then
		model = Instance.new("Model")
		model.Name = settings.EditorModelName
		model.Parent = maps
	end
	return model
end

-- Célula da grade sob o mouse (centro no plano), ou nil.
local function cellUnderMouse(mouse: PluginMouse): Vector3?
	local ray = mouse.UnitRay
	if math.abs(ray.Direction.Z) < 1e-4 then
		return nil
	end
	local t = (planeZ - ray.Origin.Z) / ray.Direction.Z
	if t < 0 then
		return nil
	end
	local hit = ray.Origin + ray.Direction * t
	local grid = state.grid
	local cx = (math.floor(hit.X / grid) + 0.5) * grid
	local cy = (math.floor(hit.Y / grid) + 0.5) * grid
	return Vector3.new(cx, cy, planeZ)
end

local function cellKey(center: Vector3, grid: number): string
	return string.format("%g,%g,%g", center.X, center.Y, grid)
end

local function findAt(model: Model, center: Vector3): BasePart?
	-- Qualquer bloco do modelo que cubra o centro da célula (pode ter outro tamanho de grade).
	for _, child in model:GetChildren() do
		if child:IsA("BasePart") then
			local localPoint = child.CFrame:PointToObjectSpace(center)
			local half = child.Size / 2
			if math.abs(localPoint.X) < half.X and math.abs(localPoint.Y) < half.Y then
				return child
			end
		end
	end
	return nil
end

local function addArrows(part: BasePart, direction: string)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Arrows"
	gui.Face = Enum.NormalId.Back -- a câmera do jogo olha o plano a partir de +Z
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 25
	gui.LightInfluence = 0
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Text = MapElements.ARROW_TEXT
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = Color3.fromRGB(110, 125, 160)
	label.Rotation = MapElements.ARROW_ROTATION[direction] or 0
	label.Parent = gui
end

-- Quadriculado das linhas de largada/chegada (na face que a câmera do jogo vê).
local function addChecker(part: BasePart, first: Color3, second: Color3)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Checker"
	gui.Face = Enum.NormalId.Back
	gui.LightInfluence = 0
	gui.Parent = part
	local cells = MapElements.CHECKER_CELLS
	for row = 0, cells - 1 do
		for column = 0, cells - 1 do
			local square = Instance.new("Frame")
			square.BorderSizePixel = 0
			square.Size = UDim2.fromScale(1 / cells, 1 / cells)
			square.Position = UDim2.fromScale(column / cells, row / cells)
			square.BackgroundColor3 = if (row + column) % 2 == 0 then first else second
			square.Parent = gui
		end
	end
end

-- Peça de um elemento (aparência, tag e atributos), sem posição nem pai.
local function buildPart(element, grid: number, direction: string): Part
	local part = Instance.new("Part")
	part.Name = element.id
	part.Anchored = true
	part.Size = Vector3.new(grid, grid, settings.BlockDepth)
	part.Color = element.color
	part.Material = element.material
	part.Transparency = element.transparency
	part.CanCollide = element.canCollide
	part.CastShadow = element.transparency == 0
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part:SetAttribute("Element", element.id)
	if element.tag then
		CollectionService:AddTag(part, element.tag)
	end
	if element.usesDirection then
		part:SetAttribute(settings.DirectionAttribute, direction)
		addArrows(part, direction)
	end
	if element.checker then
		addChecker(part, element.color, element.checker)
	end
	return part
end

local function createBlock(model: Model, element, center: Vector3)
	local part = buildPart(element, state.grid, state.direction)
	part.CFrame = CFrame.new(center)
	part:SetAttribute("Cell", cellKey(center, state.grid))
	part.Parent = model
end

local function placeSpawn(model: Model, center: Vector3)
	for _, existing in CollectionService:GetTagged(Config.Tags.EditorSpawn) do
		existing:Destroy()
	end
	local part = Instance.new("Part")
	part.Name = "EditorSpawn"
	part.Anchored = true
	part.CanCollide = false
	part.Size = Vector3.new(state.grid, 0.4, settings.BlockDepth)
	part.CFrame = CFrame.new(center - Vector3.new(0, state.grid / 2 - 0.2, 0))
	part.Color = Color3.fromRGB(80, 220, 120)
	part.Transparency = 0.3
	part:SetAttribute("Enabled", true)
	CollectionService:AddTag(part, Config.Tags.EditorSpawn)
	part.Parent = model
end

local function paintAt(center: Vector3)
	local model = getModel()
	local existing = findAt(model, center)
	if state.tool == "Erase" then
		if existing then
			existing:Destroy()
		end
		return
	end
	if state.tool == "Spawn" then
		placeSpawn(model, center)
		return
	end
	local element = MapElements.byId[state.tool]
	if not element then
		return
	end
	if existing then
		local same = existing:GetAttribute("Element") == element.id
			and existing:GetAttribute("Cell") == cellKey(center, state.grid)
			and (
				not element.usesDirection
				or existing:GetAttribute(settings.DirectionAttribute) == state.direction
			)
		if same then
			return
		end
		existing:Destroy()
	end
	createBlock(model, element, center)
end

-- UI -----------------------------------------------------------------------------------------------

local buttons: { [string]: TextButton } = {}
local directionButtons: { [string]: TextButton } = {}
local gridButtons: { [number]: TextButton } = {}
local directionRow: Frame
local statusLabel: TextLabel

local function refreshUi()
	for id, button in buttons do
		button.BorderSizePixel = if id == state.tool then 3 else 0
	end
	for dir, button in directionButtons do
		button.BackgroundColor3 = if dir == state.direction
			then Color3.fromRGB(90, 140, 230)
			else Color3.fromRGB(60, 60, 70)
	end
	for size, button in gridButtons do
		button.BackgroundColor3 = if size == state.grid
			then Color3.fromRGB(90, 140, 230)
			else Color3.fromRGB(60, 60, 70)
	end
	local element = MapElements.byId[state.tool]
	directionRow.Visible = element ~= nil and element.usesDirection
	local name = if element then element.label elseif state.tool == "Erase" then "Apagar" else "Spawn de teste"
	statusLabel.Text = `{name} — grade {state.grid} studs\n{if element then element.description else ""}`
end

local root = Instance.new("ScrollingFrame")
root.Size = UDim2.fromScale(1, 1)
root.BackgroundColor3 = Color3.fromRGB(35, 35, 40)
root.CanvasSize = UDim2.new()
root.AutomaticCanvasSize = Enum.AutomaticSize.Y
root.ScrollBarThickness = 6
root.Parent = widget
local layout = Instance.new("UIListLayout")
layout.Padding = UDim.new(0, 4)
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Parent = root
local padding = Instance.new("UIPadding")
padding.PaddingLeft = UDim.new(0, 6)
padding.PaddingRight = UDim.new(0, 6)
padding.PaddingTop = UDim.new(0, 6)
padding.Parent = root

local order = 0
local function nextOrder(): number
	order += 1
	return order
end

local function makeButton(parent: Instance, text: string, color: Color3, height: number): TextButton
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(1, 0, 0, height)
	button.BackgroundColor3 = color
	button.BorderColor3 = Color3.fromRGB(255, 255, 255)
	button.BorderMode = Enum.BorderMode.Inset
	button.BorderSizePixel = 0
	button.Font = Enum.Font.GothamBold
	button.TextSize = 14
	button.Text = text
	local brightness = color.R * 0.3 + color.G * 0.59 + color.B * 0.11
	button.TextColor3 = if brightness > 0.6 then Color3.new(0, 0, 0) else Color3.new(1, 1, 1)
	button.LayoutOrder = nextOrder()
	button.Parent = parent
	return button
end

local function selectTool(id: string)
	state.tool = id
	plugin:Activate(true) -- volta a pintar se outra ferramenta do Studio tiver tomado o mouse
	refreshUi()
end

-- Cartões com miniatura 3D de cada bloco (como a grade da Caixa de ferramentas).
local cards = Instance.new("Frame")
cards.Size = UDim2.fromScale(1, 0)
cards.AutomaticSize = Enum.AutomaticSize.Y
cards.BackgroundTransparency = 1
cards.LayoutOrder = nextOrder()
cards.Parent = root
local grid = Instance.new("UIGridLayout")
grid.CellSize = UDim2.new(0.5, -3, 0, 104)
grid.CellPadding = UDim2.fromOffset(6, 6)
grid.SortOrder = Enum.SortOrder.LayoutOrder
grid.Parent = cards

for index, element in MapElements.list do
	local card = Instance.new("TextButton")
	card.Text = ""
	card.AutoButtonColor = true
	card.BackgroundColor3 = Color3.fromRGB(52, 52, 60)
	card.BorderColor3 = Color3.fromRGB(90, 160, 255)
	card.BorderMode = Enum.BorderMode.Inset
	card.BorderSizePixel = 0
	card.LayoutOrder = index
	card.Parent = cards

	local viewport = Instance.new("ViewportFrame")
	viewport.Size = UDim2.new(1, -8, 0, 74)
	viewport.Position = UDim2.fromOffset(4, 4)
	viewport.BackgroundColor3 = Color3.fromRGB(120, 160, 210)
	viewport.Ambient = Color3.fromRGB(200, 200, 200)
	viewport.LightColor = Color3.fromRGB(255, 255, 255)
	viewport.LightDirection = Vector3.new(-1, -2, -1)
	viewport.Active = false
	viewport.Parent = card
	local preview = buildPart(element, 4, "Up")
	preview.CFrame = CFrame.new()
	preview.Size = Vector3.new(4, 4, 4)
	preview.Parent = viewport
	local camera = Instance.new("Camera")
	camera.FieldOfView = 40
	camera.CFrame = CFrame.lookAt(Vector3.new(5, 4.5, 8), Vector3.zero)
	camera.Parent = viewport
	viewport.CurrentCamera = camera

	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, -4, 0, 22)
	label.Position = UDim2.new(0, 2, 1, -24)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.GothamBold
	label.TextSize = 13
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextTruncate = Enum.TextTruncate.AtEnd
	label.Text = element.label
	label.Parent = card

	buttons[element.id] = card
	card.Activated:Connect(function()
		selectTool(element.id)
	end)
end

directionRow = Instance.new("Frame")
directionRow.Size = UDim2.new(1, 0, 0, 30)
directionRow.BackgroundTransparency = 1
directionRow.LayoutOrder = nextOrder()
directionRow.Parent = root
local rowLayout = Instance.new("UIListLayout")
rowLayout.FillDirection = Enum.FillDirection.Horizontal
rowLayout.Padding = UDim.new(0, 4)
rowLayout.Parent = directionRow
for _, pair in { { "Up", "↑" }, { "Down", "↓" }, { "Left", "←" }, { "Right", "→" } } do
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(0.25, -3, 1, 0)
	button.Font = Enum.Font.GothamBold
	button.TextSize = 18
	button.TextColor3 = Color3.new(1, 1, 1)
	button.Text = pair[2]
	button.Parent = directionRow
	directionButtons[pair[1]] = button
	button.Activated:Connect(function()
		state.direction = pair[1]
		refreshUi()
	end)
end

local eraseButton = makeButton(root, "Apagar", Color3.fromRGB(120, 40, 40), 30)
buttons.Erase = eraseButton
eraseButton.Activated:Connect(function()
	selectTool("Erase")
end)

local spawnButton = makeButton(root, "Spawn de teste (clique no mapa)", Color3.fromRGB(40, 110, 60), 30)
buttons.Spawn = spawnButton
spawnButton.Activated:Connect(function()
	selectTool("Spawn")
end)

local testToggle = makeButton(root, "", Color3.fromRGB(60, 60, 70), 30)
local function refreshTestToggle()
	local spawn = CollectionService:GetTagged(Config.Tags.EditorSpawn)[1]
	local enabled = spawn and spawn:GetAttribute("Enabled") == true
	testToggle.Text = if not spawn
		then "Sem spawn de teste"
		elseif enabled then "Testar no editor: LIGADO"
		else "Testar no editor: desligado"
end
testToggle.Activated:Connect(function()
	local spawn = CollectionService:GetTagged(Config.Tags.EditorSpawn)[1]
	if spawn then
		ChangeHistoryService:SetWaypoint("MapBuilder antes")
		spawn:SetAttribute("Enabled", spawn:GetAttribute("Enabled") ~= true)
		ChangeHistoryService:SetWaypoint("MapBuilder spawn de teste")
	end
	refreshTestToggle()
end)

local gridRow = Instance.new("Frame")
gridRow.Size = UDim2.new(1, 0, 0, 26)
gridRow.BackgroundTransparency = 1
gridRow.LayoutOrder = nextOrder()
gridRow.Parent = root
local gridLayout = Instance.new("UIListLayout")
gridLayout.FillDirection = Enum.FillDirection.Horizontal
gridLayout.Padding = UDim.new(0, 4)
gridLayout.Parent = gridRow
for _, size in { 2, 4, 8 } do
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(1 / 3, -3, 1, 0)
	button.Font = Enum.Font.Gotham
	button.TextSize = 13
	button.TextColor3 = Color3.new(1, 1, 1)
	button.Text = `grade {size}`
	button.Parent = gridRow
	gridButtons[size] = button
	button.Activated:Connect(function()
		state.grid = size
		refreshUi()
	end)
end

local cameraButton = makeButton(root, "Câmera 2D na área", Color3.fromRGB(60, 60, 70), 26)
-- Câmera de frente para o plano do jogo (vista 2D), centrada na área do editor.
local function focusCamera2D()
	local model = getModel()
	local center = if #model:GetChildren() > 0
		then model:GetBoundingBox().Position
		else Vector3.new(0, 0, planeZ)
	local camera = workspace.CurrentCamera
	camera.CFrame =
		CFrame.lookAt(Vector3.new(center.X, center.Y, planeZ + 90), Vector3.new(center.X, center.Y, planeZ))
	camera.Focus = CFrame.new(center.X, center.Y, planeZ)
end
cameraButton.Activated:Connect(focusCamera2D)

statusLabel = Instance.new("TextLabel")
statusLabel.Size = UDim2.new(1, 0, 0, 60)
statusLabel.BackgroundTransparency = 1
statusLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
statusLabel.Font = Enum.Font.Gotham
statusLabel.TextSize = 12
statusLabel.TextWrapped = true
statusLabel.TextXAlignment = Enum.TextXAlignment.Left
statusLabel.TextYAlignment = Enum.TextYAlignment.Top
statusLabel.LayoutOrder = nextOrder()
statusLabel.Parent = root

-- Pintura --------------------------------------------------------------------------------------------

local mouse = plugin:GetMouse()
local ghost: Part? = nil
local lastKey: string? = nil

local function updateGhost()
	local center = cellUnderMouse(mouse)
	if not widget.Enabled or not center then
		if ghost then
			ghost.Parent = nil
		end
		return nil
	end
	if not ghost then
		ghost = Instance.new("Part")
		ghost.Name = "MapBuilderGhost"
		ghost.Anchored = true
		ghost.CanCollide = false
		ghost.CanQuery = false
		ghost.CanTouch = false
		ghost.Archivable = false
		ghost.Material = Enum.Material.Neon
	end
	local element = MapElements.byId[state.tool]
	ghost.Color = if element
		then element.color
		elseif state.tool == "Erase" then Color3.fromRGB(255, 60, 60)
		else Color3.fromRGB(80, 220, 120)
	ghost.Transparency = 0.6
	ghost.Size = Vector3.new(state.grid, state.grid, settings.BlockDepth + 0.2)
	ghost.CFrame = CFrame.new(center)
	ghost.Parent = workspace.CurrentCamera
	return center
end

local function paintUnderMouse()
	local center = updateGhost()
	if not center then
		return
	end
	local key = cellKey(center, state.grid) .. state.tool
	if key == lastKey then
		return
	end
	lastKey = key
	paintAt(center)
end

mouse.Button1Down:Connect(function()
	if not widget.Enabled then
		return
	end
	state.painting = true
	lastKey = nil
	state.recording = ChangeHistoryService:TryBeginRecording("MapBuilder", "Pintar blocos")
	paintUnderMouse()
end)

mouse.Button1Up:Connect(function()
	if not state.painting then
		return
	end
	state.painting = false
	if state.recording then
		ChangeHistoryService:FinishRecording(state.recording, Enum.FinishRecordingOperation.Commit)
		state.recording = nil
	end
	refreshTestToggle()
end)

mouse.Move:Connect(function()
	if state.painting then
		paintUnderMouse()
	else
		updateGhost()
	end
end)

local function setOpen(open: boolean)
	widget.Enabled = open
	toggleButton:SetActive(open)
	if open then
		plugin:Activate(true) -- o mouse do viewport passa a pintar
		refreshTestToggle()
		focusCamera2D()
	else
		plugin:Deactivate()
		if ghost then
			ghost.Parent = nil
		end
	end
end

toggleButton.Click:Connect(function()
	setOpen(not widget.Enabled)
end)
widget:GetPropertyChangedSignal("Enabled"):Connect(function()
	if not widget.Enabled then
		setOpen(false)
	end
end)
plugin.Deactivation:Connect(function()
	if widget.Enabled then
		toggleButton:SetActive(false)
	end
end)
plugin.Unloading:Connect(function()
	if ghost then
		ghost:Destroy()
	end
end)

refreshUi()
