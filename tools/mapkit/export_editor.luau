--!strict
--[[
	Exporta Workspace.Maps.Editor (o que o MapBuilder pinta) no formato race-and-escape/tiles@1 e
	RETORNA o JSON (string). Só lê, não muda nada no place.

	Uso: colar no Command Bar do Studio (modo Edit) ou rodar pelo MCP `execute_luau`; salvar o
	retorno em maps/<nome>/tiles.json. Formato em tools/mapkit/README.md.

	A lógica é a mesma do botão "Exportar" do plugin (plugins/MapBuilder/init.server.luau,
	`exportTiles`), duplicada para não depender do plugin instalado: mudou lá, mude aqui. O nome do
	modelo, do atributo de direção e da tag do spawn vêm do Config quando ele está no place (Rojo).
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UNIT = 2 -- studs: célula do MapBuilder
local MODEL_NAME, DIRECTION_ATTRIBUTE, SPAWN_TAG = "Editor", "Direction", "EditorSpawn"
local shared = ReplicatedStorage:FindFirstChild("Shared")
local configModule = shared and shared:FindFirstChild("Config")
if configModule and configModule:IsA("ModuleScript") then
	local Config = (require :: any)(configModule)
	MODEL_NAME = Config.MapElements.EditorModelName
	DIRECTION_ATTRIBUTE = Config.MapElements.DirectionAttribute
	SPAWN_TAG = Config.Tags.EditorSpawn
end

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

local function jsonString(value: string): string
	local escaped = string.gsub(value, '[%c"\\]', function(char: string): string
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

local function cellKey(x: number, y: number): string
	return `{x},{y}`
end

local maps = workspace:FindFirstChild("Maps")
local model = maps and maps:FindFirstChild(MODEL_NAME)
if not model then
	return `sem Workspace.Maps.{MODEL_NAME}`
end

local cells: { [string]: string } = {}
local directions: { [string]: string } = {}
local minX, minY, maxX, maxY = math.huge, math.huge, -math.huge, -math.huge
local function include(x: number, y: number)
	minX, minY = math.min(minX, x), math.min(minY, y)
	maxX, maxY = math.max(maxX, x), math.max(maxY, y)
end

for _, child in model:GetChildren() do
	local elementId = child:GetAttribute("Element")
	if not child:IsA("BasePart") or typeof(elementId) ~= "string" or not LEGEND_CHAR[elementId] then
		continue
	end
	-- Peça unida: cobre várias células de UNIT studs (mesma conta do `coveredCells` do plugin).
	local ix = math.round((child.Position.X - child.Size.X / 2) / UNIT)
	local iy = math.round((child.Position.Y - child.Size.Y / 2) / UNIT)
	local w = math.max(1, math.round(child.Size.X / UNIT))
	local h = math.max(1, math.round(child.Size.Y / UNIT))
	local direction = child:GetAttribute(DIRECTION_ATTRIBUTE)
	for x = ix, ix + w - 1 do
		for y = iy, iy + h - 1 do
			local key = cellKey(x, y)
			cells[key] = elementId
			if elementId == "OneWay" then
				directions[key] = if typeof(direction) == "string" then direction else "Up"
			end
			include(x, y)
		end
	end
end

local spawnCell: { number }? = nil
local spawnPart = CollectionService:GetTagged(SPAWN_TAG)[1]
if spawnPart and spawnPart:IsA("BasePart") and spawnPart:IsDescendantOf(model) then
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
	` "format": "race-and-escape/tiles@1",`,
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
	table.insert(lines, `  {jsonString(char)}: {value}{if index < #LEGEND_ORDER then "," else ""}`)
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
return table.concat(lines, "\n") .. "\n"
