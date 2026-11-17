--!strict
-- Monta Workspace.Tutorial (greybox 2.5D, plano Z = 0, X horizontal, Y altura, studs). ADR 0041, 0046.
-- Rodar no Studio em modo Edit (MCP execute_luau ou barra de comandos). Apaga o Tutorial antigo antes.
-- Sala colada ao lobby, à esquerda: X -1608..-1100, Y 96..228 (chão com topo em Y = 104, como o
-- lobby; teto em 196 até X -1500 e em 224 na lição 7). Entra-se pela abertura na parede oeste do
-- lobby (Y 104..116) e anda-se para a esquerda.
-- Sete lições do gancho, uma por vez; cair numa lição leva ao começo dela por chão (rampas), sem morte.
-- No fim, um portal com a tag `LobbyPortal` (o LobbyService começa a corrida e leva ao RaceStart).
-- Mesmas cores e convenções do Map01 e do Lobby (tools/map2d.py, KINDS). Nenhum script no mapa.
type Kind = {
	color: Color3,
	tags: { string }?,
	class: string?,
	yaw: number?,
	collide: boolean?,
	ghost: boolean?,
	z: number?,
	depth: number?,
	transparency: number?,
}
local KINDS: { [string]: Kind } = {
	Rock = { color = Color3.fromHex("6f717b") }, -- chão, paredes, teto e alvos (gancho gruda)
	SlopeL = { color = Color3.fromHex("6f717b"), class = "WedgePart", yaw = 90 }, -- rampa, sobe para a direita
	NoHook = { color = Color3.fromHex("8e5bd6"), tags = { "NoHook" } }, -- não gruda
	HookOnce = { color = Color3.fromHex("5fbf6a"), tags = { "HookOnce" } }, -- gruda 1 vez
	Portal = {
		color = Color3.fromHex("2fc4c4"),
		tags = { "LobbyPortal" },
		collide = false,
		transparency = 0.35,
	}, -- fim do tutorial: começa a corrida (LobbyService)
	Backdrop = { color = Color3.fromHex("23252c"), collide = false, ghost = true, z = -10, depth = 1 }, -- fundo, não gruda
	Sign = { color = Color3.fromHex("33363f"), collide = false, ghost = true, z = -9.3, depth = 0.4 }, -- placa de dica no fundo
}

local old = workspace:FindFirstChild("Tutorial")
if old then
	old:Destroy()
end
local model = Instance.new("Model")
model.Name = "Tutorial"

-- Peça com centro (x, y) e tamanho (w, h) no plano. Rampas: WedgePart deitada no plano (yaw 90 =
-- rampa virada para -X, sobe para a direita).
local function p(name: string, kind: string, x: number, y: number, w: number, h: number): BasePart
	local k = KINDS[kind]
	local part = Instance.new(k.class or "Part") :: BasePart
	local depth = k.depth or 12
	if k.yaw then
		part.Size = Vector3.new(depth, h, w)
		part.CFrame = CFrame.new(x, y, 0) * CFrame.Angles(0, math.rad(k.yaw), 0)
	else
		part.Size = Vector3.new(w, h, depth)
		part.CFrame = CFrame.new(x, y, k.z or 0)
	end
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
	part:SetAttribute("Kind", kind)
	for _, tag in k.tags or {} do
		part:AddTag(tag)
	end
	part.Parent = model
	return part
end

-- Retângulo de x1..x2 por y1..y2 (x1 < x2, y1 < y2).
local function r(name: string, kind: string, x1: number, x2: number, y1: number, y2: number): BasePart
	return p(name, kind, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
end

-- Placa de texto no fundo (SurfaceGui na face +Z, a que olha para a câmera).
local function sign(name: string, x: number, y: number, w: number, h: number, text: string)
	local part = p(name, "Sign", x, y, w, h)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Text"
	gui.Face = Enum.NormalId.Back
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 20
	gui.LightInfluence = 0
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = text
	label.TextScaled = true
	label.TextWrapped = true
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = Color3.fromHex("ffffff")
	label.Parent = gui
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, 12)
	padding.PaddingRight = UDim.new(0, 12)
	padding.PaddingTop = UDim.new(0, 8)
	padding.PaddingBottom = UDim.new(0, 8)
	padding.Parent = label
end

-- Caixa da sala.
r("Floor", "Rock", -1608, -1100, 96, 104) -- topo em Y = 104 (o do lobby)
r("WallEast", "Rock", -1104, -1100, 116, 196) -- acima da abertura para o lobby (Y 104..116)
r("Ceiling", "Rock", -1340, -1100, 196, 200)
r("CeilingNoHook", "NoHook", -1500, -1340, 196, 200) -- roxo: ninguém pula as lições 5 e 6 pelo teto
-- Lição 7 tem teto mais alto (224): degrau roxo fecha a caixa entre os dois tetos.
r("CeilingStep7", "NoHook", -1500, -1496, 196, 228)
r("Ceiling7", "NoHook", -1608, -1500, 224, 228) -- roxo: ninguém atravessa o vão pelo teto
r("WallWest", "NoHook", -1608, -1604, 104, 224)
r("Backdrop", "Backdrop", -1500, -1100, 96, 200)
r("Backdrop7", "Backdrop", -1608, -1500, 96, 228)

-- Lição 1 (X -1144..-1104, chão 104): clicar num bloco e ser puxado. Degrau de 20: o pulo não alcança.
r("Step1", "Rock", -1184, -1144, 104, 124) -- T1, topo 124
-- Alto e quase na borda: perto da parede, a linha até o bloco passa por cima da quina do degrau.
p("Target1", "Rock", -1146, 138, 4, 4) -- X -1148..-1144, Y 136..140

-- Lição 2 (fosso X -1184..-1284, chão 104): segurar para ficar preso. Puxado até a plataforma sem
-- segurar, o embalo passa direto; segurando, para no ponto e cai em cima dela. Rampa volta a T1.
p("Ramp2", "SlopeL", -1195, 114, 22, 20) -- X -1206..-1184, de 104 (oeste) a 124 (leste)
r("Perch2", "Rock", -1213, -1209, 132, 136) -- plataforma no ar (passa-se por baixo no fosso)
p("Target2", "Rock", -1211, 147, 4, 4) -- para segurar acima da plataforma

-- Lição 3 (mesmo fosso): encadear dois alvos no ar até T2. Da plataforma, T2 está fora do alcance.
p("Target3a", "Rock", -1236, 152, 4, 4)
p("Target3b", "Rock", -1260, 156, 4, 4)
r("Step2", "Rock", -1317, -1284, 104, 140) -- T2, topo 140

-- Lição 4 (T2, X -1314..-1284): roxo não prende. A parede até T3 tem a face roxa; o bloco cinza leva.
r("Wall4", "NoHook", -1317, -1314, 140, 164)
p("Decoy4", "NoHook", -1296, 160, 4, 4) -- roxo no caminho, para tentar e ver que não prende
p("Target4", "Rock", -1306, 175, 4, 4)
r("Step3", "Rock", -1352, -1317, 104, 164) -- T3, topo 164

-- Lição 5 (vão X -1352..-1397, chão 140): verde prende só uma vez. Teto roxo por cima.
r("Pit5", "Rock", -1397, -1352, 104, 140)
p("Ramp5", "SlopeL", -1366, 152, 28, 24) -- X -1380..-1352, de 140 a 164 (volta a T3)
p("Target5", "HookOnce", -1374, 178, 4, 4)
r("Step4", "Rock", -1427, -1397, 104, 164) -- T4, topo 164

-- Lição 6 (vão X -1427..-1457): soltar o gancho e dar o pulo duplo. Puxado de T4 até a face leste do
-- bloco (quase na horizontal), o corpo para encostado nele com os pés abaixo do topo do bloco (174) e
-- da borda roxa T5 (172): só passa por cima com o pulo no ar. T5 roxa não prende.
r("Pit6", "Rock", -1457, -1427, 104, 140)
p("Ramp6", "SlopeL", -1442, 152, 30, 24) -- X -1457..-1427, de 140 a 164 (volta a T4)
p("Target6", "Rock", -1451, 172, 4, 4) -- Y 170..174
r("Step5", "NoHook", -1500, -1457, 104, 172) -- T5, topo 172 (também o começo da lição 7)

-- Lição 7 (vão X -1556..-1500, chão 140): salto de embalo (ADR 0050). Da borda oeste de T5, puxa-se
-- até a face de baixo do bloco Target7a sem segurar: o gancho solta perto dele com 0,45 × 58 ≈ 26
-- studs/s (sobra ~20–24 em X depois de raspar embaixo do bloco). Target7b fica a 44,5 em X e 11,5 mais
-- alto (46 de centro a centro): segurando sob Target7a, o bloco está a ~48–50 do root (alcance 40) e
-- sem pulo duplo a queda afasta mais. Com o embalo e Espaço no ar, ele entra no alcance. T6 roxo (topo
-- 184, a 41 do ponto de soltura) não se alcança sem o segundo gancho. Rampa leva de volta a T5.
r("Pit7", "Rock", -1556, -1500, 104, 140)
p("Ramp7", "SlopeL", -1520, 156, 40, 32) -- X -1540..-1500, de 140 (oeste) a 172 (leste, T5)
p("Target7a", "Rock", -1521, 187.5, 4, 4) -- Y 185,5..189,5
p("Target7b", "Rock", -1565.5, 199, 4, 4) -- X -1567,5..-1563,5, Y 197..201
r("Step6", "NoHook", -1604, -1556, 104, 184) -- T6, topo 184 (embaixo de Target7b)

-- Fim: portal para a corrida.
local portal = p("Portal", "Portal", -1592, 191, 6, 14)

-- Texto em cima do portal (como no lobby).
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

-- Dicas (placas no fundo).
sign("Sign0", -1123, 146, 34, 10, "Tutorial do gancho\nJá sabe jogar? Volte e use o portal Corrida.")
sign("Sign1", -1124, 124, 34, 10, "1. Mire num bloco cinza e clique: o gancho puxa você até ele.")
sign("Sign2", -1166, 154, 34, 12, "2. Segure o clique: fica preso no ponto. Solte em cima da plataforma.")
sign("Sign3", -1248, 175, 40, 10, "3. Ainda no ar, clique no próximo bloco. Encadeie até o outro lado.")
sign("SignFall", -1240, 116, 30, 8, "Caiu? A rampa leva de volta.")
sign("Sign4", -1298, 188, 30, 10, "4. Roxo não prende. Procure o cinza.")
sign("Sign5", -1372, 189, 36, 10, "5. Verde prende só uma vez (volta ao renascer ou num checkpoint).")
sign("Sign6", -1440, 189, 32, 10, "6. Puxe até o bloco e, já solto, aperte Espaço no ar: pulo duplo.")
sign("Sign7", -1532, 210, 40, 12, "7. Puxe por baixo sem segurar, Espaço no ar, e o próximo bloco.")
sign("SignEnd", -1578, 194, 16, 8, "Pronto! Entre no portal.")

model.Parent = workspace
return #model:GetChildren()
