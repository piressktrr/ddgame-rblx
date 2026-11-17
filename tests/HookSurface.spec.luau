--!nonstrict
-- nonstrict: describe/it/expect são globais injetados pelo TestEZ no ambiente do spec (ver TOOLS.md).
-- As peças de teste ficam fora do DataModel (Parent nil) e são destruídas no fim: nada vai para o mapa.
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local HookSurface = require(ReplicatedStorage.Shared.Util.HookSurface)

return function()
	local model: Model
	local part: Part

	beforeEach(function()
		model = Instance.new("Model")
		part = Instance.new("Part")
		part.Parent = model
	end)

	afterEach(function()
		model:Destroy()
	end)

	describe("getKind", function()
		it("peça sem tag é Normal", function()
			expect(HookSurface.getKind(part)).to.equal("Normal")
		end)

		it("tag NoHook na própria peça", function()
			CollectionService:AddTag(part, Config.Tags.NoHook)
			expect(HookSurface.getKind(part)).to.equal("NoHook")
		end)

		it("tag HookOnce num ancestral (Model inteiro)", function()
			CollectionService:AddTag(model, Config.Tags.HookOnce)
			expect(HookSurface.getKind(part)).to.equal("HookOnce")
		end)

		it("roxo vence quando há as duas tags", function()
			CollectionService:AddTag(model, Config.Tags.HookOnce)
			CollectionService:AddTag(part, Config.Tags.NoHook)
			expect(HookSurface.getKind(part)).to.equal("NoHook")
		end)
	end)

	describe("getHookOnceKey", function()
		it("é nil para peça que não é verde", function()
			expect(HookSurface.getHookOnceKey(part)).to.equal(nil)
		end)

		it("é a instância com a tag (o Model conta como um uso só)", function()
			local other = Instance.new("Part")
			other.Parent = model
			CollectionService:AddTag(model, Config.Tags.HookOnce)
			expect(HookSurface.getHookOnceKey(part)).to.equal(model)
			expect(HookSurface.getHookOnceKey(other)).to.equal(model)
		end)

		it("prefere a tag mais próxima da peça", function()
			CollectionService:AddTag(model, Config.Tags.HookOnce)
			CollectionService:AddTag(part, Config.Tags.HookOnce)
			expect(HookSurface.getHookOnceKey(part)).to.equal(part)
		end)
	end)
end
