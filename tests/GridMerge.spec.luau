--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GridMerge = require(ReplicatedStorage.Shared.Logic.GridMerge)

return function()
	local function cells(list)
		local out = {}
		for _, item in list do
			table.insert(out, { x = item[1], y = item[2], kind = item[3] })
		end
		return out
	end

	it("linha de células iguais vira um retângulo só", function()
		local rects = GridMerge.merge(cells({ { 0, 0, "Freeze" }, { 1, 0, "Freeze" }, { 2, 0, "Freeze" } }))
		expect(#rects).to.equal(1)
		expect(rects[1].w).to.equal(3)
		expect(rects[1].h).to.equal(1)
	end)

	it("bloco 2x2 vira um retângulo 2x2", function()
		local rects = GridMerge.merge(cells({ { 0, 0, "A" }, { 1, 0, "A" }, { 0, 1, "A" }, { 1, 1, "A" } }))
		expect(#rects).to.equal(1)
		expect(rects[1].w).to.equal(2)
		expect(rects[1].h).to.equal(2)
	end)

	it("tipos diferentes não se juntam", function()
		local rects = GridMerge.merge(cells({ { 0, 0, "Freeze" }, { 1, 0, "Kill" }, { 2, 0, "Freeze" } }))
		expect(#rects).to.equal(3)
	end)

	it("forma em L cobre todas as células sem sobrepor", function()
		local rects = GridMerge.merge(
			cells({ { 0, 0, "A" }, { 1, 0, "A" }, { 2, 0, "A" }, { 0, 1, "A" }, { 0, 2, "A" } })
		)
		local area = 0
		for _, rect in rects do
			area += rect.w * rect.h
		end
		expect(area).to.equal(5)
		expect(#rects).to.equal(2)
	end)

	it("célula repetida conta uma vez", function()
		local rects = GridMerge.merge(cells({ { 0, 0, "A" }, { 0, 0, "A" } }))
		expect(#rects).to.equal(1)
	end)
end
