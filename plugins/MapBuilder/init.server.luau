--!nonstrict
--[[
	MapBuilder: plugin do Studio para montar mapas 2D pintando blocos numa grade.

	Instalar/atualizar: `rojo build plugin.project.json --plugin MapBuilder.rbxm` (reabra o Studio).
	Uso: botão "MapBuilder" na aba Plugins abre a paleta. Escolha um elemento e clique/arraste no
	plano do jogo (Z = Config.Plane.Z) para pintar; "Apagar" remove o bloco clicado. Ctrl+Z desfaz
	cada traço. Os blocos vão para Workspace.Maps.<Config.MapElements.EditorModelName>.

	Os elementos (cor, tag, colisão) vêm de ReplicatedStorage.Shared.MapElements, os mesmos que o jogo
	usa: o place precisa estar aberto com o código sincronizado pelo Rojo.

	Exportar / Importar: o mapa do Editor como dados (`maps/<nome>/tiles.json`, formato
	race-and-escape/tiles@1 de tools/mapkit/README.md). Seção "Importar / exportar" abaixo.
]]

local ChangeHistoryService = game:GetService("ChangeHistoryService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local StudioService = game:GetService("StudioService")

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
	local logic = shared and shared:FindFirstChild("Logic")
	local mergeModule = logic and logic:FindFirstChild("GridMerge")
	if not configModule or not elementsModule or not mergeModule then
		return nil, nil, nil
	end
	return require(configModule), require(elementsModule), require(mergeModule)
end

local Config, MapElements, GridMerge = loadShared()
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

--[[
	Blocos contínuos: cada traço pinta células de UNIT studs e, ao soltar o mouse, `mergeModel` junta
	células vizinhas iguais (mesmo elemento e direção) em retângulos de uma peça só. Assim blocos
	translúcidos lado a lado não mostram as "paredinhas" entre eles. Apagar (ou pintar) dentro de uma
	peça unida a divide de volta em células antes.
]]
local UNIT = 2 -- studs: menor célula (= menor grade); blocos maiores são vários UNITs
local DECOR_TILE = 4 -- studs: setas e textos se repetem a cada bloco deste tamanho

local function cellKey(ix: number, iy: number): string
	return `{ix},{iy}`
end

local function isElementPart(instance: Instance): boolean
	return instance:IsA("BasePart") and typeof(instance:GetAttribute("Element")) == "string"
end

-- Células (índices) cobertas por uma peça alinhada à grade.
local function coveredCells(part: BasePart): (number, number, number, number)
	local ix = math.round((part.Position.X - part.Size.X / 2) / UNIT)
	local iy = math.round((part.Position.Y - part.Size.Y / 2) / UNIT)
	return ix, iy, math.max(1, math.round(part.Size.X / UNIT)), math.max(1, math.round(part.Size.Y / UNIT))
end

local function newSurface(part: BasePart, name: string): SurfaceGui
	local gui = Instance.new("SurfaceGui")
	gui.Name = name
	gui.Face = Enum.NormalId.Back -- a câmera do jogo olha o plano a partir de +Z
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 25
	gui.LightInfluence = 0
	gui.Parent = part
	return gui
end

-- Desenhos na face, repetidos ao longo da peça (que pode ser vários blocos unidos).
local function decorate(part: BasePart, element, direction: string)
	local size = part.Size
	if element.checker then
		local gui = newSurface(part, "Checker")
		local columns = math.max(1, math.round(size.X / UNIT))
		local rows = math.max(1, math.round(size.Y / UNIT))
		for row = 0, rows - 1 do
			for column = 0, columns - 1 do
				local square = Instance.new("Frame")
				square.BorderSizePixel = 0
				square.Size = UDim2.fromScale(1 / columns, 1 / rows)
				square.Position = UDim2.fromScale(column / columns, row / rows)
				square.BackgroundColor3 = if (row + column) % 2 == 0 then element.color else element.checker
				square.Parent = gui
			end
		end
	end
	local text = if element.usesDirection then MapElements.ARROW_TEXT else element.text
	if text then
		local gui = newSurface(part, "Label")
		local columns = math.max(1, math.floor(size.X / DECOR_TILE))
		local rows = math.max(1, math.floor(size.Y / DECOR_TILE))
		for row = 0, rows - 1 do
			for column = 0, columns - 1 do
				local label = Instance.new("TextLabel")
				label.BackgroundTransparency = 1
				label.Size = UDim2.fromScale(1 / columns, 1 / rows)
				label.Position = UDim2.fromScale(column / columns, row / rows)
				label.Text = text
				label.TextScaled = true
				label.Font = Enum.Font.GothamBold
				label.TextColor3 = if element.usesDirection
					then Color3.fromRGB(110, 125, 160)
					else Color3.fromRGB(70, 75, 90)
				label.Rotation = if element.usesDirection
					then MapElements.ARROW_ROTATION[direction] or 0
					else 0
				label.Parent = gui
			end
		end
	end
end

-- Peça de um elemento (aparência, tag e atributos), sem posição nem pai.
local function buildPart(element, sizeX: number, sizeY: number, direction: string): Part
	local part = Instance.new("Part")
	part.Name = element.id
	part.Anchored = true
	part.Size = Vector3.new(sizeX, sizeY, settings.BlockDepth)
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
	end
	decorate(part, element, direction)
	return part
end

-- Peça retangular de células [ix, ix+w) x [iy, iy+h).
local function placeRect(
	model: Model,
	elementId: string,
	direction: string,
	ix: number,
	iy: number,
	w: number,
	h: number
): BasePart?
	local element = MapElements.byId[elementId]
	if not element then
		return nil
	end
	local part = buildPart(element, w * UNIT, h * UNIT, direction)
	part.CFrame = CFrame.new((ix + w / 2) * UNIT, (iy + h / 2) * UNIT, planeZ)
	part.Parent = model
	return part
end

local function partDirection(part: BasePart): string
	local direction = part:GetAttribute(settings.DirectionAttribute)
	return if typeof(direction) == "string" then direction else "Up"
end

-- Tira a peça do mapa SEM `Destroy()`: o Ctrl+Z (ChangeHistoryService) não consegue desfazer um
-- `Destroy()`, então desfazer um traço removia as peças novas sem trazer as antigas de volta.
local function remove(instance: Instance)
	instance.Parent = nil
end

-- Índice célula -> peça durante um traço (peças unidas aparecem em várias células).
local cellIndex: { [string]: BasePart } = {}

local function indexModel(model: Model)
	table.clear(cellIndex)
	for _, child in model:GetChildren() do
		if isElementPart(child) then
			local ix, iy, w, h = coveredCells(child :: BasePart)
			for x = ix, ix + w - 1 do
				for y = iy, iy + h - 1 do
					cellIndex[cellKey(x, y)] = child :: BasePart
				end
			end
		end
	end
end

-- Divide uma peça unida em peças de uma célula (para apagar/trocar só parte dela).
local function explode(model: Model, part: BasePart)
	local elementId = part:GetAttribute("Element") :: string
	local direction = partDirection(part)
	local ix, iy, w, h = coveredCells(part)
	remove(part)
	for x = ix, ix + w - 1 do
		for y = iy, iy + h - 1 do
			local key = cellKey(x, y)
			cellIndex[key] = placeRect(model, elementId, direction, x, y, 1, 1)
		end
	end
end

local function paintCell(model: Model, x: number, y: number, element)
	local key = cellKey(x, y)
	local existing = cellIndex[key]
	if existing and not existing.Parent then
		existing = nil
	end
	if existing and (existing.Size.X > UNIT + 0.01 or existing.Size.Y > UNIT + 0.01) then
		explode(model, existing)
		existing = cellIndex[key]
	end
	if existing then
		local same = element ~= nil
			and existing:GetAttribute("Element") == element.id
			and (not element.usesDirection or partDirection(existing) == state.direction)
		if same then
			return
		end
		remove(existing)
		cellIndex[key] = nil
	end
	if element then
		cellIndex[key] = placeRect(model, element.id, state.direction, x, y, 1, 1)
	end
end

-- Junta células vizinhas iguais (mesmo elemento e direção) em peças retangulares (Shared.Logic.GridMerge).
local function mergeModel(model: Model)
	local cells = {}
	for _, child in model:GetChildren() do
		if isElementPart(child) then
			local part = child :: BasePart
			local kind = `{part:GetAttribute("Element")}|{partDirection(part)}`
			local ix, iy, w, h = coveredCells(part)
			for x = ix, ix + w - 1 do
				for y = iy, iy + h - 1 do
					table.insert(cells, { x = x, y = y, kind = kind })
				end
			end
			remove(part)
		end
	end
	for _, rect in GridMerge.merge(cells) do
		local elementId, direction = string.match(rect.kind, "^(.-)|(.*)$")
		placeRect(model, elementId :: string, direction :: string, rect.x, rect.y, rect.w, rect.h)
	end
	table.clear(cellIndex)
end

local function placeSpawn(model: Model, center: Vector3, size: number?)
	local side = size or state.grid
	for _, existing in CollectionService:GetTagged(Config.Tags.EditorSpawn) do
		remove(existing)
	end
	local part = Instance.new("Part")
	part.Name = "EditorSpawn"
	part.Anchored = true
	part.CanCollide = false
	part.Size = Vector3.new(side, 0.4, settings.BlockDepth)
	part.CFrame = CFrame.new(center - Vector3.new(0, side / 2 - 0.2, 0))
	part.Color = Color3.fromRGB(80, 220, 120)
	part.Transparency = 0.3
	part:SetAttribute("Enabled", true)
	CollectionService:AddTag(part, Config.Tags.EditorSpawn)
	part.Parent = model
end

-- Pinta (ou apaga) todas as células do pincel (grade atual) em volta de `center`.
local function paintAt(center: Vector3)
	local model = getModel()
	if state.tool == "Spawn" then
		placeSpawn(model, center)
		return
	end
	local element = MapElements.byId[state.tool]
	if not element and state.tool ~= "Erase" then
		return
	end
	local half = state.grid / 2
	if state.tool == "Erase" then
		-- O spawn de teste não é bloco de elemento: apaga se o pincel encostar nele.
		for _, spawn in CollectionService:GetTagged(Config.Tags.EditorSpawn) do
			if spawn:IsA("BasePart") then
				local offset = spawn.Position - center
				if
					math.abs(offset.X) < spawn.Size.X / 2 + half
					and math.abs(offset.Y) < spawn.Size.Y / 2 + half
				then
					remove(spawn)
				end
			end
		end
	end
	local x0 = math.round((center.X - half) / UNIT)
	local y0 = math.round((center.Y - half) / UNIT)
	local count = math.max(1, math.round(state.grid / UNIT))
	for x = x0, x0 + count - 1 do
		for y = y0, y0 + count - 1 do
			paintCell(model, x, y, element)
		end
	end
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
	local preview = buildPart(element, 4, 4, "Up")
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

local mergeButton = makeButton(root, "Unir blocos iguais agora", Color3.fromRGB(60, 60, 70), 26)
mergeButton.Activated:Connect(function()
	local recording = ChangeHistoryService:TryBeginRecording("MapBuilder", "Unir blocos")
	mergeModel(getModel())
	if recording then
		ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit)
	end
end)

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

-- Importar / exportar ----------------------------------------------------------------------------
--[[
	Mapa como dados (ADR 0052): grade `race-and-escape/tiles@1`, a mesma de tools/mapkit/tiles.py
	(formato em tools/mapkit/README.md). Célula (i, j): i da esquerda para a direita, j de BAIXO
	para cima; `rows[1]` é a linha mais alta. Exportar escreve o JSON com a mesma ordem e o mesmo
	espaçamento do Python (diff limpo). tools/mapkit/export_editor.luau repete a exportação para o
	Command Bar / MCP: mudou aqui, mude lá.
]]

local TILES_FORMAT = "race-and-escape/tiles@1"
local LEGEND_ORDER = { ".", "#", "x", "h", "f", "u", "o", "k", "g", "S", "F", "s", "e", "c", "R" }
local LEGEND: { [string]: string } = {
	["#"] = "Block",
	x = "Unhookable",
	h = "HookThrough",
	f = "Freeze",
	u = "Unfreeze",
	o = "OneWay",
	k = "Kill",
	g = "HookOnce",
	S = "StartLine",
	F = "FinishLine",
	s = "SoloStart",
	e = "SoloEnd",
	c = "Checkpoint",
	R = "RaceStart",
}
local LEGEND_CHAR: { [string]: string } = {}
for char, id in LEGEND do
	LEGEND_CHAR[id] = char
end
local OUTPUT_CHUNK = 8000 -- caracteres por print no Output (quebra só entre linhas do JSON)

local function jsonString(value: string): string
	local escaped = string.gsub(value, '[%c"\\]', function(char)
		if char == '"' then
			return '\\"'
		elseif char == "\\" then
			return "\\\\"
		elseif char == "\n" then
			return "\\n"
		elseif char == "\t" then
			return "\\t"
		end
		return string.format("\\u%04x", string.byte(char))
	end)
	return `"{escaped}"`
end

-- Lê o Editor e monta o JSON do formato. Peças unidas viram as células que cobrem.
local function exportTiles(model: Model): (string, number)
	local cells: { [string]: string } = {}
	local directions: { [string]: string } = {}
	local minX, minY, maxX, maxY = math.huge, math.huge, -math.huge, -math.huge
	local function include(x: number, y: number)
		minX, minY = math.min(minX, x), math.min(minY, y)
		maxX, maxY = math.max(maxX, x), math.max(maxY, y)
	end
	local count = 0
	for _, child in model:GetChildren() do
		if isElementPart(child) and LEGEND_CHAR[child:GetAttribute("Element")] then
			local part = child :: BasePart
			local elementId = part:GetAttribute("Element") :: string
			local ix, iy, w, h = coveredCells(part)
			for x = ix, ix + w - 1 do
				for y = iy, iy + h - 1 do
					local key = cellKey(x, y)
					if not cells[key] then
						count += 1
					end
					cells[key] = elementId
					if elementId == "OneWay" then
						directions[key] = partDirection(part)
					end
					include(x, y)
				end
			end
		end
	end
	local spawnCell: { number }? = nil
	local spawnPart = CollectionService:GetTagged(Config.Tags.EditorSpawn)[1]
	if spawnPart and spawnPart:IsA("BasePart") and spawnPart:IsDescendantOf(model) then
		-- O pé fica na base da peça do spawn (placeSpawn): célula que contém essa base.
		local sx = math.floor(spawnPart.Position.X / UNIT)
		local sy = math.floor((spawnPart.Position.Y - spawnPart.Size.Y / 2 + 0.01) / UNIT)
		include(sx, sy)
		spawnCell = { sx, sy }
	end
	if minX == math.huge then
		minX, minY, maxX, maxY = 0, 0, -1, -1
	end
	local width, height = maxX - minX + 1, maxY - minY + 1

	local lines = {
		"{",
		` "format": {jsonString(TILES_FORMAT)},`,
		` "name": {jsonString(model.Name)},`,
		` "source": {jsonString(`MapBuilder ({model:GetFullName()})`)},`,
		` "cell": {UNIT},`,
		` "origin": [{minX * UNIT}, {minY * UNIT}],`,
		` "width": {width},`,
		` "height": {height},`,
		` "legend": \{`,
	}
	for index, char in LEGEND_ORDER do
		local id = LEGEND[char]
		local value = if id then jsonString(id) else "null"
		local comma = if index < #LEGEND_ORDER then "," else ""
		table.insert(lines, `  {jsonString(char)}: {value}{comma}`)
	end
	table.insert(lines, " },")
	table.insert(
		lines,
		if spawnCell then ` "spawn": [{spawnCell[1] - minX}, {spawnCell[2] - minY}],` else ` "spawn": null,`
	)
	local directionLines = {}
	for y = minY, maxY do
		for x = minX, maxX do
			local direction = directions[cellKey(x, y)]
			if direction then
				table.insert(directionLines, `  "{x - minX},{y - minY}": {jsonString(direction)}`)
			end
		end
	end
	if #directionLines == 0 then
		table.insert(lines, ` "directions": \{\},`)
	else
		table.insert(lines, ` "directions": \{`)
		table.insert(lines, table.concat(directionLines, ",\n"))
		table.insert(lines, " },")
	end
	table.insert(lines, ` "attributes": \{\},`)
	if height <= 0 then
		table.insert(lines, ` "rows": []`)
	else
		table.insert(lines, ` "rows": [`)
		local rows = {}
		for y = maxY, minY, -1 do
			local chars = table.create(width)
			for x = minX, maxX do
				local id = cells[cellKey(x, y)]
				table.insert(chars, if id then LEGEND_CHAR[id] else ".")
			end
			table.insert(rows, `  "{table.concat(chars)}"`)
		end
		table.insert(lines, table.concat(rows, ",\n"))
		table.insert(lines, " ]")
	end
	table.insert(lines, "}")
	return table.concat(lines, "\n") .. "\n", count
end

local function printChunked(text: string)
	local chunk = {}
	local size = 0
	local function flush()
		if #chunk > 0 then
			print(table.concat(chunk, "\n"))
			table.clear(chunk)
			size = 0
		end
	end
	for line in string.gmatch(text, "[^\n]+") do
		if size + #line > OUTPUT_CHUNK then
			flush()
		end
		table.insert(chunk, line)
		size += #line + 1
	end
	flush()
end

type ImportPlan = {
	name: string,
	cells: { any }, -- GridMerge.Cell
	spawn: Vector3?,
	skipped: { [string]: number },
	warnings: { string },
}

-- Lê o JSON e monta a lista de células (índices de UNIT studs no mundo) sem mexer no mapa.
local function planImport(text: string): (ImportPlan?, string?)
	local ok, data = pcall(function()
		return HttpService:JSONDecode(text)
	end)
	if not ok or typeof(data) ~= "table" then
		return nil, "JSON inválido"
	end
	if data.format ~= TILES_FORMAT then
		return nil, `formato {tostring(data.format)} (esperado {TILES_FORMAT})`
	end
	local cell = tonumber(data.cell) or UNIT
	local scale = math.round(cell / UNIT)
	if scale < 1 or math.abs(scale * UNIT - cell) > 1e-6 then
		return nil, `cell = {cell}: precisa ser múltiplo de {UNIT} studs`
	end
	local origin = data.origin or { 0, 0 }
	local ox = math.round((tonumber(origin[1]) or 0) / UNIT)
	local oy = math.round((tonumber(origin[2]) or 0) / UNIT)
	local warnings = {}
	if
		math.abs(ox * UNIT - (tonumber(origin[1]) or 0)) > 1e-6
		or math.abs(oy * UNIT - (tonumber(origin[2]) or 0)) > 1e-6
	then
		table.insert(warnings, `origem arredondada para a grade de {UNIT} studs`)
	end
	-- JSON null some na decodificação: caractere fora da legenda = vazio.
	local legend = if typeof(data.legend) == "table" then data.legend else LEGEND
	local directions = if typeof(data.directions) == "table" then data.directions else {}
	local rows = if typeof(data.rows) == "table" then data.rows else {}
	local height = #rows
	local cells = {}
	local skipped: { [string]: number } = {}
	for r, row in rows do
		local j = height - r
		for i = 1, #row do
			local id = legend[string.sub(row, i, i)]
			if typeof(id) ~= "string" then
				continue
			end
			local element = MapElements.byId[id]
			if not element then
				skipped[id] = (skipped[id] or 0) + 1
				continue
			end
			local direction = "Up"
			if element.usesDirection then
				local given = directions[`{i - 1},{j}`]
				direction = if MapElements.isDirection(given) then given else "Up"
			end
			local kind = `{id}|{direction}`
			for a = 0, scale - 1 do
				for b = 0, scale - 1 do
					table.insert(cells, { x = ox + (i - 1) * scale + a, y = oy + j * scale + b, kind = kind })
				end
			end
		end
	end
	if typeof(data.collide) == "table" and next(data.collide) then
		table.insert(warnings, "`collide` ignorado: o MapBuilder monta cada elemento com a colisão padrão")
	end
	if typeof(data.attributes) == "table" and next(data.attributes) then
		table.insert(
			warnings,
			"`attributes` ignorado (Order, RequiresHookLevel...): o MapBuilder não guarda atributos"
		)
	end
	local spawn: Vector3? = nil
	if typeof(data.spawn) == "table" and tonumber(data.spawn[1]) and tonumber(data.spawn[2]) then
		local sx = ox + data.spawn[1] * scale
		local sy = oy + data.spawn[2] * scale
		spawn = Vector3.new((sx + 0.5) * UNIT, (sy + 0.5) * UNIT, planeZ)
	end
	local name = if typeof(data.name) == "string" then data.name else "?"
	return { name = name, cells = cells, spawn = spawn, skipped = skipped, warnings = warnings }, nil
end

-- Apaga o Editor e pinta o plano (um passo só no Ctrl+Z).
local function applyImport(plan: ImportPlan)
	local model = getModel()
	local recording = ChangeHistoryService:TryBeginRecording("MapBuilder", "Importar mapa")
	for _, child in model:GetChildren() do
		remove(child)
	end
	for _, rect in GridMerge.merge(plan.cells) do
		local elementId, direction = string.match(rect.kind, "^(.-)|(.*)$")
		placeRect(model, elementId :: string, direction :: string, rect.x, rect.y, rect.w, rect.h)
	end
	if plan.spawn then
		placeSpawn(model, plan.spawn, UNIT)
	end
	table.clear(cellIndex)
	if recording then
		ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit)
	end
end

local ioTitle = Instance.new("TextLabel")
ioTitle.Size = UDim2.new(1, 0, 0, 20)
ioTitle.BackgroundTransparency = 1
ioTitle.Font = Enum.Font.GothamBold
ioTitle.TextSize = 13
ioTitle.TextColor3 = Color3.fromRGB(220, 220, 220)
ioTitle.TextXAlignment = Enum.TextXAlignment.Left
ioTitle.Text = "Mapa como dados (tiles.json)"
ioTitle.LayoutOrder = nextOrder()
ioTitle.Parent = root

local exportButton = makeButton(root, "Exportar", Color3.fromRGB(50, 90, 140), 26)
local importFileButton = makeButton(root, "Importar arquivo .json", Color3.fromRGB(50, 90, 140), 26)
local importTextButton = makeButton(root, "Importar do texto colado", Color3.fromRGB(60, 60, 70), 26)

local ioBox = Instance.new("TextBox")
ioBox.Size = UDim2.new(1, 0, 0, 140)
ioBox.BackgroundColor3 = Color3.fromRGB(25, 25, 30)
ioBox.BorderSizePixel = 0
ioBox.ClipsDescendants = true
ioBox.ClearTextOnFocus = false
ioBox.TextEditable = true
ioBox.MultiLine = true
ioBox.TextWrapped = false
ioBox.TextXAlignment = Enum.TextXAlignment.Left
ioBox.TextYAlignment = Enum.TextYAlignment.Top
ioBox.Font = Enum.Font.Code
ioBox.TextSize = 11
ioBox.TextColor3 = Color3.fromRGB(210, 220, 210)
ioBox.PlaceholderText = "Exportar mostra o JSON aqui (Ctrl+A, Ctrl+C). Para importar, cole o JSON aqui."
ioBox.PlaceholderColor3 = Color3.fromRGB(120, 120, 130)
ioBox.Text = ""
ioBox.LayoutOrder = nextOrder()
ioBox.Parent = root

local confirmFrame = Instance.new("Frame")
confirmFrame.Size = UDim2.fromScale(1, 0)
confirmFrame.AutomaticSize = Enum.AutomaticSize.Y
confirmFrame.BackgroundColor3 = Color3.fromRGB(70, 40, 40)
confirmFrame.BorderSizePixel = 0
confirmFrame.Visible = false
confirmFrame.LayoutOrder = nextOrder()
confirmFrame.Parent = root
local confirmLayout = Instance.new("UIListLayout")
confirmLayout.Padding = UDim.new(0, 4)
confirmLayout.SortOrder = Enum.SortOrder.LayoutOrder
confirmLayout.Parent = confirmFrame
local confirmLabel = Instance.new("TextLabel")
confirmLabel.Size = UDim2.fromScale(1, 0)
confirmLabel.AutomaticSize = Enum.AutomaticSize.Y
confirmLabel.BackgroundTransparency = 1
confirmLabel.Font = Enum.Font.Gotham
confirmLabel.TextSize = 12
confirmLabel.TextWrapped = true
confirmLabel.TextColor3 = Color3.new(1, 1, 1)
confirmLabel.TextXAlignment = Enum.TextXAlignment.Left
confirmLabel.LayoutOrder = nextOrder()
confirmLabel.Parent = confirmFrame
local confirmButton = makeButton(confirmFrame, "Apagar o Editor e importar", Color3.fromRGB(160, 50, 50), 26)
local cancelButton = makeButton(confirmFrame, "Cancelar", Color3.fromRGB(60, 60, 70), 26)

local ioStatus = Instance.new("TextLabel")
ioStatus.Size = UDim2.fromScale(1, 0)
ioStatus.AutomaticSize = Enum.AutomaticSize.Y
ioStatus.BackgroundTransparency = 1
ioStatus.Font = Enum.Font.Gotham
ioStatus.TextSize = 12
ioStatus.TextWrapped = true
ioStatus.TextColor3 = Color3.fromRGB(200, 200, 200)
ioStatus.TextXAlignment = Enum.TextXAlignment.Left
ioStatus.Text = ""
ioStatus.LayoutOrder = nextOrder()
ioStatus.Parent = root

local pendingPlan: ImportPlan? = nil

local function finishImport(plan: ImportPlan)
	applyImport(plan)
	local skipped = {}
	for id, n in plan.skipped do
		table.insert(skipped, `{id} {n}`)
	end
	table.sort(skipped)
	local message = `Importado "{plan.name}": {#plan.cells} células`
	if #skipped > 0 then
		message ..= `; sem elemento no MapBuilder (ficaram de fora): {table.concat(skipped, ", ")}`
	end
	for _, warning in plan.warnings do
		message ..= `\n{warning}`
	end
	ioStatus.Text = message
	print(`[MapBuilder] {message}`)
	refreshTestToggle()
	focusCamera2D()
end

local function startImport(text: string)
	local plan, err = planImport(text)
	if not plan then
		ioStatus.Text = `Importar: {err}`
		warn(`[MapBuilder] importar: {err}`)
		return
	end
	local existing = #getModel():GetChildren()
	if existing == 0 then
		finishImport(plan)
		return
	end
	pendingPlan = plan
	confirmLabel.Text =
		`Importar "{plan.name}" ({#plan.cells} células) apaga as {existing} peças de Workspace.Maps.{settings.EditorModelName}. Ctrl+Z desfaz.`
	confirmFrame.Visible = true
end

confirmButton.Activated:Connect(function()
	local plan = pendingPlan
	pendingPlan = nil
	confirmFrame.Visible = false
	if plan then
		finishImport(plan)
	end
end)
cancelButton.Activated:Connect(function()
	pendingPlan = nil
	confirmFrame.Visible = false
	ioStatus.Text = "Importação cancelada"
end)

exportButton.Activated:Connect(function()
	local text, count = exportTiles(getModel())
	ioBox.Text = text
	ioStatus.Text =
		`Exportado: {count} células, {#text} caracteres. Copie da caixa (Ctrl+A, Ctrl+C) e salve em maps/<nome>/tiles.json; também está no Output.`
	print(`[MapBuilder] exportar: {count} células, {#text} caracteres (JSON abaixo)`)
	printChunked(text)
end)

importFileButton.Activated:Connect(function()
	local ok, file = pcall(function()
		return StudioService:PromptImportFileAsync({ "json" })
	end)
	if not ok then
		ioStatus.Text =
			'Não deu para abrir o seletor de arquivo; cole o JSON na caixa e use "Importar do texto colado".'
		warn(`[MapBuilder] PromptImportFileAsync falhou: {file}`)
		return
	end
	if not file then
		ioStatus.Text = "Nenhum arquivo escolhido"
		return
	end
	local readOk, text = pcall(function()
		return (file :: any):GetBinaryContents()
	end)
	if not readOk then
		ioStatus.Text = `Não deu para ler o arquivo: {text}`
		return
	end
	startImport(text)
end)

importTextButton.Activated:Connect(function()
	if ioBox.Text == "" then
		ioStatus.Text = "Cole o JSON na caixa primeiro"
		return
	end
	startImport(ioBox.Text)
end)

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
	local key = `{center.X},{center.Y},{state.grid},{state.tool}`
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
	indexModel(getModel())
	paintUnderMouse()
end)

mouse.Button1Up:Connect(function()
	if not state.painting then
		return
	end
	state.painting = false
	mergeModel(getModel()) -- junta os blocos iguais vizinhos (design contínuo)
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
