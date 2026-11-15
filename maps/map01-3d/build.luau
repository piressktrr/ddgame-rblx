-- GERADO por tools/stages3d.py. Não editar à mão.
local CollectionService = game:GetService("CollectionService")
local maps = workspace:FindFirstChild("Maps") or Instance.new("Folder")
maps.Name = "Maps"
maps.Parent = workspace
local old = maps:FindFirstChild("Map01")
if old then old:Destroy() end
local model = Instance.new("Model")
model.Name = "Map01"
local COLORS = { solid = Color3.fromRGB(163, 162, 165), start = Color3.fromRGB(90, 160, 110), checkpoint = Color3.fromRGB(255, 210, 63), finish = Color3.fromRGB(245, 245, 245), shortcut = Color3.fromRGB(120, 170, 220) }
local TAGS = { checkpoint = "Checkpoint", finish = "RaceFinish" }
local STAGES = { "Aquecimento", "Zigue-zague", "Rampas", "Serpentina", "Labirinto", "Torre final" }
local folders = {}
local function P(stage, name, kind, cx, cy, cz, sx, sy, sz, rz, order)
	local parent = model
	if stage > 0 then
		if not folders[stage] then
			local f = Instance.new("Model")
			f.Name = string.format("Estagio%d_%s", stage, STAGES[stage])
			f.Parent = model
			folders[stage] = f
		end
		parent = folders[stage]
	end
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = Vector3.new(sx, sy, sz)
	p.CFrame = CFrame.new(cx, cy, cz) * CFrame.Angles(0, 0, math.rad(rz))
	p.Color = COLORS[kind]
	p:SetAttribute("Kind", kind)
	if order then p:SetAttribute("Order", order) end
	if TAGS[kind] then CollectionService:AddTag(p, TAGS[kind]) end
	p.Parent = parent
end
P(0, "LobbyPiso", "start", -20, -1, 0, 40, 2, 40, 0)
P(1, "E1_Entrada", "solid", 6, -1, 0, 12, 2, 24, 0)
P(1, "E1_Saida", "solid", 90, -1, 0, 12, 2, 24, 0)
P(1, "E1_SaidaMarco", "checkpoint", 90, 0.2, 0, 4, 0.4, 24, 0, 1)
P(1, "E1_Plat1", "solid", 22, -1, 0, 12, 2, 10, 0)
P(1, "E1_Plat2", "solid", 38, 0, 0, 12, 2, 10, 0)
P(1, "E1_Plat3", "solid", 54, 1, 0, 12, 2, 10, 0)
P(1, "E1_Plat4", "solid", 72, 0, 0, 16, 2, 10, 0)
P(1, "E1_AtalhoViga", "shortcut", 48, -0.5, 9, 72, 1, 2, 0)
P(2, "E2_Entrada", "solid", 102, -1, 0, 12, 2, 24, 0)
P(2, "E2_Saida", "solid", 186, -1, 0, 12, 2, 24, 0)
P(2, "E2_SaidaMarco", "checkpoint", 186, 0.2, 0, 4, 0.4, 24, 0, 2)
P(2, "E2_Passarela1", "solid", 116, -1, -9, 16, 2, 6, 0)
P(2, "E2_Passarela2", "solid", 130, -1, 9, 20, 2, 6, 0)
P(2, "E2_Passarela3", "solid", 146, -1, -9, 20, 2, 6, 0)
P(2, "E2_Passarela4", "solid", 162, -1, 9, 20, 2, 6, 0)
P(2, "E2_Passarela5", "solid", 174, -1, -9, 12, 2, 6, 0)
P(2, "E2_Travessia1", "solid", 122, -1, 0, 4, 2, 12, 0)
P(2, "E2_Travessia2", "solid", 138, -1, 0, 4, 2, 12, 0)
P(2, "E2_Travessia3", "solid", 154, -1, 0, 4, 2, 12, 0)
P(2, "E2_Travessia4", "solid", 170, -1, 0, 4, 2, 12, 0)
P(2, "E2_AtalhoPino1", "shortcut", 114, -0.5, 0, 3, 1, 3, 0)
P(2, "E2_AtalhoPino2", "shortcut", 130, -0.5, 0, 3, 1, 3, 0)
P(2, "E2_AtalhoPino3", "shortcut", 146, -0.5, 0, 3, 1, 3, 0)
P(2, "E2_AtalhoPino4", "shortcut", 162, -0.5, 0, 3, 1, 3, 0)
P(2, "E2_AtalhoPino5", "shortcut", 176, -0.5, 0, 3, 1, 3, 0)
P(3, "E3_Entrada", "solid", 198, -1, 0, 12, 2, 24, 0)
P(3, "E3_Saida", "solid", 282, -1, 0, 12, 2, 24, 0)
P(3, "E3_SaidaMarco", "checkpoint", 282, 0.2, 0, 4, 0.4, 24, 0, 3)
P(3, "E3_RampaSobe1", "solid", 214.371, 3.072, 0, 21.541, 2, 12, 21.801)
P(3, "E3_Plato1", "solid", 230, 7, 0, 12, 2, 12, 0)
P(3, "E3_RampaDesce", "solid", 241.445, 3.168, 0, 14.422, 2, 12, -33.69)
P(3, "E3_RampaSobe2", "solid", 254.555, 3.168, 0, 14.422, 2, 12, 33.69)
P(3, "E3_Plato2", "solid", 264, 7, 0, 8, 2, 12, 0)
P(3, "E3_RampaDesce2", "solid", 271.293, 3.293, 0, 11.314, 2, 12, -45)
P(3, "E3_AtalhoPonte1", "shortcut", 241, 7.5, 7, 10, 1, 2, 0)
P(3, "E3_AtalhoPonte2", "shortcut", 255, 7.5, 7, 10, 1, 2, 0)
P(4, "E4_Entrada", "solid", 294, -1, 0, 12, 2, 24, 0)
P(4, "E4_Saida", "solid", 378, 17, 0, 12, 2, 24, 0)
P(4, "E4_SaidaMarco", "checkpoint", 378, 18.2, 0, 4, 0.4, 24, 0, 4)
P(4, "E4_Degrau1", "solid", 306, 2.5, -5, 8, 1, 8, 0)
P(4, "E4_Degrau2", "solid", 318, 5.5, 5, 8, 1, 8, 0)
P(4, "E4_Degrau3", "solid", 330, 8.5, -5, 8, 1, 8, 0)
P(4, "E4_Degrau4", "solid", 342, 11.5, 5, 8, 1, 8, 0)
P(4, "E4_Degrau5", "solid", 354, 14.5, -5, 8, 1, 8, 0)
P(4, "E4_Degrau6", "solid", 366, 17.5, 5, 8, 1, 8, 0)
P(4, "E4_AtalhoRampa1", "shortcut", 310.121, 2.015, 11, 20.616, 1, 2, 14.036)
P(4, "E4_AtalhoRampa2", "shortcut", 334.121, 8.015, 11, 20.616, 1, 2, 14.036)
P(4, "E4_AtalhoRampa3", "shortcut", 360.121, 14.515, 11, 24.739, 1, 2, 14.036)
P(5, "E5_Entrada", "solid", 390, 17, 0, 12, 2, 24, 0)
P(5, "E5_Saida", "solid", 474, 17, 0, 12, 2, 24, 0)
P(5, "E5_SaidaMarco", "checkpoint", 474, 18.2, 0, 4, 0.4, 24, 0, 5)
P(5, "E5_Piso", "solid", 432, 17, 0, 72, 2, 24, 0)
P(5, "E5_Parede1", "solid", 409, 22.5, -3, 2, 9, 18, 0)
P(5, "E5_Parede2a", "solid", 421, 22.5, -4, 2, 9, 4, 0)
P(5, "E5_Parede2b", "solid", 421, 22.5, 7, 2, 9, 10, 0)
P(5, "E5_Parede2Atalho", "shortcut", 421, 26, 0, 2, 2, 4, 0)
P(5, "E5_Parede3", "solid", 433, 22.5, -3, 2, 9, 18, 0)
P(5, "E5_Parede4a", "solid", 445, 22.5, -4, 2, 9, 4, 0)
P(5, "E5_Parede4b", "solid", 445, 22.5, 7, 2, 9, 10, 0)
P(5, "E5_Parede4Atalho", "shortcut", 445, 26, 0, 2, 2, 4, 0)
P(5, "E5_Parede5", "solid", 457, 22.5, -3, 2, 9, 18, 0)
P(6, "E6_Entrada", "solid", 486, 17, 0, 12, 2, 24, 0)
P(6, "E6_Pilar", "solid", 528, 30.5, 0, 8, 29, 8, 0)
P(6, "E6_Espiral1", "solid", 518, 20.5, -10, 8, 1, 8, 0)
P(6, "E6_Espiral2", "solid", 528, 23.5, -10, 8, 1, 8, 0)
P(6, "E6_Espiral3", "solid", 538, 26.5, -10, 8, 1, 8, 0)
P(6, "E6_Espiral4", "solid", 538, 29.5, 0, 8, 1, 8, 0)
P(6, "E6_Espiral5", "solid", 538, 32.5, 10, 8, 1, 8, 0)
P(6, "E6_Espiral6", "solid", 528, 35.5, 10, 8, 1, 8, 0)
P(6, "E6_Espiral7", "solid", 518, 38.5, 10, 8, 1, 8, 0)
P(6, "E6_Espiral8", "solid", 518, 41.5, 0, 8, 1, 8, 0)
P(6, "E6_Acesso", "solid", 503.5, 17, -10, 15, 2, 8, 0)
P(6, "E6_AtalhoPino1", "shortcut", 544.5, 35.5, 14.5, 3, 1, 3, 0)
P(6, "E6_AtalhoPino2", "shortcut", 550.5, 38.5, 14.5, 3, 1, 3, 0)
P(6, "E6_AtalhoPino3", "shortcut", 556.5, 41.5, 14.5, 3, 1, 3, 0)
P(6, "E6_Chegada", "solid", 556, 44, 0, 40, 2, 24, 0)
P(6, "E6_Fim", "finish", 567, 45.2, 0, 6, 0.4, 24, 0)
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.Neutral = true
spawn.Duration = 0
spawn.Size = Vector3.new(6, 1, 6)
spawn.CFrame = CFrame.lookAlong(Vector3.new(-20, 0 + 0.5, 0), Vector3.xAxis)
spawn.Parent = model
model.Parent = maps
workspace.FallenPartsDestroyHeight = -40
return #model:GetDescendants()
