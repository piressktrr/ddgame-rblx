--!strict
--[[
	Lê as tags de uma peça para o gancho (RF-12, RF-13), igual no cliente e no servidor.
	A tag pode estar na própria peça ou num ancestral (um Model inteiro marcado como `NoHook`).
	As regras em si ficam em `Logic/HookRules` (puras).
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)

local HookSurface = {}

-- A instância com a tag: a peça ou o ancestral mais próximo dentro do Workspace.
local function findTagged(part: Instance, tag: string): Instance?
	local current: Instance? = part
	while current and current ~= workspace do
		if CollectionService:HasTag(current, tag) then
			return current
		end
		current = current.Parent
	end
	return nil
end

function HookSurface.getKind(part: BasePart): HookRules.SurfaceKind
	return HookRules.surfaceKind(
		findTagged(part, Config.Tags.NoHook) ~= nil,
		findTagged(part, Config.Tags.HookOnce) ~= nil
	)
end

-- Chave do uso de uma superfície verde: a instância que tem a tag `HookOnce` (nil se não for verde).
-- Um Model verde com várias peças conta como um uso só.
function HookSurface.getHookOnceKey(part: BasePart): Instance?
	return findTagged(part, Config.Tags.HookOnce)
end

return HookSurface
