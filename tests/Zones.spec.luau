--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Zones = require(ReplicatedStorage.Shared.Logic.Zones)

return function()
	describe("isAbove", function()
		-- Placa 4x1x4 no centro: topo em Y = 0.5, base em Y = -0.5; altura extra de 3.
		local size = Vector3.new(4, 1, 4)
		local origin = CFrame.new()

		it("aceita pontos entre a base e a altura acima do topo", function()
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, 0.5, 0))).to.equal(true)
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, 3.5, 0))).to.equal(true)
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, -0.5, 0))).to.equal(true)
		end)

		it("recusa acima da altura e abaixo da base", function()
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, 3.6, 0))).to.equal(false)
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, -0.6, 0))).to.equal(false)
		end)

		it("recusa fora da área (X ou Z)", function()
			expect(Zones.isAbove(origin, size, 3, Vector3.new(2.1, 1, 0))).to.equal(false)
			expect(Zones.isAbove(origin, size, 3, Vector3.new(0, 1, -2.1))).to.equal(false)
		end)

		it("respeita posição e rotação da peça", function()
			-- Peça em (10, 0, 0) girada 90° em Y: o lado de 6 fica no eixo Z do mundo.
			local cframe = CFrame.new(10, 0, 0) * CFrame.Angles(0, math.rad(90), 0)
			local long = Vector3.new(6, 1, 2)
			expect(Zones.isAbove(cframe, long, 3, Vector3.new(10, 1, 2.9))).to.equal(true)
			expect(Zones.isAbove(cframe, long, 3, Vector3.new(12.9, 1, 0))).to.equal(false)
		end)
	end)

	describe("isInside", function()
		local size = Vector3.new(2, 2, 2)

		it("aceita dentro e na borda", function()
			expect(Zones.isInside(CFrame.new(), size, 0, Vector3.zero)).to.equal(true)
			expect(Zones.isInside(CFrame.new(), size, 0, Vector3.new(1, 1, 1))).to.equal(true)
		end)

		it("usa a margem em cada lado", function()
			expect(Zones.isInside(CFrame.new(), size, 0.5, Vector3.new(0, 1.5, 0))).to.equal(true)
			expect(Zones.isInside(CFrame.new(), size, 0.5, Vector3.new(0, 1.6, 0))).to.equal(false)
			expect(Zones.isInside(CFrame.new(), size, 0, Vector3.new(0, 0, -1.1))).to.equal(false)
		end)
	end)

	describe("isFrozen", function()
		it("só número conta como congelado", function()
			expect(Zones.isFrozen(10)).to.equal(true)
			expect(Zones.isFrozen(nil)).to.equal(false)
			expect(Zones.isFrozen("x")).to.equal(false)
			expect(Zones.isFrozen(true)).to.equal(false)
		end)
	end)

	describe("pickEffect", function()
		-- Argumentos: inKill, inUnfreeze, inFreeze, frozenUntil, now.
		it("zona mortal vence tudo", function()
			expect(Zones.pickEffect(true, true, true, 5, 1)).to.equal("Kill")
			expect(Zones.pickEffect(true, false, false, nil, 1)).to.equal("Kill")
		end)

		it("congelado na zona de descongelar volta ao normal, mesmo com o tempo vencido", function()
			expect(Zones.pickEffect(false, true, false, 20, 10)).to.equal("Unfreeze")
			expect(Zones.pickEffect(false, true, true, 5, 10)).to.equal("Unfreeze")
		end)

		it("congelado com o tempo vencido morre", function()
			expect(Zones.pickEffect(false, false, false, 10, 10)).to.equal("Expire")
			expect(Zones.pickEffect(false, false, true, 5, 10)).to.equal("Expire")
		end)

		it("congelado no gelo não renova o tempo", function()
			expect(Zones.pickEffect(false, false, true, 20, 10)).to.equal(nil)
		end)

		it("gelo congela, mas não se também estiver na zona de descongelar", function()
			expect(Zones.pickEffect(false, false, true, nil, 10)).to.equal("Freeze")
			expect(Zones.pickEffect(false, true, true, nil, 10)).to.equal(nil)
		end)

		it("fora de zona e sem gelo nada muda", function()
			expect(Zones.pickEffect(false, false, false, nil, 10)).to.equal(nil)
		end)
	end)
end
