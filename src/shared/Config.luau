--!strict
--[[
	Constantes de gameplay. Nenhum número mágico fora deste arquivo.
	Valores iniciais para playtest; serão ajustados nos testes (e por boosts, ADR 0025).
]]

local Config = {
	-- Câmera lateral 2.5D (ADR 0011).
	Camera = {
		Distance = 46, -- distância da câmera até o plano do jogo
		Height = 6, -- quanto a câmera fica acima do personagem
		LookAhead = 6, -- studs que a câmera adianta na direção em que o personagem anda
		FieldOfView = 50,
		Smoothing = 10, -- maior = segue mais rápido
	},

	-- Plano onde todo o jogo acontece (ADR 0011).
	Plane = {
		Z = 0,
		MaxDrift = 0.05, -- desvio em Z tolerado antes de corrigir
	},

	Hook = {
		Range = 40, -- studs
		Cooldown = 0.25, -- segundos
		PullStrength = 120,
	},

	Freeze = {
		Duration = 15, -- segundos congelado até morrer (ADR 0014)
	},

	Tags = {
		NoHook = "NoHook",
		HookOnce = "HookOnce",
		FreezeZone = "FreezeZone",
		UnfreezeZone = "UnfreezeZone",
		KillZone = "KillZone",
		Checkpoint = "Checkpoint",
		RaceStart = "RaceStart",
		RaceFinish = "RaceFinish",
		BouncerPickup = "BouncerPickup",
		BouncerZone = "BouncerZone",
	},
}

return table.freeze(Config)
