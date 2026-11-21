"""Simulador 2D do movimento do jogador (ADR 0052, etapa 1), para medir e validar mapas fora do Studio.

Porta, o mais fiel possível, o código do jogo (todos os números vêm do `Config.luau`):
- `MovementController.luau` + `Shared/Logic/DoubleJump.luau`: andar (WalkSpeed), pulo (JumpPower),
  pulo duplo (zera a queda e põe vy = DoubleJumpVelocity; uma carga, que volta ao tocar o chão ou
  quando o gancho prende; só depois de DoubleJumpMinAirTime no ar; nunca com a corda presa; vale
  no embalo; apertos colados (JumpRequestRepeatGap) contam como um só).
- `HookController/init.luau` (modo "DDNet"): o gancho voa a FireSpeed a partir da posição do disparo
  até Range; prende no primeiro alvo válido, volta se bater em superfície proibida ou esgotar o
  alcance; não dispara de novo enquanto estiver no ar (voando ou voltando) nem antes de Cooldown
  desde o último prender (o aperto fica pendente enquanto o botão estiver segurado); soltar o botão
  solta a corda e o corpo segue no embalo.
- `HookController/DDNetPhysics.luau` + `Shared/Logic/HookRules.luau` (`hookDrag`): puxão a cada
  quadro, proporcional ao tempo em ticks de TickRate (máx. 4 por quadro), DragAccel até DragSpeed,
  DragMinDistance, DragDownFactor, assist/resist com A/D, HangDamping perto do ponto. Prender no
  chão com o ponto não muito para baixo (PullTakeOffMinUp) tira o corpo do chão na hora.
- `HookController/AirBody.luau`: enquanto o gancho controla o corpo (preso e no embalo) a gravidade
  é HookGravity; A/D seguem o controle do DDNet (AirControlAccel/AirControlSpeed no ar,
  GroundControlAccel/WalkSpeed no chão, sem cortar velocidade acima do limite); sem A/D, atrito por
  tick (AirFriction/GroundFriction); pouso rápido no embalo freia com LandingFriction; limite
  horizontal MaxSwingSpeed. O embalo acaba ao pousar com |vx| <= WalkSpeed ou depois de
  MomentumMaxTime no ar; aí o Humanoid volta a controlar.
- Gravidade do mundo: `Movement.Gravity` (o CheckpointService põe em `workspace.Gravity`).

Modelo do corpo: uma caixa de `Zones.CharacterBoxSize` (2 x 5,5) com centro em
`root + CharacterBoxOffsetY`; os pés ficam a 3 studs abaixo do root. O estado (`State.x`, `State.y`)
é a posição do HumanoidRootPart, em studs (X horizontal, Y altura).

Simplificações (o que NÃO está aqui):
- Sem gancho em jogador, sem martelo, sem empurrão entre jogadores, sem modo solo (um jogador só).
- Humanoid fora do gancho: a velocidade horizontal vai a `WalkSpeed * direção` na hora (no Roblox a
  aceleração é altíssima), no chão e no ar (controle total no ar). Sem subida automática de degrau
  (o Humanoid real "sobe" quinas baixas); sem escorregar em rampa; sem rampas (mundo em grade).
- Colisão: caixa contra o mundo, eixo por eixo, sem atrito nem quique (o eixo que bate zera). O
  "chão" do AirBody é um raio no centro com GroundCheckMargin, como no jogo; o do Humanoid é a
  caixa encostada em algo sólido logo abaixo.
- Mão única (OneWay) não é sólida aqui (atravessável) e o gancho a atravessa, como no jogo.
- Zonas (freeze, unfreeze, kill e qualquer outra) vêm de `world.zone_at`/`world.zones_in_box`.
  Congelar ou morrer encerra a simulação (opção `stop_on`); sem dano de queda (o jogo não tem).
- Recarga do pulo duplo ao prender: no jogo ela vem do sinal de mudança do atributo HookActive, que só
  muda de false para true se o corpo não estava no embalo. Portanto prender de novo DURANTE o embalo
  não devolve a carga. O simulador reproduz isso (`recharge_on_reattach=False`).
- Câmera, mira com mouse, rede e servidor (tolerâncias do HookService) ficam de fora: a mira é uma
  direção ou um ponto do plano.
- Passo fixo: controle a `CONTROL_DT` (1/60 s, como o PreSimulation a 60 FPS) e integração a 240 Hz
  (sub-passos), com aceleração constante em cada sub-passo.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol, Sequence

from tools.mapkit.luau_config import ConfigData, load_config

CONTROL_DT = 1 / 60  # s: um quadro do PreSimulation
SUBSTEPS = 4  # integração a 240 Hz, como o solver do Roblox
MAX_TICKS_PER_FRAME = 4  # DDNetPhysics: quadro longo não vira rajada de puxões
INPUT_DEADZONE = 0.1  # AirBody: |A/D| abaixo disso conta como sem direção
GROUND_PROBE = 0.05  # studs abaixo da caixa que contam como "apoiado" para o Humanoid
_BISECT_STEPS = 22
_EPS = 1e-9

Vec = tuple[float, float]

# Superfícies que o raio do gancho devolve.
SURFACE_HOOK = "hook"
SURFACE_NOHOOK = "nohook"
SURFACE_ONCE = "once"


# --------------------------------------------------------------------------------------------------
# Parâmetros (tudo do Config)
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MovementParams:
    """Números do movimento tirados do Config (ver `from_config`)."""

    gravity: float
    walk_speed: float
    jump_power: float
    double_jump_velocity: float
    double_jump_min_air_time: float
    jump_repeat_gap: float
    hook_mode: str
    hook_range: float
    hook_cooldown: float
    tick_rate: float
    fire_speed: float
    drag_accel: float
    drag_speed: float
    drag_min_distance: float
    drag_down_factor: float
    drag_assist_factor: float
    drag_resist_factor: float
    hang_damping: float
    hang_damping_margin: float
    hook_gravity: float
    pull_takeoff_min_up: float
    air_control_accel: float
    air_control_speed: float
    air_friction: float
    ground_control_accel: float
    ground_friction: float
    landing_friction: float
    max_swing_speed: float
    momentum_max_time: float
    ground_check_margin: float
    box_width: float
    box_height: float
    box_offset_y: float
    touch_margin: float

    @staticmethod
    def from_config(cfg: ConfigData) -> "MovementParams":
        mv = cfg["Movement"]
        hk = cfg["Hook"]
        zn = cfg["Zones"]
        box = zn["CharacterBoxSize"]
        return MovementParams(
            gravity=float(mv["Gravity"]),
            walk_speed=float(mv["WalkSpeed"]),
            jump_power=float(mv["JumpPower"]),
            double_jump_velocity=float(mv["DoubleJumpVelocity"]),
            double_jump_min_air_time=float(mv["DoubleJumpMinAirTime"]),
            jump_repeat_gap=float(mv["JumpRequestRepeatGap"]),
            hook_mode=str(hk["Mode"]),
            hook_range=float(hk["Range"]),
            hook_cooldown=float(hk["Cooldown"]),
            tick_rate=float(hk["TickRate"]),
            fire_speed=float(hk["FireSpeed"]),
            drag_accel=float(hk["DragAccel"]),
            drag_speed=float(hk["DragSpeed"]),
            drag_min_distance=float(hk["DragMinDistance"]),
            drag_down_factor=float(hk["DragDownFactor"]),
            drag_assist_factor=float(hk["DragAssistFactor"]),
            drag_resist_factor=float(hk["DragResistFactor"]),
            hang_damping=float(hk["HangDamping"]),
            hang_damping_margin=float(hk["HangDampingMargin"]),
            hook_gravity=float(hk["HookGravity"]),
            pull_takeoff_min_up=float(hk["PullTakeOffMinUp"]),
            air_control_accel=float(hk["AirControlAccel"]),
            air_control_speed=float(hk["AirControlSpeed"]),
            air_friction=float(hk["AirFriction"]),
            ground_control_accel=float(hk["GroundControlAccel"]),
            ground_friction=float(hk["GroundFriction"]),
            landing_friction=float(hk["LandingFriction"]),
            max_swing_speed=float(hk["MaxSwingSpeed"]),
            momentum_max_time=float(hk["MomentumMaxTime"]),
            ground_check_margin=float(hk["GroundCheckMargin"]),
            box_width=float(box[0]),
            box_height=float(box[1]),
            box_offset_y=float(zn["CharacterBoxOffsetY"]),
            touch_margin=float(zn["TouchMargin"]),
        )

    # Geometria do corpo em relação ao root.
    @property
    def half_width(self) -> float:
        return self.box_width / 2

    @property
    def feet_offset(self) -> float:
        """Studs do root até a base da caixa (pés). ~3,0."""
        return self.box_height / 2 - self.box_offset_y

    @property
    def head_offset(self) -> float:
        """Studs do root até o topo da caixa (cabeça). ~2,5."""
        return self.box_height / 2 + self.box_offset_y


_DEFAULT_PARAMS: MovementParams | None = None


def default_params() -> MovementParams:
    """Parâmetros do `src/shared/Config.luau` atual (lidos uma vez)."""
    global _DEFAULT_PARAMS
    if _DEFAULT_PARAMS is None:
        _DEFAULT_PARAMS = MovementParams.from_config(load_config())
    return _DEFAULT_PARAMS


# --------------------------------------------------------------------------------------------------
# Mundo
# --------------------------------------------------------------------------------------------------


class World(Protocol):
    """Interface mínima do mundo. Opcionais: `box_overlaps`, `zones_in_box`, `zone_at`."""

    def is_solid(self, x: float, y: float) -> bool: ...

    def raycast_hook(
        self, origin: Vec, direction: Vec, max_dist: float
    ) -> tuple[Any, ...] | None: ...


# Tipos de célula do GridWorld: (sólido para o corpo, comportamento para o gancho, zona).
# Gancho: "hook"/"nohook"/"once" param o raio; None = o raio atravessa.
CELL_KINDS: dict[str, tuple[bool, str | None, str | None]] = {
    "block": (True, SURFACE_HOOK, None),
    "nohook": (True, SURFACE_NOHOOK, None),
    "once": (True, SURFACE_ONCE, None),
    "hookthrough": (True, None, None),
    "freeze": (False, None, "freeze"),
    "unfreeze": (False, None, "unfreeze"),
    "kill": (False, None, "kill"),
    "oneway": (False, None, None),
}

# Elementos do MapBuilder (`Shared/MapElements.luau`, campo `id`) → tipo de célula.
MAPBUILDER_ELEMENTS: dict[str, str] = {
    "Block": "block",
    "Unhookable": "nohook",
    "HookThrough": "hookthrough",
    "HookOnce": "once",
    "Freeze": "freeze",
    "Unfreeze": "unfreeze",
    "Kill": "kill",
    "OneWay": "oneway",
    "StartLine": "start",
    "FinishLine": "finish",
    "SoloStart": "solostart",
    "SoloEnd": "soloend",
}

# Legenda padrão de `GridWorld.from_rows`.
DEFAULT_LEGEND: dict[str, str | None] = {
    ".": None,
    " ": None,
    "#": "block",
    "X": "nohook",
    "O": "once",
    "T": "hookthrough",
    "F": "freeze",
    "U": "unfreeze",
    "K": "kill",
    "W": "oneway",
    "S": "start",
    "E": "finish",
}


class GridWorld:
    """Mundo em grade de células quadradas (o MapBuilder usa células de 2 studs).

    A célula (ix, iy) cobre x em [ox + ix*c, ox + (ix+1)*c) e y em [oy + iy*c, oy + (iy+1)*c).
    Tipos em `CELL_KINDS`; qualquer outro nome vira zona atravessável com esse nome (ex.: "finish").
    """

    def __init__(
        self,
        cell_size: float = 2.0,
        origin: Vec = (0.0, 0.0),
        cells: dict[tuple[int, int], str] | None = None,
    ):
        self.cell_size = float(cell_size)
        self.origin = (float(origin[0]), float(origin[1]))
        self.cells: dict[tuple[int, int], str] = dict(cells or {})
        self._once_keys: dict[tuple[int, int], int] | None = None

    # --- construção ---
    @classmethod
    def from_rows(
        cls,
        rows: Sequence[str],
        cell_size: float = 2.0,
        origin: Vec = (0.0, 0.0),
        legend: dict[str, str | None] | None = None,
    ) -> "GridWorld":
        """Desenho em texto: a ÚLTIMA linha é iy = 0 (embaixo), a primeira é a mais alta."""
        table = DEFAULT_LEGEND if legend is None else legend
        world = cls(cell_size, origin)
        height = len(rows)
        for row_index, row in enumerate(rows):
            iy = height - 1 - row_index
            for ix, char in enumerate(row):
                kind = table.get(char)
                if kind:
                    world.cells[(ix, iy)] = kind
        return world

    def set_cell(self, ix: int, iy: int, kind: str | None) -> None:
        if kind is None:
            self.cells.pop((ix, iy), None)
        else:
            self.cells[(ix, iy)] = kind
        self._once_keys = None

    def fill_rect(self, x0: float, y0: float, x1: float, y1: float, kind: str | None) -> None:
        """Pinta as células cobertas pelo retângulo em studs (x0 < x1, y0 < y1)."""
        ix0, ix1, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                self.set_cell(ix, iy, kind)

    # --- consultas ---
    def cell_of(self, x: float, y: float) -> tuple[int, int]:
        c = self.cell_size
        return math.floor((x - self.origin[0]) / c), math.floor((y - self.origin[1]) / c)

    def kind_at(self, x: float, y: float) -> str | None:
        return self.cells.get(self.cell_of(x, y))

    def _props(self, kind: str | None) -> tuple[bool, str | None, str | None]:
        if kind is None:
            return (False, None, None)
        return CELL_KINDS.get(kind, (False, None, kind))

    def is_solid(self, x: float, y: float) -> bool:
        return self._props(self.kind_at(x, y))[0]

    def zone_at(self, x: float, y: float) -> str | None:
        return self._props(self.kind_at(x, y))[2]

    def _cell_range(self, x0: float, y0: float, x1: float, y1: float) -> tuple[int, int, int, int]:
        c = self.cell_size
        ox, oy = self.origin
        ix0 = math.floor((x0 - ox) / c + _EPS)
        ix1 = math.ceil((x1 - ox) / c - _EPS) - 1
        iy0 = math.floor((y0 - oy) / c + _EPS)
        iy1 = math.ceil((y1 - oy) / c - _EPS) - 1
        return ix0, ix1, iy0, iy1

    def box_overlaps(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        """A caixa aberta (x0..x1, y0..y1) encosta por dentro em alguma célula sólida?"""
        ix0, ix1, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
        cells = self.cells
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                kind = cells.get((ix, iy))
                if kind is not None and self._props(kind)[0]:
                    return True
        return False

    def _solid_cell(self, ix: int, iy: int) -> bool:
        kind = self.cells.get((ix, iy))
        return kind is not None and self._props(kind)[0]

    def sweep_box(self, x0: float, y0: float, x1: float, y1: float, dx: float, dy: float) -> float:
        """Quanto a caixa anda em UM eixo (dx ou dy, o outro 0) até encostar em algo sólido.

        Devolve o deslocamento permitido, com o mesmo sinal e |valor| <= |pedido|.
        """
        c = self.cell_size
        ox, oy = self.origin
        if dx != 0:
            _, _, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
            if dx > 0:
                first = math.ceil((x1 - ox) / c - _EPS)
                last = math.ceil((x1 + dx - ox) / c - _EPS) - 1
                for col in range(first, last + 1):
                    if any(self._solid_cell(col, iy) for iy in range(iy0, iy1 + 1)):
                        return min(max(ox + col * c - x1, 0.0), dx)
            else:
                first = math.floor((x0 - ox) / c + _EPS) - 1
                last = math.floor((x0 + dx - ox) / c + _EPS)
                for col in range(first, last - 1, -1):
                    if any(self._solid_cell(col, iy) for iy in range(iy0, iy1 + 1)):
                        return max(min(ox + (col + 1) * c - x0, 0.0), dx)
            return dx
        if dy != 0:
            ix0, ix1, _, _ = self._cell_range(x0, y0, x1, y1)
            if dy > 0:
                first = math.ceil((y1 - oy) / c - _EPS)
                last = math.ceil((y1 + dy - oy) / c - _EPS) - 1
                for row in range(first, last + 1):
                    if any(self._solid_cell(ix, row) for ix in range(ix0, ix1 + 1)):
                        return min(max(oy + row * c - y1, 0.0), dy)
            else:
                first = math.floor((y0 - oy) / c + _EPS) - 1
                last = math.floor((y0 + dy - oy) / c + _EPS)
                for row in range(first, last - 1, -1):
                    if any(self._solid_cell(ix, row) for ix in range(ix0, ix1 + 1)):
                        return max(min(oy + (row + 1) * c - y0, 0.0), dy)
            return dy
        return 0.0

    def zones_in_box(self, x0: float, y0: float, x1: float, y1: float) -> set[str]:
        ix0, ix1, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
        found: set[str] = set()
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                zone = self._props(self.cells.get((ix, iy)))[2]
                if zone:
                    found.add(zone)
        return found

    def _once_key(self, cell: tuple[int, int]) -> int:
        """Peças verdes vizinhas contam como a mesma peça (componente conexo)."""
        if self._once_keys is None:
            keys: dict[tuple[int, int], int] = {}
            next_key = 0
            for start, kind in self.cells.items():
                if kind != "once" or start in keys:
                    continue
                stack = [start]
                keys[start] = next_key
                while stack:
                    cx, cy = stack.pop()
                    for nb in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if nb not in keys and self.cells.get(nb) == "once":
                            keys[nb] = next_key
                            stack.append(nb)
                next_key += 1
            self._once_keys = keys
        return self._once_keys.get(cell, -1)

    def raycast_hook(
        self, origin: Vec, direction: Vec, max_dist: float
    ) -> tuple[Vec, str, Any] | None:
        """Raio do gancho (DDA na grade). Devolve (ponto, superfície, chave) ou None.

        A célula onde o raio começa é ignorada (como o Raycast do Roblox, que não acerta a peça em
        que a origem está). Células sem efeito no gancho (hookthrough, zonas, mão única) são
        atravessadas.
        """
        dx, dy = direction
        length = math.hypot(dx, dy)
        if length <= 0 or max_dist <= 0:
            return None
        dx, dy = dx / length, dy / length
        c = self.cell_size
        ox, oy = self.origin
        px, py = (origin[0] - ox) / c, (origin[1] - oy) / c
        ix, iy = math.floor(px), math.floor(py)
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1
        inf = math.inf
        t_delta_x = abs(c / dx) if dx != 0 else inf
        t_delta_y = abs(c / dy) if dy != 0 else inf
        if dx > 0:
            t_max_x = (ix + 1 - px) * c / dx
        elif dx < 0:
            t_max_x = (px - ix) * c / -dx
        else:
            t_max_x = inf
        if dy > 0:
            t_max_y = (iy + 1 - py) * c / dy
        elif dy < 0:
            t_max_y = (py - iy) * c / -dy
        else:
            t_max_y = inf
        while True:
            if t_max_x < t_max_y:
                t = t_max_x
                ix += step_x
                t_max_x += t_delta_x
            else:
                t = t_max_y
                iy += step_y
                t_max_y += t_delta_y
            if t > max_dist:
                return None
            kind = self.cells.get((ix, iy))
            if kind is None:
                continue
            surface = self._props(kind)[1]
            if surface is None:
                continue
            point = (origin[0] + dx * t, origin[1] + dy * t)
            key: Any = ("once", self._once_key((ix, iy))) if surface == SURFACE_ONCE else (ix, iy)
            return point, surface, key


class AnchorWorld:
    """Envolve outro mundo e soma pontos de gancho "soltos" (círculos de `radius` que só o gancho vê).

    Serve para medir o gancho sem que o bloco do ponto atrapalhe o corpo (medida otimista).
    """

    def __init__(self, base: Any, anchors: Sequence[Vec], radius: float = 0.5, surface: str = "hook"):
        self.base = base
        self.anchors = [(float(a[0]), float(a[1])) for a in anchors]
        self.radius = float(radius)
        self.surface = surface
        for name in ("box_overlaps", "sweep_box", "zones_in_box", "zone_at"):
            if hasattr(base, name):
                setattr(self, name, getattr(base, name))

    def is_solid(self, x: float, y: float) -> bool:
        return bool(self.base.is_solid(x, y))

    def raycast_hook(self, origin: Vec, direction: Vec, max_dist: float) -> tuple[Any, ...] | None:
        best = self.base.raycast_hook(origin, direction, max_dist)
        best_t = math.hypot(best[0][0] - origin[0], best[0][1] - origin[1]) if best else math.inf
        length = math.hypot(direction[0], direction[1])
        if length <= 0:
            return best
        dx, dy = direction[0] / length, direction[1] / length
        for i, (ax, ay) in enumerate(self.anchors):
            fx, fy = origin[0] - ax, origin[1] - ay
            b = fx * dx + fy * dy
            c = fx * fx + fy * fy - self.radius * self.radius
            disc = b * b - c
            if disc < 0:
                continue
            t = -b - math.sqrt(disc)
            if t < 0:
                t = 0.0 if c <= 0 else -b + math.sqrt(disc)
            if 0 <= t <= max_dist and t < best_t:
                best_t = t
                best = ((origin[0] + dx * t, origin[1] + dy * t), self.surface, ("anchor", i))
        return best


def _box_overlaps(world: Any, x0: float, y0: float, x1: float, y1: float) -> bool:
    fn = getattr(world, "box_overlaps", None)
    if fn is not None:
        return bool(fn(x0, y0, x1, y1))
    # Genérico: amostra pontos dentro da caixa a cada 0,25 stud.
    nx = max(1, math.ceil((x1 - x0) / 0.25))
    ny = max(1, math.ceil((y1 - y0) / 0.25))
    for i in range(nx + 1):
        x = min(max(x0 + (x1 - x0) * i / nx, x0 + 1e-6), x1 - 1e-6)
        for j in range(ny + 1):
            y = min(max(y0 + (y1 - y0) * j / ny, y0 + 1e-6), y1 - 1e-6)
            if world.is_solid(x, y):
                return True
    return False


def _zones_in_box(world: Any, x0: float, y0: float, x1: float, y1: float) -> set[str]:
    fn = getattr(world, "zones_in_box", None)
    if fn is not None:
        return set(fn(x0, y0, x1, y1))
    zone_at = getattr(world, "zone_at", None)
    if zone_at is None:
        return set()
    found: set[str] = set()
    nx = max(1, math.ceil((x1 - x0) / 0.5))
    ny = max(1, math.ceil((y1 - y0) / 0.5))
    for i in range(nx + 1):
        for j in range(ny + 1):
            zone = zone_at(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny)
            if zone:
                found.add(zone)
    return found


# --------------------------------------------------------------------------------------------------
# Regras puras (portadas do Luau)
# --------------------------------------------------------------------------------------------------


def saturated_add(lo: float, hi: float, current: float, modifier: float) -> float:
    """`HookRules.saturatedAdd`: soma sem passar do limite, sem cortar o que já está além dele."""
    if modifier < 0:
        if current < lo:
            return current
        return max(current + modifier, lo)
    if current > hi:
        return current
    return min(current + modifier, hi)


def hook_drag(
    vx: float, vy: float, to_x: float, to_y: float, move_dir: float, p: MovementParams, ticks: float
) -> Vec:
    """`HookRules.hookDrag` (DDNet HOOK_GRABBED) com os ajustes deste jogo."""
    distance = math.hypot(to_x, to_y)
    if distance <= p.drag_min_distance:
        return vx, vy
    speed = math.hypot(vx, vy)
    k = p.drag_accel / p.tick_rate * ticks / distance
    pull_x, pull_y = to_x * k, to_y * k
    if pull_y < 0:
        pull_y *= p.drag_down_factor
    assisted = (pull_x < 0 and move_dir < 0) or (pull_x > 0 and move_dir > 0)
    pull_x *= p.drag_assist_factor if assisted else p.drag_resist_factor
    nx, ny = vx + pull_x, vy + pull_y
    next_speed = math.hypot(nx, ny)
    if next_speed > p.drag_speed and next_speed >= speed:
        if speed >= p.drag_speed:
            return vx, vy  # acima do limite e aceleraria: descartado (DDNet)
        a = pull_x * pull_x + pull_y * pull_y
        b = 2 * (vx * pull_x + vy * pull_y)
        c = speed * speed - p.drag_speed * p.drag_speed
        t = (-b + math.sqrt(max(b * b - 4 * a * c, 0.0))) / (2 * a)
        t = min(max(t, 0.0), 1.0)
        nx, ny = vx + pull_x * t, vy + pull_y * t
    return nx, ny


# --------------------------------------------------------------------------------------------------
# Entradas
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class InputEvent:
    """Evento de entrada no tempo `t` (segundos desde o início deste `simulate`).

    kind:
    - "move": value = -1 (A), 0 ou 1 (D); vale até o próximo "move";
    - "jump": aperto de Espaço (pulo do chão ou, no ar, pulo duplo; o jogo usa a mesma tecla);
    - "hook": aperta e segura o botão do gancho; value = ("dir", dx, dy) ou ("point", x, y);
    - "aim": troca a mira sem apertar (vale para um disparo pendente); value como em "hook";
    - "unhook": solta o botão do gancho.
    """

    t: float
    kind: str
    value: Any = None


def move(t: float, direction: float) -> InputEvent:
    return InputEvent(t, "move", float(direction))


def jump(t: float) -> InputEvent:
    return InputEvent(t, "jump")


double_jump = jump  # mesma tecla: o pulo no ar é o pulo duplo


def hook(t: float, point: Vec | None = None, direction: Vec | None = None) -> InputEvent:
    if (point is None) == (direction is None):
        raise ValueError("hook: informe point OU direction")
    aim = ("point", *point) if point is not None else ("dir", *direction)  # type: ignore[misc]
    return InputEvent(t, "hook", aim)


def aim(t: float, point: Vec | None = None, direction: Vec | None = None) -> InputEvent:
    if (point is None) == (direction is None):
        raise ValueError("aim: informe point OU direction")
    value = ("point", *point) if point is not None else ("dir", *direction)  # type: ignore[misc]
    return InputEvent(t, "aim", value)


def unhook(t: float) -> InputEvent:
    return InputEvent(t, "unhook")


# --------------------------------------------------------------------------------------------------
# Estado
# --------------------------------------------------------------------------------------------------


@dataclass
class HookState:
    phase: str = "idle"  # idle | flying | retracting | attached
    tip: Vec = (0.0, 0.0)  # ponta do gancho no ar
    direction: Vec = (0.0, 0.0)
    traveled: float = 0.0
    anchor: Vec | None = None  # ponto preso
    surface: str | None = None


@dataclass
class BodyState:
    """O AirBody existe (gancho preso ou embalo)."""

    airborne: bool = False  # o corpo assumiu (Humanoid em `Physics`)
    momentum_start: float | None = None  # embalo: quando soltou


@dataclass
class State:
    """Estado completo do jogador. `x`, `y` = HumanoidRootPart (studs); tempos em `t` absoluto."""

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    t: float = 0.0
    move_dir: float = 0.0
    grounded: bool = False  # caixa apoiada (Humanoid)
    # Pulo duplo (DoubleJump.State)
    dj_charged: bool = True
    airborne_since: float | None = None
    last_jump_request: float = -math.inf
    # Gancho
    hook: HookState = field(default_factory=HookState)
    body: BodyState | None = None
    button_held: bool = False
    fire_pending: bool = False
    aim: tuple | None = None
    last_attach_time: float = -math.inf
    used_once: set = field(default_factory=set)
    hook_active_attr: bool = False  # espelho do atributo HookActive
    # Fim
    dead: bool = False
    frozen: bool = False
    zones: set = field(default_factory=set)

    @staticmethod
    def standing(x: float, floor_y: float, params: MovementParams | None = None) -> "State":
        """Parado em pé com os pés em `floor_y`."""
        p = params or default_params()
        return State(x=x, y=floor_y + p.feet_offset + 1e-6, grounded=True)

    def feet(self, params: MovementParams | None = None) -> float:
        return self.y - (params or default_params()).feet_offset

    def box(self, params: MovementParams | None = None) -> tuple[float, float, float, float]:
        p = params or default_params()
        return (
            self.x - p.half_width,
            self.y - p.feet_offset,
            self.x + p.half_width,
            self.y + p.head_offset,
        )

    @property
    def hook_attached(self) -> bool:
        return self.hook.phase == "attached"

    @property
    def in_momentum(self) -> bool:
        return self.body is not None and not self.hook_attached


@dataclass(frozen=True)
class Sample:
    t: float
    x: float
    y: float
    vx: float
    vy: float
    grounded: bool
    hook_phase: str
    momentum: bool


@dataclass
class SimResult:
    trajectory: list[Sample]
    final: State
    time: float  # segundos simulados nesta chamada
    landed: bool  # terminou apoiado no chão
    dead: bool
    frozen: bool
    zones: set
    events: list[tuple[float, str]]  # (t relativo, o que houve)
    stop_reason: str

    @property
    def max_y(self) -> float:
        return max(s.y for s in self.trajectory)

    def event_times(self, name: str) -> list[float]:
        return [t for t, e in self.events if e == name]


# --------------------------------------------------------------------------------------------------
# Simulador
# --------------------------------------------------------------------------------------------------


class _Sim:
    def __init__(self, state: State, world: Any, p: MovementParams, recharge_on_reattach: bool):
        self.s = state
        self.w = world
        self.p = p
        self.recharge_on_reattach = recharge_on_reattach
        self.t0 = state.t
        self.events: list[tuple[float, str]] = []

    def log(self, what: str) -> None:
        self.events.append((round(self.s.t - self.t0, 6), what))

    # --- chão ---
    def humanoid_grounded(self) -> bool:
        s, p = self.s, self.p
        if s.vy > 1e-6:
            return False
        x0, y0, x1, _ = s.box(p)
        return _box_overlaps(self.w, x0 + 1e-6, y0 - GROUND_PROBE, x1 - 1e-6, y0)

    def body_grounded(self) -> bool:
        """`AirBody.isGrounded`: raio do centro até GroundCheckMargin abaixo dos pés."""
        s, p = self.s, self.p
        if s.vy > 0:
            return False
        feet = s.y - p.feet_offset
        return _box_overlaps(self.w, s.x - 1e-4, feet - p.ground_check_margin, s.x + 1e-4, feet)

    def is_physics_state(self) -> bool:
        return self.s.body is not None and self.s.body.airborne

    def is_grounded_for_jump(self) -> bool:
        """`MovementController.isGrounded`."""
        if self.is_physics_state():
            return self.body_grounded()
        return self.s.grounded

    # --- atributo HookActive / recarga ---
    def publish_hook_active(self) -> None:
        s = self.s
        active = s.hook_attached or s.body is not None
        if active and not s.hook_active_attr:
            s.dj_charged = True  # MovementController: atributo ligou → DoubleJump.recharge
        s.hook_active_attr = active

    # --- pulo ---
    def set_grounded_dj(self, grounded: bool) -> None:
        s = self.s
        if grounded:
            s.airborne_since = None
            s.dj_charged = True
        elif s.airborne_since is None:
            s.airborne_since = s.t

    def on_jump(self) -> None:
        s, p = self.s, self.p
        if s.frozen or s.dead:
            return
        # HookController.tryGroundJump: corpo em `Physics` e apoiado.
        if self.is_physics_state() and self.body_grounded():
            s.vy = p.jump_power
            self.set_grounded_dj(True)
            self.log("jump")
            return
        grounded = self.is_grounded_for_jump()
        self.set_grounded_dj(grounded)
        if not self.is_physics_state() and grounded:
            s.vy = p.jump_power  # pulo do Humanoid (JumpPower)
            s.grounded = False
            s.last_jump_request = s.t
            self.log("jump")
            return
        # DoubleJump.request
        hook_active = s.hook_attached  # corda presa (no embalo vale)
        is_new_press = s.t - s.last_jump_request > p.jump_repeat_gap
        s.last_jump_request = s.t
        if not is_new_press or hook_active or not s.dj_charged:
            return
        since = s.airborne_since
        if since is None or s.t - since < p.double_jump_min_air_time - 1e-9:
            return
        s.dj_charged = False
        s.vy = p.double_jump_velocity
        self.log("double_jump")

    # --- gancho ---
    def aim_direction(self) -> Vec | None:
        s = self.s
        if s.aim is None:
            return None
        kind, ax, ay = s.aim
        if kind == "point":
            ax, ay = ax - s.x, ay - s.y
        length = math.hypot(ax, ay)
        if length <= 1e-9:
            return None
        return ax / length, ay / length

    def process_pending_fire(self) -> None:
        s, p = self.s, self.p
        if not s.fire_pending or s.hook_attached:
            return
        if s.t - s.last_attach_time < p.hook_cooldown - 1e-9:
            return
        s.fire_pending = False
        self.try_fire()

    def try_fire(self) -> None:
        s = self.s
        if s.hook_attached or s.frozen or s.dead:
            return
        if s.hook.phase in ("flying", "retracting"):
            return  # gancho ainda no ar
        direction = self.aim_direction()
        if direction is None:
            return
        s.hook = HookState(phase="flying", tip=(s.x, s.y), direction=direction, traveled=0.0)
        self.log("hook_fire")

    def release(self) -> None:
        s = self.s
        if not s.hook_attached:
            return
        s.hook = HookState()
        if s.body is not None:
            s.body.momentum_start = s.t
        self.publish_hook_active()
        self.log("hook_release")

    def attach(self, point: Vec, surface: str, key: Any) -> None:
        s, p = self.s, self.p
        if s.body is None:
            s.body = BodyState(airborne=not s.grounded)
        s.body.momentum_start = None
        s.hook = HookState(phase="attached", anchor=point, surface=surface)
        if surface == SURFACE_ONCE:
            s.used_once.add(key)
        s.last_attach_time = s.t
        was_active = s.hook_active_attr
        self.publish_hook_active()
        if self.recharge_on_reattach and was_active:
            s.dj_charged = True
        # DDNetPhysics.new: no chão, com o ponto não muito para baixo, o corpo assume (takeOff).
        to_x, to_y = point[0] - s.x, point[1] - s.y
        dist = math.hypot(to_x, to_y)
        if s.grounded and dist > 0 and to_y / dist > p.pull_takeoff_min_up:
            s.body.airborne = True
        self.log("hook_attach")

    def step_flight(self, dt: float) -> None:
        s, p = self.s, self.p
        h = s.hook
        if h.phase not in ("flying", "retracting"):
            return
        step = p.fire_speed * dt
        if h.phase == "retracting":
            to_x, to_y = s.x - h.tip[0], s.y - h.tip[1]
            dist = math.hypot(to_x, to_y)
            if dist <= step:
                s.hook = HookState()
                return
            h.tip = (h.tip[0] + to_x / dist * step, h.tip[1] + to_y / dist * step)
            return
        step = min(step, p.hook_range - h.traveled)
        hit = self.w.raycast_hook(h.tip, h.direction, step) if step > 0 else None
        if hit is not None:
            point, surface = hit[0], hit[1]
            key = hit[2] if len(hit) > 2 else (round(point[0], 3), round(point[1], 3))
            usable = surface == SURFACE_HOOK or (surface == SURFACE_ONCE and key not in s.used_once)
            if usable:
                self.attach((float(point[0]), float(point[1])), surface, key)
                return
            h.tip = (float(point[0]), float(point[1]))
            h.phase = "retracting"
            self.log("hook_refused")
            return
        h.tip = (h.tip[0] + h.direction[0] * step, h.tip[1] + h.direction[1] * step)
        h.traveled += step
        if h.traveled >= p.hook_range - 1e-9:
            h.phase = "retracting"
            self.log("hook_miss")

    # --- AirBody ---
    def body_step(self, dt: float, horizontal: float) -> None:
        s, p = self.s, self.p
        body = s.body
        assert body is not None
        if not body.airborne:
            if s.grounded:
                return  # Humanoid anda normalmente
            body.airborne = True  # enterAir
        grounded = self.body_grounded()
        vx = s.vx
        direction = 1 if horizontal > INPUT_DEADZONE else (-1 if horizontal < -INPUT_DEADZONE else 0)
        ticks = dt * p.tick_rate
        if grounded and body.momentum_start is not None and abs(vx) > p.walk_speed:
            vx *= p.landing_friction**ticks
            if abs(vx) < p.walk_speed:
                vx = math.copysign(p.walk_speed, vx)
        elif direction == 0:
            vx *= (p.ground_friction if grounded else p.air_friction) ** ticks
        else:
            accel = p.ground_control_accel if grounded else p.air_control_accel
            limit = p.walk_speed if grounded else p.air_control_speed
            vx = saturated_add(-limit, limit, vx, direction * accel * dt)
        s.vx = min(max(vx, -p.max_swing_speed), p.max_swing_speed)

    def momentum_over(self) -> bool:
        s, p = self.s, self.p
        body = s.body
        assert body is not None
        if body.momentum_start is None:
            return False
        if not body.airborne:
            return True
        grounded = self.body_grounded()
        if s.t - body.momentum_start >= p.momentum_max_time and not grounded:
            return True
        return grounded and abs(s.vx) <= p.walk_speed

    def end_body(self) -> None:
        self.s.body = None
        self.publish_hook_active()
        self.log("momentum_end")

    # --- um quadro ---
    def control_step(self, dt: float) -> None:
        s, p = self.s, self.p
        frozen = s.frozen
        # MovementController.onStep
        self.set_grounded_dj(self.is_grounded_for_jump())
        # HookController.onPreSimulation
        self.process_pending_fire()
        self.step_flight(dt)
        stepped = False
        if s.hook_attached:
            anchor = s.hook.anchor
            assert anchor is not None and s.body is not None
            if s.body.airborne or not s.grounded:
                ticks = min(dt * p.tick_rate, MAX_TICKS_PER_FRAME)
                to_x, to_y = anchor[0] - s.x, anchor[1] - s.y
                vx, vy = hook_drag(s.vx, s.vy, to_x, to_y, s.move_dir, p, ticks)
                distance = math.hypot(to_x, to_y)
                if 0 < distance <= p.drag_min_distance + p.hang_damping_margin:
                    rx, ry = to_x / distance, to_y / distance
                    along = vx * rx + vy * ry
                    k = along * (1 - p.hang_damping**ticks)
                    vx -= rx * k
                    vy -= ry * k
                s.vx, s.vy = vx, vy
            self.body_step(dt, s.move_dir)
            stepped = True
        if s.body is not None and not stepped:
            if self.momentum_over():
                self.end_body()
            else:
                self.body_step(dt, 0.0 if frozen else s.move_dir)
        # Humanoid controla quando o corpo não assumiu.
        if not self.is_physics_state():
            s.vx = (0.0 if frozen else s.move_dir) * p.walk_speed

    def integrate(self, dt: float) -> None:
        s, p = self.s, self.p
        g = p.hook_gravity if self.is_physics_state() else p.gravity
        sub = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            dx = s.vx * sub
            dy = s.vy * sub - 0.5 * g * sub * sub
            s.vy -= g * sub
            if dx != 0 and self._move_axis(dx, 0):
                s.vx = 0.0
            if dy != 0 and self._move_axis(0, dy):
                s.vy = 0.0
        s.grounded = self.humanoid_grounded()

    def _move_axis(self, dx: float, dy: float) -> bool:
        """Move a caixa por (dx, dy) num eixo; devolve True se bateu (e encosta no obstáculo)."""
        s, p = self.s, self.p
        x0, y0, x1, y1 = s.box(p)
        sweep = getattr(self.w, "sweep_box", None)
        if sweep is not None:
            wanted = dx if dx != 0 else dy
            allowed = sweep(x0, y0, x1, y1, dx, dy)
            if dx != 0:
                s.x += allowed
            else:
                s.y += allowed
            return abs(allowed) < abs(wanted) - 1e-12
        if not _box_overlaps(self.w, x0 + dx, y0 + dy, x1 + dx, y1 + dy):
            s.x += dx
            s.y += dy
            return False
        if _box_overlaps(self.w, x0, y0, x1, y1):
            return True  # já está encostado por dentro (não deveria): não anda
        lo, hi = 0.0, 1.0
        for _ in range(_BISECT_STEPS):
            mid = (lo + hi) / 2
            if _box_overlaps(self.w, x0 + dx * mid, y0 + dy * mid, x1 + dx * mid, y1 + dy * mid):
                hi = mid
            else:
                lo = mid
        s.x += dx * lo
        s.y += dy * lo
        return True

    def check_zones(self) -> set[str]:
        s, p = self.s, self.p
        x0, y0, x1, y1 = s.box(p)
        m = p.touch_margin
        zones = _zones_in_box(self.w, x0 - m, y0 - m, x1 + m, y1 + m)
        s.zones |= zones
        return zones


Controller = Callable[[State, float], Iterable[InputEvent] | None]


def simulate(
    state: State,
    inputs: Iterable[InputEvent | tuple] = (),
    world: Any = None,
    max_time: float = 5.0,
    *,
    params: MovementParams | None = None,
    controller: Controller | None = None,
    stop_on: Sequence[str] = ("kill", "freeze"),
    stop_on_land: bool = False,
    stop_when: Callable[[State], bool] | None = None,
    kill_y: float | None = None,
    dt: float = CONTROL_DT,
    record_every: int = 1,
    recharge_on_reattach: bool = False,
) -> SimResult:
    """Simula a partir de `state` (que não é alterado) por até `max_time` segundos.

    - `inputs`: `InputEvent`s (ou tuplas `(t, kind, value)`) com `t` relativo ao início desta
      chamada; aplicados no primeiro quadro com tempo >= t, na ordem.
    - `controller(state, t_rel)`: chamado a cada quadro antes do passo; devolve eventos a aplicar já.
    - `stop_on`: zonas que encerram ("kill" → morreu, "freeze" → congelou).
    - `stop_on_land`: para quando pousar depois de ter saído do chão.
    - `stop_when(state)`: para quando devolver True (ex.: chegou à linha de chegada).
    - `kill_y`: abaixo disso (pés) conta como morte (queda para fora do mapa).
    - `recharge_on_reattach`: True = prender durante o embalo também devolve o pulo duplo (o jogo
      atual NÃO faz isso; ver o topo do arquivo).
    """
    p = params or default_params()
    if world is None:
        world = GridWorld()
    s = copy.deepcopy(state)
    sim = _Sim(s, world, p, recharge_on_reattach)
    pending = sorted(
        (ev if isinstance(ev, InputEvent) else InputEvent(*ev) for ev in inputs),
        key=lambda ev: ev.t,
    )
    trajectory: list[Sample] = []
    stop_reason = "max_time"
    was_airborne = not s.grounded
    index = 0
    frame = 0
    n_frames = max(0, round(max_time / dt))

    def record() -> None:
        trajectory.append(
            Sample(
                round(s.t - sim.t0, 6),
                s.x,
                s.y,
                s.vx,
                s.vy,
                s.grounded,
                s.hook.phase,
                s.in_momentum,
            )
        )

    def apply(ev: InputEvent) -> None:
        kind = ev.kind
        if kind == "move":
            s.move_dir = max(-1.0, min(1.0, float(ev.value)))
        elif kind == "jump":
            sim.on_jump()
        elif kind == "hook":
            s.aim = tuple(ev.value)
            s.button_held = True
            s.fire_pending = True
            sim.process_pending_fire()
        elif kind == "aim":
            s.aim = tuple(ev.value)
        elif kind == "unhook":
            s.button_held = False
            s.fire_pending = False
            if s.hook.phase == "flying":
                s.hook.phase = "retracting"
            sim.release()
        else:
            raise ValueError(f"entrada desconhecida: {kind!r}")

    record()
    while frame < n_frames:
        t_rel = s.t - sim.t0
        while index < len(pending) and pending[index].t <= t_rel + 1e-9:
            apply(pending[index])
            index += 1
        if controller is not None:
            for ev in controller(s, t_rel) or ():
                apply(ev)
        sim.control_step(dt)
        sim.integrate(dt)
        s.t += dt
        frame += 1
        if s.grounded and was_airborne:
            sim.log("land")
        zones = sim.check_zones()
        if "kill" in zones and "kill" in stop_on:
            s.dead = True
            sim.log("kill")
        if "freeze" in zones:
            if not s.frozen:
                sim.log("freeze")
            s.frozen = True
            if s.hook_attached:
                sim.release()
        if frame % record_every == 0 or s.dead:
            record()
        if s.dead:
            stop_reason = "kill"
            break
        if s.frozen and "freeze" in stop_on:
            stop_reason = "freeze"
            break
        if kill_y is not None and s.y - p.feet_offset < kill_y:
            s.dead = True
            sim.log("fell")
            stop_reason = "fell"
            break
        if stop_on_land and s.grounded and was_airborne:
            stop_reason = "landed"
            break
        if stop_when is not None and stop_when(s):
            stop_reason = "stop_when"
            break
        was_airborne = not s.grounded
    if trajectory[-1].t != round(s.t - sim.t0, 6):
        record()
    return SimResult(
        trajectory=trajectory,
        final=s,
        time=s.t - sim.t0,
        landed=s.grounded,
        dead=s.dead,
        frozen=s.frozen,
        zones=set(s.zones),
        events=sim.events,
        stop_reason=stop_reason,
    )


__all__ = [
    "CONTROL_DT",
    "AnchorWorld",
    "CELL_KINDS",
    "MAPBUILDER_ELEMENTS",
    "GridWorld",
    "InputEvent",
    "MovementParams",
    "Sample",
    "SimResult",
    "State",
    "World",
    "aim",
    "default_params",
    "double_jump",
    "hook",
    "hook_drag",
    "jump",
    "move",
    "saturated_add",
    "simulate",
    "unhook",
]
