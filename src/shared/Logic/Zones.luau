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
export type Effect = "Kill" | "Unfreeze" | "Expire" | "Freeze"

-- Diz se o valor do atributo `FrozenUntil` indica personagem congelado.
function Zones.isFrozen(frozenUntil: unknown): boolean
	return typeof(frozenUntil) == "number"
end

--[[
	Decide o efeito a partir das zonas que o personagem toca e do atributo `FrozenUntil`.
	Prioridade: matar > descongelar > gelo vencido (morte) > congelar. Quem já está congelado e
	continua no gelo não renova o tempo. nil = nada muda.
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
	if typeof(frozenUntil) == "number" then
		if inUnfreeze then
			return "Unfreeze"
		end
		if now >= frozenUntil then
			return "Expire"
		end
		return nil
	end
	if inFreeze and not inUnfreeze then
		return "Freeze"
	end
	return nil
end

return Zones
