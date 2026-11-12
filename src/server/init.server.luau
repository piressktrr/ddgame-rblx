--!strict
-- Bootstrap do servidor: carrega e inicia todos os Services.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Loader = require(ReplicatedStorage.Shared.Util.Loader)

local services = Loader.loadAll(script.Services)
Loader.start(services)

print("[Server] Iniciado")
