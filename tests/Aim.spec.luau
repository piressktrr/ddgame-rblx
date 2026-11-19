--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Aim = require(ReplicatedStorage.Shared.Logic.Aim)

return function()
	-- Dentro da função: o TestEZ só injeta `expect` no ambiente dela.
	local function expectVector(actual: Vector3?, expected: Vector3)
		expect(actual).to.be.ok()
		local v = actual :: Vector3
		expect(v.X).to.be.near(expected.X, 1e-6)
		expect(v.Y).to.be.near(expected.Y, 1e-6)
		expect(v.Z).to.be.near(expected.Z, 1e-6)
	end

	describe("toPlane", function()
		it("mantém X e Y e troca o Z pelo do plano", function()
			expectVector(Aim.toPlane(Vector3.new(1, 2, 3), 5), Vector3.new(1, 2, 5))
		end)
	end)

	describe("intersectPlane", function()
		it("acha onde o raio cruza o plano", function()
			local hit = Aim.intersectPlane(Vector3.new(0, 0, 10), Vector3.new(1, 0, -1), 0)
			expectVector(hit, Vector3.new(10, 0, 0))
		end)

		it("devolve nil com raio paralelo ao plano", function()
			expect(Aim.intersectPlane(Vector3.new(0, 0, 10), Vector3.new(1, 0, 0), 0)).to.equal(nil)
		end)

		it("devolve nil com raio apontando para longe do plano", function()
			expect(Aim.intersectPlane(Vector3.new(0, 0, 10), Vector3.new(0, 0, 1), 0)).to.equal(nil)
		end)

		it("devolve a própria origem se ela já está no plano", function()
			local hit = Aim.intersectPlane(Vector3.new(3, 4, 2), Vector3.new(0, 1, -1), 2)
			expectVector(hit, Vector3.new(3, 4, 2))
		end)
	end)

	describe("planarDirection", function()
		it("dá a direção unitária ignorando o Z", function()
			local dir = Aim.planarDirection(Vector3.new(0, 0, 0), Vector3.new(3, 4, 7))
			expectVector(dir, Vector3.new(0.6, 0.8, 0))
		end)

		it("devolve nil se os pontos coincidem em X/Y (mesmo com Z diferente)", function()
			expect(Aim.planarDirection(Vector3.new(1, 1, 0), Vector3.new(1, 1, 9))).to.equal(nil)
		end)
	end)

	describe("clampToRange", function()
		it("não mexe no alvo dentro do alcance", function()
			expectVector(Aim.clampToRange(Vector3.zero, Vector3.new(3, 0, 0), 5), Vector3.new(3, 0, 0))
		end)

		it("não mexe no alvo exatamente no alcance", function()
			expectVector(Aim.clampToRange(Vector3.zero, Vector3.new(0, 5, 0), 5), Vector3.new(0, 5, 0))
		end)

		it("puxa o alvo além do alcance para a borda, na mesma direção", function()
			expectVector(Aim.clampToRange(Vector3.zero, Vector3.new(6, 8, 0), 5), Vector3.new(3, 4, 0))
		end)
	end)

	describe("castVector", function()
		it("sempre tem o comprimento do alcance, mesmo com o alvo perto", function()
			expectVector(Aim.castVector(Vector3.zero, Vector3.new(1, 0, 0), 30), Vector3.new(30, 0, 0))
		end)

		it("ignora o Z do alvo", function()
			expectVector(Aim.castVector(Vector3.zero, Vector3.new(3, 4, 9), 10), Vector3.new(6, 8, 0))
		end)

		it("devolve nil com o alvo em cima da origem", function()
			expect(Aim.castVector(Vector3.new(2, 2, 0), Vector3.new(2, 2, 0), 10)).to.equal(nil)
		end)
	end)
end
