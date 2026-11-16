--!strict
--[[
	Lista única dos RemoteEvents do jogo (IMPLEMENTATION_PLAN §1). O servidor cria todos no bootstrap
	(`Net.createAll`); o cliente espera cada um aparecer (`Net.get`). Blink/ByteNet só se o volume pedir.

	Gancho (Fase 1):
	  HookAttach   cliente -> servidor   (attachId: number, part: BasePart, point: Vector3)
	  HookDetach   cliente -> servidor   (attachId: number)
	  HookRejected servidor -> cliente   (attachId: number, reason: string)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

export type RemoteName = "HookAttach" | "HookDetach" | "HookRejected"

local REMOTE_NAMES: { RemoteName } = { "HookAttach", "HookDetach", "HookRejected" }
local FOLDER_NAME = "Remotes"

local Net = {}

local function getFolder(): Instance
	if not RunService:IsServer() then
		return ReplicatedStorage:WaitForChild(FOLDER_NAME)
	end
	local existing = ReplicatedStorage:FindFirstChild(FOLDER_NAME)
	if existing then
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = FOLDER_NAME
	folder.Parent = ReplicatedStorage
	return folder
end

-- Devolve o RemoteEvent. No servidor cria se ainda não existir; no cliente espera (pode ceder).
function Net.get(name: RemoteName): RemoteEvent
	local folder = getFolder()
	if not RunService:IsServer() then
		return folder:WaitForChild(name) :: RemoteEvent
	end
	local existing = folder:FindFirstChild(name)
	if existing then
		return existing :: RemoteEvent
	end
	local remote = Instance.new("RemoteEvent")
	remote.Name = name
	remote.Parent = folder
	return remote
end

-- Só no servidor: cria todos os remotes de uma vez, antes de qualquer jogador precisar deles.
function Net.createAll()
	assert(RunService:IsServer(), "[Net] createAll só pode rodar no servidor")
	for _, name in REMOTE_NAMES do
		Net.get(name)
	end
end

return Net
