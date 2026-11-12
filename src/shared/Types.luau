--!strict
--[[
	Tipos compartilhados entre servidor e cliente.
]]

export type TeamId = string

export type PlayMode = "Solo" | "Team"

export type RaceState = {
	mode: PlayMode,
	teamId: TeamId?,
	checkpointIndex: number,
	startedAt: number?,
}

return {}
