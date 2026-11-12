--!strict
--[[
	Loader: carrega todos os ModuleScripts de uma pasta e executa o ciclo de vida.

	Ciclo de vida de cada Service/Controller:
	  1. Init()  -> síncrono, em ordem alfabética. Prepara estado e referências.
	                Não deve esperar (yield) nem depender de outro módulo já ter iniciado.
	  2. Start() -> chamado depois que TODOS terminaram o Init, cada um em sua própria thread.
	                Aqui pode conectar eventos, iniciar loops e usar outros módulos.
]]

export type Module = {
	Init: ((self: any) -> ())?,
	Start: ((self: any) -> ())?,
}

local Loader = {}

local function sortedModuleScripts(folder: Instance): { ModuleScript }
	local scripts: { ModuleScript } = {}
	for _, child in folder:GetChildren() do
		if child:IsA("ModuleScript") then
			table.insert(scripts, child)
		end
	end
	table.sort(scripts, function(a, b)
		return a.Name < b.Name
	end)
	return scripts
end

function Loader.loadAll(folder: Instance): { [string]: Module }
	local modules: { [string]: Module } = {}
	for _, moduleScript in sortedModuleScripts(folder) do
		modules[moduleScript.Name] = (require :: any)(moduleScript)
	end
	return modules
end

function Loader.start(modules: { [string]: Module })
	local names: { string } = {}
	for name in modules do
		table.insert(names, name)
	end
	table.sort(names)

	for _, name in names do
		local module = modules[name]
		if module.Init then
			local ok, err = pcall(module.Init, module)
			if not ok then
				error(`[Loader] Falha no Init de {name}: {err}`)
			end
		end
	end

	for _, name in names do
		local module = modules[name]
		if module.Start then
			task.spawn(function()
				local ok, err = pcall(module.Start, module)
				if not ok then
					warn(`[Loader] Falha no Start de {name}: {err}`)
				end
			end)
		end
	end
end

return Loader
