-- GERADO por tools/mapgen.py a partir de layout.json. Não editar à mão.
local maps = workspace:FindFirstChild("Maps") or Instance.new("Folder")
maps.Name = "Maps"
maps.Parent = workspace
local old = maps:FindFirstChild("Map01")
if old then old:Destroy() end
local model = Instance.new("Model")
model.Name = "Map01"
local function block(name, kind, x1, x2, y1, y2, r, g, b)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = Vector3.new(x2 - x1, math.max(y2 - y1, 0.2), 12)
	p.Position = Vector3.new((x1 + x2) / 2, (y1 + y2) / 2, 0)
	p.Color = Color3.fromRGB(r, g, b)
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p:SetAttribute("Kind", kind)
	if kind == "kill" then p.CanCollide = false; p.Transparency = 0.5 end
	p.Parent = model
end
block("WallLeft", "solid", -4, 0, -4, 70, 163, 162, 165)
block("StartFloor", "start", 0, 60, -4, 0, 90, 160, 110)
block("StartCeiling", "solid", 0, 60, 16, 20, 163, 162, 165)
block("S1_Step1", "solid", 64, 78, -2, 2, 163, 162, 165)
block("S1_Step2", "solid", 82, 94, 1, 5, 163, 162, 165)
block("S1_Step3", "solid", 98, 112, 4, 8, 163, 162, 165)
block("S2_Hub", "solid", 116, 150, 4, 8, 163, 162, 165)
block("S2_Up1", "solid", 152, 158, 11, 12, 163, 162, 165)
block("S2_Up2", "solid", 161, 167, 14, 15, 163, 162, 165)
block("S2_Up3", "solid", 172, 178, 14, 15, 163, 162, 165)
block("S2_Up4", "solid", 183, 189, 14, 15, 163, 162, 165)
block("S2_Up5", "solid", 194, 200, 14, 15, 163, 162, 165)
block("S2_TunnelFloor", "solid", 150, 190, -8, -4, 163, 162, 165)
block("S2_TunnelCeiling", "solid", 158, 188, 6, 8, 163, 162, 165)
block("S2_TunnelBump1", "solid", 168, 171, -4, -1, 163, 162, 165)
block("S2_TunnelBump2", "solid", 179, 182, -4, -1, 163, 162, 165)
block("S2_Stair1", "solid", 190, 195, -8, 0, 163, 162, 165)
block("S2_Stair2", "solid", 195, 200, -8, 3, 163, 162, 165)
block("S2_Stair3", "solid", 200, 205, -8, 6, 163, 162, 165)
block("S3_Rejoin", "solid", 205, 250, 6, 10, 163, 162, 165)
block("CP1", "checkpoint", 219, 225, 10, 10.4, 255, 210, 63)
block("S3_Tower1", "solid", 253, 259, 12, 13, 163, 162, 165)
block("S3_Tower2", "solid", 262, 268, 15, 16, 163, 162, 165)
block("S3_Tower3", "solid", 271, 277, 18, 19, 163, 162, 165)
block("S3_Tower4", "solid", 280, 286, 21, 22, 163, 162, 165)
block("S3_Tower5", "solid", 289, 295, 24, 25, 163, 162, 165)
block("S3_TopWalk", "solid", 298, 340, 27, 28, 163, 162, 165)
block("S3_Low1", "solid", 250, 262, -2, 2, 163, 162, 165)
block("S3_Low2", "solid", 267, 273, -2, 2, 163, 162, 165)
block("S3_Low3", "solid", 278, 284, -2, 2, 163, 162, 165)
block("S3_Low4", "solid", 289, 295, -2, 2, 163, 162, 165)
block("S3_Low5", "solid", 300, 306, -2, 2, 163, 162, 165)
block("S3_LowStair1", "solid", 310, 316, 1, 5, 163, 162, 165)
block("S3_LowStair2", "solid", 319, 325, 4, 8, 163, 162, 165)
block("FinishFloor", "solid", 328, 370, 6, 10, 163, 162, 165)
block("Finish", "finish", 355, 361, 10, 10.4, 255, 255, 255)
block("WallRight", "solid", 370, 374, 6, 70, 163, 162, 165)
block("PitMarker", "kill", 0, 370, -22, -20, 224, 38, 43)
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.Neutral = true
spawn.Duration = 0
spawn.Size = Vector3.new(6, 1, 6)
spawn.Position = Vector3.new(10, 0 + 0.5, 0)
spawn.Parent = model
model.Parent = maps
workspace.FallenPartsDestroyHeight = -30
return #model:GetChildren()
