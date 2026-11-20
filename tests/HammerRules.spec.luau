return function()
	local ReplicatedStorage = game:GetService("ReplicatedStorage")
	local HammerRules = require(ReplicatedStorage.Shared.Logic.HammerRules)

	local SETTINGS = { PivotHeight = 1.5, Reach = 5.5, Radius = 2.4, Strength = 45, UpBias = 1.1, Lift = 4.5 }

	describe("isHit", function()
		it("acerta quem está colado na direção da mira", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(3, 0, 0), SETTINGS)).to.equal(
				true
			)
		end)

		it("acerta quem está acima, mirando para cima (bater de baixo)", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.yAxis, Vector3.new(0, 5, 0), SETTINGS)).to.equal(
				true
			)
		end)

		it("só acerta perto do martelo: longe na diagonal erra", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(4, -4, 0), SETTINGS)).to.equal(
				false
			)
		end)

		it("acerta quem está colado atrás (corpo encostado no ombro)", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(-1.5, 0, 0), SETTINGS)).to.equal(
				true
			)
		end)

		it("erra quem está longe ou no lado oposto da mira", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(9, 0, 0), SETTINGS)).to.equal(
				false
			)
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(-3, 0, 0), SETTINGS)).to.equal(
				false
			)
		end)

		it("ignora a profundidade (Z) e aceita folga", function()
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(3, 0, 50), SETTINGS)).to.equal(
				true
			)
			expect(HammerRules.isHit(Vector3.zero, Vector3.xAxis, Vector3.new(9, 0, 0), SETTINGS, 1.5)).to.equal(
				true
			)
		end)
	end)

	describe("knockback", function()
		it("de lado: empurra para o lado e para cima", function()
			local push = HammerRules.knockback(Vector3.zero, Vector3.new(3, 0, 0), SETTINGS)
			expect(push.X > 25).to.equal(true)
			expect(push.Y > 30).to.equal(true)
			expect(push.Z).to.equal(0)
		end)

		it("de baixo joga mais alto que de lado", function()
			local below = HammerRules.knockback(Vector3.zero, Vector3.new(0, 5, 0), SETTINGS)
			local side = HammerRules.knockback(Vector3.zero, Vector3.new(3, 0, 0), SETTINGS)
			expect(math.abs(below.Y - 49.5) < 1e-3).to.equal(true)
			expect(below.Y > side.Y).to.equal(true)
		end)

		it("nunca empurra para baixo, mesmo batendo de cima", function()
			local above = HammerRules.knockback(Vector3.zero, Vector3.new(0, -5, 0), SETTINGS)
			expect(above.Y > 0).to.equal(true)
		end)
	end)
end
