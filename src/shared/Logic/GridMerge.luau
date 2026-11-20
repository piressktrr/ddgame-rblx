--!strict
--[[
	Junta células vizinhas iguais de uma grade em retângulos (varredura gulosa: estende a linha para
	a direita, depois sobe enquanto a linha inteira bate). Lógica pura, usada pelo MapBuilder para os
	blocos pintados virarem peças contínuas.
]]

export type Cell = { x: number, y: number, kind: string }
export type Rect = { x: number, y: number, w: number, h: number, kind: string }

local GridMerge = {}

function GridMerge.key(x: number, y: number): string
	return `{x},{y}`
end

function GridMerge.merge(cells: { Cell }): { Rect }
	local byKey: { [string]: Cell } = {}
	local ordered: { Cell } = {}
	for _, cell in cells do
		local key = GridMerge.key(cell.x, cell.y)
		if not byKey[key] then
			byKey[key] = cell
			table.insert(ordered, cell)
		end
	end
	table.sort(ordered, function(a, b)
		return if a.y == b.y then a.x < b.x else a.y < b.y
	end)

	local used: { [string]: boolean } = {}
	local function free(x: number, y: number, kind: string): boolean
		local key = GridMerge.key(x, y)
		local other = byKey[key]
		return not used[key] and other ~= nil and other.kind == kind
	end

	local rects: { Rect } = {}
	for _, cell in ordered do
		if used[GridMerge.key(cell.x, cell.y)] then
			continue
		end
		local w = 1
		while free(cell.x + w, cell.y, cell.kind) do
			w += 1
		end
		local h = 1
		while true do
			local rowFree = true
			for dx = 0, w - 1 do
				if not free(cell.x + dx, cell.y + h, cell.kind) then
					rowFree = false
					break
				end
			end
			if not rowFree then
				break
			end
			h += 1
		end
		for dx = 0, w - 1 do
			for dy = 0, h - 1 do
				used[GridMerge.key(cell.x + dx, cell.y + dy)] = true
			end
		end
		table.insert(rects, { x = cell.x, y = cell.y, w = w, h = h, kind = cell.kind })
	end
	return rects
end

return GridMerge
