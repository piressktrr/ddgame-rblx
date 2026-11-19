--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HookRules = require(ReplicatedStorage.Shared.Logic.HookRules)

local LIMITS: HookRules.RopeLimits = {
	minLength = 2,
	maxLength = 50,
	reelInSpeed = 20,
	reelOutSpeed = 10,
	maxLead = 1,
}

local function expectVector(actual: Vector3, expected: Vector3)
	expect(actual.X).to.be.near(expected.X, 1e-6)
	expect(actual.Y).to.be.near(expected.Y, 1e-6)
	expect(actual.Z).to.be.near(expected.Z, 1e-6)
end

return function()
	describe("surfaceKind", function()
		it("sem tags é Normal", function()
			expect(HookRules.surfaceKind(false, false)).to.equal("Normal")
		end)

		it("NoHook vira NoHook", function()
			expect(HookRules.surfaceKind(true, false)).to.equal("NoHook")
		end)

		it("HookOnce vira HookOnce", function()
			expect(HookRules.surfaceKind(false, true)).to.equal("HookOnce")
		end)

		it("roxo vence quando a peça tem as duas tags", function()
			expect(HookRules.surfaceKind(true, true)).to.equal("NoHook")
		end)
	end)

	describe("canAttach", function()
		it("nunca prende no roxo", function()
			expect(HookRules.canAttach("NoHook", false)).to.equal(false)
			expect(HookRules.canAttach("NoHook", true)).to.equal(false)
		end)

		it("prende no verde só se ainda não usou", function()
			expect(HookRules.canAttach("HookOnce", false)).to.equal(true)
			expect(HookRules.canAttach("HookOnce", true)).to.equal(false)
		end)

		it("sempre prende no normal", function()
			expect(HookRules.canAttach("Normal", false)).to.equal(true)
			expect(HookRules.canAttach("Normal", true)).to.equal(true)
		end)
	end)

	describe("pointOnPart", function()
		local size = Vector3.new(4, 2, 2)

		it("aceita ponto na superfície", function()
			expect(HookRules.pointOnPart(CFrame.new(), size, Vector3.new(2, 0, 0), 0)).to.equal(true)
		end)

		it("aceita ponto fora dentro da folga e recusa além dela", function()
			expect(HookRules.pointOnPart(CFrame.new(), size, Vector3.new(2.05, 0, 0), 0.1)).to.equal(true)
			expect(HookRules.pointOnPart(CFrame.new(), size, Vector3.new(2.2, 0, 0), 0.1)).to.equal(false)
		end)

		it("recusa ponto fora da profundidade (Z) da peça", function()
			expect(HookRules.pointOnPart(CFrame.new(), size, Vector3.new(0, 0, 1.5), 0.1)).to.equal(false)
		end)

		it("respeita a rotação da peça", function()
			local rotated = CFrame.Angles(0, 0, math.rad(90))
			expect(HookRules.pointOnPart(rotated, size, Vector3.new(0, 2, 0), 0.01)).to.equal(true)
			expect(HookRules.pointOnPart(rotated, size, Vector3.new(2, 0, 0), 0.01)).to.equal(false)
		end)
	end)

	describe("isWithinRange", function()
		it("inclui a borda e recusa além dela", function()
			expect(HookRules.isWithinRange(Vector3.zero, Vector3.new(3, 4, 0), 5)).to.equal(true)
			expect(HookRules.isWithinRange(Vector3.zero, Vector3.new(3, 4.01, 0), 5)).to.equal(false)
		end)
	end)

	describe("cooldownReady", function()
		it("fica pronto exatamente no fim do cooldown", function()
			expect(HookRules.cooldownReady(1, 1.4, 0.5)).to.equal(false)
			expect(HookRules.cooldownReady(1, 1.5, 0.5)).to.equal(true)
		end)

		it("fica pronto se nunca usou (-inf)", function()
			expect(HookRules.cooldownReady(-math.huge, 0, 0.5)).to.equal(true)
		end)
	end)

	describe("nextRopeLength", function()
		it("mantém o comprimento sem comando", function()
			expect(HookRules.nextRopeLength(10, 0, 0.1, 10, LIMITS)).to.equal(10)
		end)

		it("sem comando ainda respeita o máximo", function()
			expect(HookRules.nextRopeLength(60, 0, 0.1, 60, LIMITS)).to.equal(50)
		end)

		it("ao recolher, não desce mais que maxLead abaixo da distância real", function()
			-- 10 - 20*0.1 = 8, mas a distância é 10 e maxLead 1: para em 9.
			expect(HookRules.nextRopeLength(10, -1, 0.1, 10, LIMITS)).to.be.near(9, 1e-9)
		end)

		it("com corda frouxa (personagem mais perto), recolhe na velocidade normal", function()
			expect(HookRules.nextRopeLength(10, -1, 0.1, 5, LIMITS)).to.be.near(8, 1e-9)
		end)

		it("parede segurando: comprimento já abaixo da distância não encurta mais", function()
			expect(HookRules.nextRopeLength(9.5, -1, 0.1, 10, LIMITS)).to.be.near(9, 1e-9)
			expect(HookRules.nextRopeLength(9, -1, 0.1, 10, LIMITS)).to.be.near(9, 1e-9)
		end)

		it("recolher nunca aumenta a corda, mesmo esticada", function()
			expect(HookRules.nextRopeLength(10, -1, 0.1, 20, LIMITS)).to.equal(10)
		end)

		it("recolher para no mínimo", function()
			expect(HookRules.nextRopeLength(3, -1, 1, 3, LIMITS)).to.equal(2)
		end)

		it("comando analógico parcial recolhe proporcionalmente", function()
			expect(HookRules.nextRopeLength(10, -0.5, 0.1, 5, LIMITS)).to.be.near(9, 1e-9)
		end)

		it("soltar aumenta na velocidade de soltar e para no máximo", function()
			expect(HookRules.nextRopeLength(10, 1, 0.1, 10, LIMITS)).to.be.near(11, 1e-9)
			expect(HookRules.nextRopeLength(49.5, 1, 1, 49.5, LIMITS)).to.equal(50)
		end)
	end)

	describe("initialRopeLength", function()
		it("usa a distância dentro dos limites", function()
			expect(HookRules.initialRopeLength(1, LIMITS)).to.equal(2)
			expect(HookRules.initialRopeLength(30, LIMITS)).to.equal(30)
			expect(HookRules.initialRopeLength(100, LIMITS)).to.equal(50)
		end)
	end)

	describe("clampSpeed", function()
		it("não mexe abaixo do limite", function()
			expectVector(HookRules.clampSpeed(Vector3.new(3, 4, 0), 10), Vector3.new(3, 4, 0))
		end)

		it("reduz o módulo mantendo a direção", function()
			expectVector(HookRules.clampSpeed(Vector3.new(3, 4, 0), 2.5), Vector3.new(1.5, 2, 0))
		end)

		it("vetor zero continua zero", function()
			expectVector(HookRules.clampSpeed(Vector3.zero, 0), Vector3.zero)
		end)
	end)

	describe("pullSpeed", function()
		it("sem frear usa a velocidade de cruzeiro", function()
			expect(HookRules.pullSpeed(0.5, 100, 50, 5, false)).to.equal(100)
		end)

		it("freando longe do ponto fica no cruzeiro", function()
			expect(HookRules.pullSpeed(1000, 100, 50, 5, true)).to.equal(100)
		end)

		it("freando segue sqrt(2*accel*restante)", function()
			expect(HookRules.pullSpeed(4, 100, 50, 5, true)).to.be.near(20, 1e-9)
		end)

		it("freando não desce do mínimo (nem com restante negativo)", function()
			expect(HookRules.pullSpeed(0, 100, 50, 5, true)).to.equal(5)
			expect(HookRules.pullSpeed(-3, 100, 50, 5, true)).to.equal(5)
		end)

		it("mínimo acima do cruzeiro não quebra: fica no cruzeiro", function()
			expect(HookRules.pullSpeed(0, 10, 50, 20, true)).to.equal(10)
		end)
	end)

	describe("moveToward", function()
		it("anda no máximo maxDelta", function()
			expectVector(HookRules.moveToward(Vector3.zero, Vector3.new(10, 0, 0), 3), Vector3.new(3, 0, 0))
		end)

		it("chega no alvo se estiver perto", function()
			expectVector(HookRules.moveToward(Vector3.zero, Vector3.new(1, 1, 0), 20), Vector3.new(1, 1, 0))
		end)

		it("já no alvo continua no alvo", function()
			expectVector(HookRules.moveToward(Vector3.one, Vector3.one, 0), Vector3.one)
		end)
	end)

	describe("hookDrag (DDNet)", function()
		local DRAG: HookRules.DragSettings = {
			accelPerTick = 10,
			maxSpeed = 50,
			minDistance = 2,
			downFactor = 0.3,
			assistFactor = 0.95,
			resistFactor = 0.75,
		}
		-- Vector3 guarda float32: 1e-4 de folga.
		local function near(actual: Vector3, x: number, y: number, z: number)
			expect(actual.X).to.be.near(x, 1e-4)
			expect(actual.Y).to.be.near(y, 1e-4)
			expect(actual.Z).to.be.near(z, 1e-4)
		end

		it("soma o puxão à velocidade atual, sem substituir (tangencial fica)", function()
			near(HookRules.hookDrag(Vector3.new(20, 0, 0), Vector3.new(0, 10, 0), 0, DRAG), 20, 10, 0)
		end)

		it("para baixo puxa só downFactor", function()
			near(HookRules.hookDrag(Vector3.zero, Vector3.new(0, -10, 0), 0, DRAG), 0, -3, 0)
		end)

		it("A/D no sentido do puxão reforçam o X; contra ou parado, amortecem", function()
			near(HookRules.hookDrag(Vector3.zero, Vector3.new(10, 0, 0), 1, DRAG), 9.5, 0, 0)
			near(HookRules.hookDrag(Vector3.zero, Vector3.new(10, 0, 0), -1, DRAG), 7.5, 0, 0)
			near(HookRules.hookDrag(Vector3.zero, Vector3.new(10, 0, 0), 0, DRAG), 7.5, 0, 0)
		end)

		it("perto do ponto não puxa", function()
			near(HookRules.hookDrag(Vector3.new(1, 2, 0), Vector3.new(1, 1, 0), 0, DRAG), 1, 2, 0)
		end)

		it("não acelera além de maxSpeed, mas a velocidade acima dele é preservada", function()
			near(HookRules.hookDrag(Vector3.new(0, 45, 0), Vector3.new(0, 10, 0), 0, DRAG), 0, 50, 0)
			near(HookRules.hookDrag(Vector3.new(80, 0, 0), Vector3.new(10, 0, 0), 0, DRAG), 80, 0, 0)
		end)

		it("acima de maxSpeed, puxão que aumentaria a velocidade é descartado (não curva)", function()
			near(HookRules.hookDrag(Vector3.new(80, 0, 0), Vector3.new(0, 10, 0), 0, DRAG), 80, 0, 0)
		end)

		it("fração de tick aplica a fração do puxão", function()
			near(HookRules.hookDrag(Vector3.zero, Vector3.new(0, 10, 0), 0, DRAG, 0.5), 0, 5, 0)
		end)

		it("acima de maxSpeed ainda freia", function()
			near(HookRules.hookDrag(Vector3.new(80, 0, 0), Vector3.new(-10, 0, 0), 0, DRAG), 72.5, 0, 0)
		end)

		it("ignora o Z da distância e mantém o Z da velocidade", function()
			near(HookRules.hookDrag(Vector3.new(0, 0, 1), Vector3.new(0, 10, 99), 0, DRAG), 0, 10, 1)
		end)
	end)

	describe("saturatedAdd (DDNet)", function()
		it("soma dentro dos limites e para no limite", function()
			expect(HookRules.saturatedAdd(-10, 10, 0, 4)).to.equal(4)
			expect(HookRules.saturatedAdd(-10, 10, 8, 4)).to.equal(10)
			expect(HookRules.saturatedAdd(-10, 10, -8, -4)).to.equal(-10)
		end)

		it("não corta valor já acima do limite no sentido da soma (embalo preservado)", function()
			expect(HookRules.saturatedAdd(-10, 10, 30, 4)).to.equal(30)
			expect(HookRules.saturatedAdd(-10, 10, -30, -4)).to.equal(-30)
		end)

		it("contra o embalo, freia normalmente", function()
			expect(HookRules.saturatedAdd(-10, 10, 30, -4)).to.equal(26)
		end)
	end)

	describe("isFiniteNumber / isFiniteVector", function()
		it("aceita números comuns", function()
			expect(HookRules.isFiniteNumber(0)).to.equal(true)
			expect(HookRules.isFiniteNumber(-12.5)).to.equal(true)
		end)

		it("recusa NaN e infinitos", function()
			expect(HookRules.isFiniteNumber(0 / 0)).to.equal(false)
			expect(HookRules.isFiniteNumber(math.huge)).to.equal(false)
			expect(HookRules.isFiniteNumber(-math.huge)).to.equal(false)
		end)

		it("recusa vetor com qualquer componente inválida", function()
			expect(HookRules.isFiniteVector(Vector3.new(1, 2, 3))).to.equal(true)
			expect(HookRules.isFiniteVector(Vector3.new(0 / 0, 0, 0))).to.equal(false)
			expect(HookRules.isFiniteVector(Vector3.new(0, math.huge, 0))).to.equal(false)
			expect(HookRules.isFiniteVector(Vector3.new(0, 0, -math.huge))).to.equal(false)
		end)
	end)
end
