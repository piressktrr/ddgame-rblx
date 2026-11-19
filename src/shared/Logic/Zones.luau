--!strict
-- Lógica pura de zonas (sem acesso a `game`), para poder ser testada fora do Studio.

local Zones = {}

-- Diz se `point` está sobre a peça descrita por `cframe` e `size`: dentro da área dela (X e Z
-- locais) e entre a base da peça e `height` studs acima do topo.
function Zones.isAbove(cframe: CFrame, size: Vector3, height: number, point: Vector3): boolean
	local localPoint = cframe:PointToObjectSpace(point)
	return math.abs(localPoint.X) <= size.X / 2
		and math.abs(localPoint.Z) <= size.Z / 2
		and localPoint.Y >= -size.Y / 2
		and localPoint.Y <= size.Y / 2 + height
end

-- Diz se `point` está dentro da caixa descrita por `cframe` e `size`, com `margin` studs de folga
-- em cada lado.
function Zones.isInside(cframe: CFrame, size: Vector3, margin: number, point: Vector3): boolean
	local localPoint = cframe:PointToObjectSpace(point)
	return math.abs(localPoint.X) <= size.X / 2 + margin
		and math.abs(localPoint.Y) <= size.Y / 2 + margin
		and math.abs(localPoint.Z) <= size.Z / 2 + margin
end

-- Efeito de zona a aplicar num personagem nesta conferência (RF-20, RF-22, RF-24, RF-25).
-- "Freeze" = congela ou renova o gelo (está dentro); "Thaw" = o gelo acabou depois de sair.
export type Effect = "Kill" | "Unfreeze" | "Freeze" | "Thaw"

-- Diz se o valor do atributo `FrozenUntil` indica personagem congelado.
function Zones.isFrozen(frozenUntil: unknown): boolean
	return typeof(frozenUntil) == "number"
end

--[[
	Decide o efeito a partir das zonas que o personagem toca e do atributo `FrozenUntil` (como no
	DDNet). Prioridade: morte > descongelar > dentro do gelo (congela/renova) > gelo acabou.
	`FrozenUntil` é quando o gelo acaba se o personagem não estiver mais no freeze. nil = nada muda.
]]
function Zones.pickEffect(
	inKill: boolean,
	inUnfreeze: boolean,
	inFreeze: boolean,
	frozenUntil: unknown,
	now: number
): Effect?
	if inKill then
		return "Kill"
	end
	if inUnfreeze then
		return if typeof(frozenUntil) == "number" then "Unfreeze" else nil
	end
	if inFreeze then
		return "Freeze"
	end
	if typeof(frozenUntil) == "number" and now >= frozenUntil then
		return "Thaw"
	end
	return nil
end

return Zones
