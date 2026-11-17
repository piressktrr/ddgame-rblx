--!strict
--[[
	Regras puras do pulo duplo (ADR 0043, RF-03). Sem acesso a `game` (RNF-04).

	- Uma carga: gasta no segundo pulo no ar; volta ao tocar o chão ou ao prender o gancho.
	- Só vale no ar, depois de `minAirTime` desde que saiu do chão (não dispara junto com o 1º pulo),
	  e nunca enquanto o gancho controla o corpo (preso ou no embalo).
	- Pedidos de pulo colados (`repeatGap`) contam como o mesmo aperto (tecla segurada repete).
]]

export type State = {
	charged: boolean, -- tem o pulo duplo disponível
	airborneSince: number?, -- quando saiu do chão; nil = no chão
	lastRequestAt: number, -- último pedido de pulo (para separar apertos)
}

export type Settings = {
	minAirTime: number,
	repeatGap: number,
}

local DoubleJump = {}

function DoubleJump.new(): State
	return { charged = true, airborneSince = nil, lastRequestAt = -math.huge }
end

-- Atualiza com o que o Humanoid diz agora. Tocar o chão recarrega.
function DoubleJump.setGrounded(state: State, grounded: boolean, now: number)
	if grounded then
		state.airborneSince = nil
		state.charged = true
	elseif state.airborneSince == nil then
		state.airborneSince = now
	end
end

-- Prender o gancho devolve a carga.
function DoubleJump.recharge(state: State)
	state.charged = true
end

-- Chamado a cada pedido de pulo. Devolve true se o pulo duplo deve acontecer agora (e gasta a carga).
function DoubleJump.request(state: State, now: number, hookActive: boolean, settings: Settings): boolean
	local isNewPress = now - state.lastRequestAt > settings.repeatGap
	state.lastRequestAt = now
	if not isNewPress or hookActive or not state.charged then
		return false
	end
	local since = state.airborneSince
	if since == nil or now - since < settings.minAirTime then
		return false
	end
	state.charged = false
	return true
end

return table.freeze(DoubleJump)
