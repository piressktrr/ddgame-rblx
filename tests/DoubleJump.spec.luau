--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local DoubleJump = require(ReplicatedStorage.Shared.Logic.DoubleJump)

local SETTINGS: DoubleJump.Settings = { minAirTime = 0.1, repeatGap = 0.05 }

return function()
	-- Estado no ar desde t = 1.
	local function airborne(): DoubleJump.State
		local state = DoubleJump.new()
		DoubleJump.setGrounded(state, false, 1)
		return state
	end

	describe("new", function()
		it("começa carregado e no chão", function()
			local state = DoubleJump.new()
			expect(state.charged).to.equal(true)
			expect(state.airborneSince).to.equal(nil)
		end)
	end)

	describe("setGrounded", function()
		it("marca quando saiu do chão e não reinicia enquanto continua no ar", function()
			local state = airborne()
			expect(state.airborneSince).to.equal(1)
			DoubleJump.setGrounded(state, false, 2)
			expect(state.airborneSince).to.equal(1)
		end)

		it("tocar o chão recarrega e limpa o tempo no ar", function()
			local state = airborne()
			expect(DoubleJump.request(state, 1.2, false, SETTINGS)).to.equal(true)
			DoubleJump.setGrounded(state, true, 1.5)
			expect(state.charged).to.equal(true)
			expect(state.airborneSince).to.equal(nil)
		end)
	end)

	describe("request", function()
		it("não pula duplo no chão", function()
			expect(DoubleJump.request(DoubleJump.new(), 5, false, SETTINGS)).to.equal(false)
		end)

		it("não pula antes de minAirTime (não dispara junto com o 1º pulo)", function()
			expect(DoubleJump.request(airborne(), 1.05, false, SETTINGS)).to.equal(false)
		end)

		it("pula no ar depois de minAirTime e gasta a carga", function()
			local state = airborne()
			expect(DoubleJump.request(state, 1.2, false, SETTINGS)).to.equal(true)
			expect(state.charged).to.equal(false)
			expect(DoubleJump.request(state, 1.4, false, SETTINGS)).to.equal(false)
		end)

		it("não pula com o gancho ativo e não gasta a carga", function()
			local state = airborne()
			expect(DoubleJump.request(state, 1.2, true, SETTINGS)).to.equal(false)
			expect(state.charged).to.equal(true)
			expect(DoubleJump.request(state, 1.4, false, SETTINGS)).to.equal(true)
		end)

		it("pedidos colados (tecla segurada) contam como o mesmo aperto", function()
			local state = airborne()
			expect(DoubleJump.request(state, 1.2, false, SETTINGS)).to.equal(true)
			DoubleJump.recharge(state)
			expect(DoubleJump.request(state, 1.22, false, SETTINGS)).to.equal(false)
			expect(state.charged).to.equal(true)
			expect(DoubleJump.request(state, 1.3, false, SETTINGS)).to.equal(true)
		end)
	end)

	describe("recharge", function()
		it("prender o gancho devolve a carga no ar", function()
			local state = airborne()
			expect(DoubleJump.request(state, 1.2, false, SETTINGS)).to.equal(true)
			DoubleJump.recharge(state)
			expect(state.charged).to.equal(true)
			expect(DoubleJump.request(state, 1.5, false, SETTINGS)).to.equal(true)
		end)
	end)
end
