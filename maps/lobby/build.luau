--!strict
-- Monta Workspace.Lobby (greybox 2.5D, plano Z = 0, X horizontal, Y altura, studs). ADR 0044.
-- Rodar no Studio em modo Edit (MCP execute_luau ou barra de comandos). Apaga o Lobby antigo antes.
-- Sala fechada em X -1100..-900, Y 100..160, longe do Map01 e do TestHook. Na parede oeste, uma
-- abertura (Y 104..116) leva ao Tutorial (maps/tutorial/build.luau), colado à esquerda.
-- Mesmas cores e convenções do Map01 (tools/map2d.py, KINDS).
type Kind = {
	color: Color3,
	tags: { string }?,
	class: string?,
	collide: boolean?,
	ghost: boolean?,
	z: number?,
	depth: number?,
	transparency: number?,
}
local KINDS: { [string]: Kind } = {
	Rock = { color = Color3.fromHex("6f717b") }, -- chão, paredes e teto
	Spawn = { color = Color3.fromHex("5aa06e"), tags = { "LobbySpawn" }, class = "SpawnLocation", depth = 1 }, -- nascimento ao entrar no jogo
	Portal = {
		color = Color3.fromHex("2fc4c4"),
		tags = { "LobbyPortal" },
		collide = false,
		transparency = 0.35,
	}, -- leva ao RaceStart
	Backdrop = { color = Color3.fromHex("23252c"), collide = false, ghost = true, z = -10, depth = 1 }, -- fundo, não gruda
}

local old = workspace:FindFirstChild("Lobby")
if old then
	old:Destroy()
end
local model = Instance.new("Model")
model.Name = "Lobby"

-- Peça com centro (x, y) e tamanho (w, h) no plano.
local function p(name: string, kind: string, x: number, y: number, w: number, h: number): BasePart
	local k = KINDS[kind]
	local part = Instance.new(k.class or "Part") :: BasePart
	part.Size = Vector3.new(w, h, k.depth or 12)
	part.CFrame = CFrame.new(x, y, k.z or 0)
	part.Name = name
	part.Anchored = true
	part.Color = k.color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.CanCollide = k.collide ~= false
	part.Transparency = k.transparency or 0
	if k.ghost then
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
	end
	if part:IsA("SpawnLocation") then
		part.Enabled = true
		part.Neutral = true
		part.Duration = 0
	end
	part:SetAttribute("Kind", kind)
	for _, tag in k.tags or {} do
		part:AddTag(tag)
	end
	part.Parent = model
	return part
end

p("Floor", "Rock", -1000, 102, 200, 4) -- topo em Y = 104
p("Ceiling", "Rock", -1000, 158, 200, 4)
p("WallLeft", "Rock", -1098, 136, 4, 40) -- Y 116..156: abertura Y 104..116 para o Tutorial (oeste)
p("WallRight", "Rock", -902, 130, 4, 52)
p("Spawn", "Spawn", -1060, 105, 12, 2)
local portal = p("Portal", "Portal", -940, 111, 6, 14)
p("Backdrop", "Backdrop", -1000, 130, 200, 60)

-- Texto em cima do portal.
local billboard = Instance.new("BillboardGui")
billboard.Name = "Label"
billboard.Size = UDim2.fromOffset(160, 40)
billboard.StudsOffset = Vector3.new(0, 9.5, 0)
billboard.LightInfluence = 0
billboard.Parent = portal
local label = Instance.new("TextLabel")
label.Size = UDim2.fromScale(1, 1)
label.BackgroundTransparency = 1
label.Text = "Corrida"
label.TextScaled = true
label.Font = Enum.Font.GothamBold
label.TextColor3 = Color3.fromHex("ffffff")
label.TextStrokeTransparency = 0.4
label.Parent = billboard

model.Parent = workspace
return #model:GetChildren()
