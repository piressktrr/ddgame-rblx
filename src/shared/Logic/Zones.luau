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

return Zones
