--!strict
-- GERADO por tools/map2d.py a partir de tools/map_layout.py (rascunho v2). Não editar à mão.
-- Monta Workspace.Maps.Map01 (greybox 2.5D, plano Z = 0, X horizontal, Y altura, studs).
-- Rodar no Studio em modo Edit (MCP execute_luau ou barra de comandos). Apaga o Map01 antigo antes.
type Kind = {
	color: Color3,
	tags: { string }?,
	class: string?,
	yaw: number?,
	collide: boolean?,
	ghost: boolean?,
	z: number?,
	depth: number?,
}
local KINDS: { [string]: Kind } = {
	Rock = { color = Color3.fromHex("6f717b") }, -- rocha e sólidos (gancho gruda)
	SlopeR = { color = Color3.fromHex("6f717b"), class = "WedgePart", yaw = -90 }, -- rampa de rocha, sobe para a esquerda
	SlopeL = { color = Color3.fromHex("6f717b"), class = "WedgePart", yaw = 90 }, -- rampa de rocha, sobe para a direita
	Kill = { color = Color3.fromHex("d9434b"), tags = { "KillZone" }, collide = false }, -- mortal (sem colisão, grudável)
	Ice = { color = Color3.fromHex("c8ecff"), tags = { "FreezeZone" } }, -- gelo
	Unfreeze = { color = Color3.fromHex("FF8A1F"), tags = { "UnfreezeZone" } }, -- descongelar
	NoHook = { color = Color3.fromHex("8e5bd6"), tags = { "NoHook" } }, -- não gruda
	HookOnce = { color = Color3.fromHex("5fbf6a"), tags = { "HookOnce" } }, -- gruda 1 vez
	Checkpoint = { color = Color3.fromHex("ffd23f"), tags = { "Checkpoint" } }, -- checkpoint (atributo Order)
	Finish = { color = Color3.fromHex("ffffff"), tags = { "RaceFinish", "Checkpoint" } }, -- fim (também o último checkpoint)
	Spawn = { color = Color3.fromHex("5aa06e"), tags = { "RaceStart" }, class = "SpawnLocation", depth = 1 }, -- início da corrida (SpawnLocation desligado; nasce-se no lobby, ADR 0044)
	Backdrop = { color = Color3.fromHex("23252c"), collide = false, ghost = true, z = -10, depth = 1 }, -- fundo, não gruda
}

local maps = workspace:FindFirstChild("Maps") or Instance.new("Folder")
maps.Name = "Maps"
maps.Parent = workspace
local old = maps:FindFirstChild("Map01")
if old then
	old:Destroy()
end
local model = Instance.new("Model")
model.Name = "Map01"

-- Peça com centro (x, y) e tamanho (w, h) no plano; rz = giro em Z (graus). Rampas: WedgePart
-- deitada no plano (yaw -90 = rampa virada para +X, sobe para a esquerda; yaw 90 = o contrário).
local function p(
	name: string,
	kind: string,
	x: number,
	y: number,
	w: number,
	h: number,
	rz: number?
): BasePart
	local k = KINDS[kind]
	local part = Instance.new(k.class or "Part") :: BasePart
	local depth = k.depth or 12
	if k.yaw then
		part.Size = Vector3.new(depth, h, w)
		part.CFrame = CFrame.new(x, y, 0) * CFrame.Angles(0, math.rad(k.yaw), 0)
	else
		part.Size = Vector3.new(w, h, depth)
		part.CFrame = CFrame.new(x, y, k.z or 0) * CFrame.Angles(0, 0, math.rad(rz or 0))
	end
	part.Name = name
	part.Anchored = true
	part.Color = k.color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.CanCollide = k.collide ~= false
	if k.ghost then
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
	end
	if part:IsA("SpawnLocation") then
		-- Desligado: o jogador nasce no lobby (ADR 0044); a tag RaceStart marca o início.
		part.Enabled = false
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
p("Rock001", "Rock", -65, 217.5, 10, 395)
p("Rock002", "Rock", 270, 30, 660, 20)
p("Rock003", "Rock", 47, 112, 214, 4)
p("Rock004", "Rock", 47, 182, 214, 4)
p("Rock005", "Rock", 47, 247, 214, 4)
p("Rock006", "Rock", 406, 410, 932, 10)
p("Rock007", "Rock", -20, 329, 40, 114)
p("Rock008", "Rock", 109, 77, 254, 4)
p("Rock009", "Rock", 241, 147, 518, 4)
p("Rock010", "Rock", 96, 217, 228, 4)
p("Rock011", "Rock", 12, 295, 24, 46)
p("Rock012", "Rock", 40, 373, 80, 26)
p("Rock013", "Rock", 117, 281, 186, 18)
p("Rock014", "Rock", 60, 315, 12, 50)
p("Rock015", "Rock", 320, 381, 480, 10)
p("Rock016", "Rock", 106, 315, 12, 50)
p("Rock017", "Rock", 152, 315, 12, 50)
p("Rock018", "Rock", 360, 368, 400, 16)
p("Rock019", "Rock", 198, 315, 12, 50)
p("Rock020", "Rock", 216, 57.5, 40, 35)
p("Rock021", "Rock", 216, 84.5, 40, 11)
p("Rock022", "Rock", 348, 142.5, 304, 5)
p("Rock023", "Rock", 203, 182, 14, 66)
p("Rock024", "Rock", 203, 245.5, 14, 53)
p("Rock025", "Rock", 355, 169.5, 290, 41)
p("Rock026", "Rock", 395, 300, 330, 120)
p("Rock027", "Rock", 268, 56, 64, 32)
p("Rock028", "Rock", 368, 135, 264, 10)
p("Rock029", "Rock", 254, 234, 8, 12)
p("Rock030", "Rock", 280, 81, 40, 18)
p("Rock031", "Rock", 294, 234, 8, 12)
p("Rock032", "Rock", 334, 233, 8, 10)
p("Rock033", "Rock", 361, 197, 22, 14)
p("Rock034", "Rock", 414, 234, 8, 12)
p("Rock035", "Rock", 510, 65, 180, 50)
p("Rock036", "Rock", 454, 234, 8, 12)
p("Rock037", "Rock", 494, 234, 8, 12)
p("Rock038", "Rock", 560, 165, 80, 150)
p("Rock039", "Rock", 690, 270, 260, 60)
p("Rock040", "Rock", 700, 348, 240, 4)
p("Rock041", "Rock", 736, 25, 272, 10)
p("Rock042", "Rock", 614, 94, 28, 4)
p("Rock043", "Rock", 614, 146, 28, 4)
p("Rock044", "Rock", 614, 198, 28, 4)
p("Rock045", "Rock", 625, 235, 50, 10)
p("Rock046", "Rock", 601.5, 317, 3, 34)
p("Rock047", "Rock", 736, 400.5, 272, 9)
p("Rock048", "Rock", 606, 361, 4, 2)
p("Rock049", "Rock", 606, 385, 4, 2)
p("Rock050", "Rock", 611.5, 329, 3, 34)
p("Rock051", "Rock", 618, 373, 4, 2)
p("Rock052", "Rock", 621.5, 317, 3, 34)
p("Rock053", "Rock", 634, 120, 24, 4)
p("Rock054", "Rock", 721, 172, 198, 4)
p("Rock055", "Rock", 630, 361, 4, 2)
p("Rock056", "Rock", 630, 385, 4, 2)
p("Rock057", "Rock", 631.5, 329, 3, 34)
p("Rock058", "Rock", 641.5, 317, 3, 34)
p("Rock059", "Rock", 642, 373, 4, 2)
p("Rock060", "Rock", 735, 120, 170, 100)
p("Rock061", "Rock", 735, 177, 170, 6)
p("Rock062", "Rock", 651.5, 329, 3, 34)
p("Rock063", "Rock", 654, 361, 4, 2)
p("Rock064", "Rock", 654, 385, 4, 2)
p("Rock065", "Rock", 661.5, 317, 3, 34)
p("Rock066", "Rock", 666, 373, 4, 2)
p("Rock067", "Rock", 671.5, 329, 3, 34)
p("Rock068", "Rock", 678, 361, 4, 2)
p("Rock069", "Rock", 678, 385, 4, 2)
p("Rock070", "Rock", 681.5, 317, 3, 34)
p("Rock071", "Rock", 690, 373, 4, 2)
p("Rock072", "Rock", 691.5, 329, 3, 34)
p("Rock073", "Rock", 701.5, 317, 3, 34)
p("Rock074", "Rock", 702, 361, 4, 2)
p("Rock075", "Rock", 702, 385, 4, 2)
p("Rock076", "Rock", 711.5, 329, 3, 34)
p("Rock077", "Rock", 714, 373, 4, 2)
p("Rock078", "Rock", 721.5, 317, 3, 34)
p("Rock079", "Rock", 726, 361, 4, 2)
p("Rock080", "Rock", 726, 385, 4, 2)
p("Rock081", "Rock", 731.5, 329, 3, 34)
p("Rock082", "Rock", 738, 373, 4, 2)
p("Rock083", "Rock", 741.5, 317, 3, 34)
p("Rock084", "Rock", 750, 361, 4, 2)
p("Rock085", "Rock", 750, 385, 4, 2)
p("Rock086", "Rock", 751.5, 329, 3, 34)
p("Rock087", "Rock", 790, 210, 60, 60)
p("Rock088", "Rock", 761.5, 317, 3, 34)
p("Rock089", "Rock", 762, 373, 4, 2)
p("Rock090", "Rock", 771.5, 329, 3, 34)
p("Rock091", "Rock", 774, 361, 4, 2)
p("Rock092", "Rock", 774, 385, 4, 2)
p("Rock093", "Rock", 781.5, 317, 3, 34)
p("Rock094", "Rock", 786, 373, 4, 2)
p("Rock095", "Rock", 791.5, 329, 3, 34)
p("Rock096", "Rock", 798, 361, 4, 2)
p("Rock097", "Rock", 798, 385, 4, 2)
p("Rock098", "Rock", 801.5, 317, 3, 34)
p("Rock099", "Rock", 833, 138, 26, 4)
p("Rock100", "Rock", 833, 210, 26, 4)
p("Rock101", "Rock", 833, 282, 26, 4)
p("Rock102", "Rock", 833, 354, 26, 4)
p("Rock103", "Rock", 854, 102, 36, 4)
p("Rock104", "Rock", 854, 174, 36, 4)
p("Rock105", "Rock", 854, 246, 36, 4)
p("Rock106", "Rock", 854, 318, 36, 4)
p("Rock107", "Rock", 867, 65, 10, 70)
p("Rock108", "Rock", 867, 138, 10, 68)
p("Rock109", "Rock", 867, 210, 10, 68)
p("Rock110", "Rock", 867, 282, 10, 68)
p("Rock111", "Rock", 867, 358, 10, 76)
p("E3_Slope1", "SlopeR", 320, 65, 40, 50)
p("E3_Slope2", "SlopeL", 400, 65, 40, 50)
p("E1_Kill1", "Kill", 39, 291, 30, 2)
p("E1_Kill2", "Kill", 83, 291, 34, 2)
p("E1_Kill3", "Kill", 129, 291, 34, 2)
p("E1_Kill4", "Kill", 175, 291, 34, 2)
p("E1_Kill5", "Kill", 207, 291, 6, 2)
p("E2_Kill1", "Kill", 290, 191, 120, 2)
p("E2_Kill2", "Kill", 436, 191, 128, 2)
p("E3_Kill1", "Kill", 248, 73, 24, 2)
p("E4_Kill1", "Kill", 70, 115, 60, 2)
p("E4_Kill2", "Kill", 70, 185, 60, 2)
p("E4_Kill3", "Kill", 68, 41, 256, 2)
p("E5_Kill1", "Kill", 700, 351, 200, 2)
p("E6_Kill1", "Kill", 833, 357, 26, 2)
p("E6_Kill2", "Kill", 849, 321, 26, 2)
p("E6_Kill3", "Kill", 833, 285, 26, 2)
p("E6_Kill4", "Kill", 849, 249, 26, 2)
p("E6_Kill5", "Kill", 833, 213, 26, 2)
p("E6_Kill6", "Kill", 849, 177, 26, 2)
p("E6_Kill7", "Kill", 833, 141, 26, 2)
p("E6_Kill8", "Kill", 849, 105, 26, 2)
p("E6_Kill9", "Kill", 665, 31, 30, 2)
p("E6_Kill10", "Kill", 697, 31, 6, 2)
p("E6_Kill11", "Kill", 737, 31, 46, 2)
p("E6_Kill12", "Kill", 777, 31, 6, 2)
p("E6_Kill13", "Kill", 802, 31, 16, 2)
p("E3_Kill2", "Kill", 332.5, 52.5, 28.847, 4.222, -50.711)
p("E3_Kill3", "Kill", 387.5, 52.5, 28.847, 4.222, 50.711)
p("E1_Ice1", "Ice", 152, 341, 12, 2)
p("E2_Ice1", "Ice", 356, 205, 12, 2)
p("E3_Ice1", "Ice", 450, 91, 20, 2)
p("E4_Ice1", "Ice", 72, 150, 24, 2)
p("E5_Ice1", "Ice", 688, 301, 10, 2)
p("E6_Ice1", "Ice", 687, 32, 14, 4)
p("E6_Ice2", "Ice", 767, 32, 14, 4)
p("E1_Unfreeze1", "Unfreeze", 198, 341, 12, 2)
p("E2_Unfreeze1", "Unfreeze", 367, 205, 10, 2)
p("E4_Unfreeze1", "Unfreeze", -44, 185, 12, 2)
p("E5_Unfreeze1", "Unfreeze", 728, 301, 10, 2)
p("E6_Unfreeze1", "Unfreeze", 707, 32, 14, 4)
p("E6_Unfreeze2", "Unfreeze", 787, 32, 14, 4)
p("Farol1_Checkpoint1", "Checkpoint", 216, 91, 32, 2):SetAttribute("Order", 1)
p("E1_Spawn1", "Spawn", 12, 319, 16, 2)
p("Farol2_Finish1", "Finish", 710, 181, 60, 2):SetAttribute("Order", 2)
p("E2_NoHook1", "NoHook", 374, 233, 8, 10)
p("E2_NoHook2", "NoHook", 354, 239, 48, 2)
p("E4_NoHook1", "NoHook", -24, 77, 12, 4)
p("E4_NoHook2", "NoHook", 160, 112, 12, 4)
p("E4_NoHook3", "NoHook", -24, 147, 12, 4)
p("E4_NoHook4", "NoHook", 160, 182, 12, 4)
p("E4_NoHook5", "NoHook", -24, 217, 12, 4)
p("E4_NoHook6", "NoHook", 160, 247, 12, 4)
p("E6_HookOnce1", "HookOnce", 648, 125, 4, 30)
p("E6_HookOnce2", "HookOnce", 602, 175, 4, 30)
p("Backdrop", "Backdrop", 401, 217.5, 942, 395)

model.Parent = maps
workspace.FallenPartsDestroyHeight = math.min(workspace.FallenPartsDestroyHeight, 0)
return #model:GetChildren()
