--!strict
-- Bootstrap do servidor: carrega e inicia todos os Services.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Loader = require(ReplicatedStorage.Shared.Util.Loader)
local Net = require(ReplicatedStorage.Shared.Net)

-- Os remotes existem antes de qualquer Service ou cliente precisar deles.
Net.createAll()

local services = Loader.loadAll(script.Services)
Loader.start(services)

print("[Server] Iniciado")
