--!strict
--[[
	Constantes de gameplay. Nenhum número mágico fora deste arquivo.
	Valores iniciais para playtest; serão ajustados nos testes.
]]

local Config = {
	Hook = {
		Range = 40, -- studs
		Cooldown = 0.25, -- segundos
		PullStrength = 120,
	},

	Freeze = {
		Duration = 3, -- segundos até descongelar sozinho
	},

	Team = {
		MaxSize = 4, -- limite ainda em aberto no design; aqui é só configuração
	},

	Tags = {
		Hookable = "Hookable",
		FreezeZone = "FreezeZone",
		UnfreezeZone = "UnfreezeZone",
		KillZone = "KillZone",
		Checkpoint = "Checkpoint",
		RaceStart = "RaceStart",
		RaceFinish = "RaceFinish",
		SoloOnly = "SoloOnly",
		TeamOnly = "TeamOnly",
	},
}

return table.freeze(Config)
