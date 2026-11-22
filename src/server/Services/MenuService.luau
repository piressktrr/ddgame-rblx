--!strict
--[[
	Cópia leve dos mapas para o menu principal (MenuController). Com o StreamingEnabled, o cliente só
	tem as peças perto do personagem, então o fundo e as prévias do menu não poderiam copiar o mapa do
	workspace. Aqui o servidor copia uma vez, ao iniciar, para `ReplicatedStorage.MenuPreview`
	(que sempre replica inteiro):
	  - `Map01`: só a faixa de baixo do mapa (onde o fundo do menu passeia e a prévia mostra a E1);
	  - `Tutorial`: o modelo do tutorial.
	Só peças visíveis, ancoradas, sem colisão nem consulta, sem tags e sem filhos além de malha/decal.
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PREVIEW_MAX_Y = 260 -- studs: altura máxima copiada do Map01

local MenuService = {}

local function copyParts(source: Instance, into: Model, keep: (BasePart) -> boolean)
	for _, part in source:GetDescendants() do
		if not part:IsA("BasePart") or part.Transparency >= 1 or not keep(part) then
			continue
		end
		local copy = part:Clone()
		-- Sem tags: senão os serviços (zonas, largada, portal...) achariam a cópia como peça do jogo.
		for _, tag in CollectionService:GetTags(copy) do
			CollectionService:RemoveTag(copy, tag)
		end
		for _, child in copy:GetChildren() do
			if not child:IsA("DataModelMesh") and not child:IsA("Decal") then
				child:Destroy()
			end
		end
		copy.Anchored = true
		copy.CanCollide = false
		copy.CanQuery = false
		copy.CanTouch = false
		copy.Parent = into
	end
end

function MenuService.Start()
	local folder = Instance.new("Folder")
	folder.Name = "MenuPreview"
	local maps = workspace:FindFirstChild("Maps")
	local map01 = maps and maps:FindFirstChild("Map01")
	if map01 then
		local model = Instance.new("Model")
		model.Name = "Map01"
		copyParts(map01, model, function(part)
			return part.Position.Y < PREVIEW_MAX_Y
		end)
		model.Parent = folder
	end
	local tutorial = workspace:FindFirstChild("Tutorial")
	if tutorial then
		local model = Instance.new("Model")
		model.Name = "Tutorial"
		copyParts(tutorial, model, function()
			return true
		end)
		model.Parent = folder
	end
	folder.Parent = ReplicatedStorage
end

return MenuService
