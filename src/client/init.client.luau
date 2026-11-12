--!strict
-- Bootstrap do cliente: carrega e inicia todos os Controllers.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Loader = require(ReplicatedStorage.Shared.Util.Loader)

local controllers = Loader.loadAll(script.Controllers)
Loader.start(controllers)

print("[Client] Iniciado")
