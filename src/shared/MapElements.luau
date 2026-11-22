--!strict
--[[
	Elementos de montagem de mapa: aparência e regras de cada bloco que o plugin MapBuilder pinta.
	Fonte única para o plugin (cria as peças) e para quem precisa saber o que um elemento é.

	O comportamento vem das tags (`Config.Tags`): ZoneService (freeze, unfreeze, morte),
	OneWayController (mão única), HookController/HookSurface (unhookable, hookthrough).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)

export type Direction = "Up" | "Down" | "Left" | "Right"

export type Element = {
	id: string,
	label: string, -- nome no plugin
	description: string,
	tag: string?, -- tag do CollectionService (nil = bloco padrão)
	color: Color3,
	transparency: number,
	material: Enum.Material,
	canCollide: boolean,
	usesDirection: boolean, -- mão única: guarda `Config.MapElements.DirectionAttribute`
	checker: Color3?, -- segunda cor do quadriculado (linhas de largada/chegada); nil = sem desenho
	text: string?, -- texto desenhado na face (ex.: linhas do solo)
}

local Tags = Config.Tags

local MapElements = {}

MapElements.list = table.freeze({
	{
		id = "Block",
		label = "Bloco",
		description = "Terreno sólido; o gancho prende",
		tag = nil,
		color = Color3.fromRGB(150, 151, 108), -- oliva (medido no vídeo de referência)
		transparency = 0,
		material = Enum.Material.SmoothPlastic,
		canCollide = true,
		usesDirection = false,
	},
	{
		id = "Unhookable",
		label = "Unhookable",
		description = "Sólido; o gancho não prende",
		tag = Tags.NoHook,
		color = Color3.fromRGB(103, 128, 154), -- xadrez azul-acinzentado (medido)
		transparency = 0,
		material = Enum.Material.SmoothPlastic,
		canCollide = true,
		usesDirection = false,
		checker = Color3.fromRGB(83, 104, 124),
	},
	{
		id = "HookThrough",
		label = "Hookthrough",
		description = "Sólido para o jogador; o gancho atravessa",
		tag = Tags.HookThrough,
		color = Color3.fromRGB(45, 45, 52), -- preto, levemente transparente (pedido)
		transparency = 0.25,
		material = Enum.Material.SmoothPlastic,
		canCollide = true,
		usesDirection = false,
	},
	{
		id = "Freeze",
		label = "Freeze",
		description = "Atravessável; congela enquanto estiver dentro e ~1 s depois de sair",
		tag = Tags.FreezeZone,
		color = Color3.fromRGB(70, 75, 90),
		transparency = 0.45,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
	},
	{
		id = "Unfreeze",
		label = "Unfreeze",
		description = "Atravessável; descongela na hora",
		tag = Tags.UnfreezeZone,
		color = Color3.fromRGB(255, 215, 70),
		transparency = 0.45,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
	},
	{
		id = "OneWay",
		label = "Mão única",
		description = "Passa só no sentido da seta; no contrário é sólido",
		tag = Tags.OneWay,
		-- Medido: nuvem (158, 181, 203) sobre o céu (120, 151, 183); cor que dá esse resultado com 30%.
		color = Color3.fromRGB(174, 194, 211),
		transparency = 0.3,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = true,
	},
	{
		id = "Kill",
		label = "Morte",
		-- Sólido para o gancho prender (ADR 0049, 0053); encostar continua levando ao checkpoint.
		description = "Sólido; o gancho prende; encostar volta na hora ao checkpoint",
		tag = Tags.KillZone,
		-- Medido: (164, 97, 114) sobre o céu; cor que dá esse resultado com 30% de transparência.
		color = Color3.fromRGB(183, 74, 84),
		transparency = 0.3,
		material = Enum.Material.SmoothPlastic,
		canCollide = true,
		usesDirection = false,
	},
	{
		id = "HookOnce",
		label = "Gancho único",
		description = "Sólido; o gancho prende uma vez por vida/checkpoint",
		tag = Tags.HookOnce,
		color = Color3.fromRGB(113, 163, 119), -- verde (medido)
		transparency = 0,
		material = Enum.Material.SmoothPlastic,
		canCollide = true,
		usesDirection = false,
	},
	{
		id = "StartLine",
		label = "Largada",
		description = "Atravessável; ao passar começa (ou recomeça) o tempo da run",
		tag = Tags.StartLine,
		color = Color3.fromRGB(240, 240, 245),
		transparency = 0.3,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
		checker = Color3.fromRGB(60, 110, 200),
	},
	{
		id = "FinishLine",
		label = "Chegada",
		description = "Atravessável; ao passar com a run valendo, salva o tempo",
		tag = Tags.FinishLine,
		color = Color3.fromRGB(240, 240, 245),
		transparency = 0.3,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
		checker = Color3.fromRGB(25, 25, 30),
	},
	{
		id = "SoloStart",
		label = "Entrar solo",
		description = "Atravessável; ao passar vira fantasma (sem colisão com outros jogadores)",
		tag = Tags.SoloStart,
		color = Color3.fromRGB(150, 155, 168),
		transparency = 0.5,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
		text = "SOLO",
	},
	{
		id = "SoloEnd",
		label = "Sair solo",
		description = "Atravessável; ao passar volta a colidir com os outros jogadores",
		tag = Tags.SoloEnd,
		color = Color3.fromRGB(205, 208, 216),
		transparency = 0.5,
		material = Enum.Material.SmoothPlastic,
		canCollide = false,
		usesDirection = false,
		text = "FIM",
	},
} :: { Element })

-- Quadrados do quadriculado por lado de um bloco (só visual).
MapElements.CHECKER_CELLS = 2

MapElements.byId = {} :: { [string]: Element }
for _, element in MapElements.list do
	MapElements.byId[element.id] = element
end
table.freeze(MapElements.byId)

-- Texto das setas da mão única (só visual): mostra o sentido em que se pode passar.
MapElements.ARROW_TEXT = "^ ^ ^"
MapElements.ARROW_ROTATION =
	table.freeze({ Up = 0, Right = 90, Down = 180, Left = 270 }) :: { [Direction]: number }

-- Vetor (no plano) do sentido permitido.
MapElements.DIRECTION_VECTOR = table.freeze({
	Up = Vector3.new(0, 1, 0),
	Down = Vector3.new(0, -1, 0),
	Left = Vector3.new(-1, 0, 0),
	Right = Vector3.new(1, 0, 0),
}) :: { [Direction]: Vector3 }

function MapElements.isDirection(value: unknown): boolean
	return value == "Up" or value == "Down" or value == "Left" or value == "Right"
end

return table.freeze(MapElements)
