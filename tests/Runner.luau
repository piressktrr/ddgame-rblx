--!strict
--[[
	Runner dos testes (TestEZ). É um ModuleScript em ServerStorage.Tests: não roda sozinho no jogo.

	Rodar no Studio em modo Edit (barra de comando ou `execute_luau` do MCP):
		return require(game.ServerStorage.Tests.Runner)()

	Devolve um texto com o resumo (passaram/falharam) e o caminho de cada teste que falhou.
	Também imprime esse texto no Output.
]]

local ServerStorage = game:GetService("ServerStorage")

local TestEZ = require(ServerStorage.DevPackages.TestEZ) :: any

type Node = {
	planNode: { phrase: string },
	status: string,
	errors: { string },
	children: { Node },
}

local function collectFailures(node: Node, path: { string }, out: { string })
	local here = table.clone(path)
	table.insert(here, node.planNode.phrase)
	if node.status == "Failure" and #node.children == 0 then
		table.insert(out, "[-] " .. table.concat(here, " > "))
		for _, message in node.errors do
			table.insert(out, "      " .. message)
		end
	end
	for _, child in node.children do
		collectFailures(child, here, out)
	end
end

local function run(): string
	local summary = ""
	local reporter = {
		report = function(results: any)
			local lines: { string } = {}
			for _, child: Node in results.children do
				collectFailures(child, {}, lines)
			end
			table.insert(
				lines,
				string.format(
					"%d passaram, %d falharam, %d pulados",
					results.successCount,
					results.failureCount,
					results.skippedCount
				)
			)
			summary = table.concat(lines, "\n")
			print("[Tests]\n" .. summary)
		end,
	}
	TestEZ.TestBootstrap:run({ script.Parent }, reporter)
	return summary
end

return run
