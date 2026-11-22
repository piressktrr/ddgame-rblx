"""Validador de mapa (ADR 0052, etapa 3): "joga" o mapa sozinho pela simulação e mede o que achou.

Rodar da raiz do repositório:

    python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json            # relatório completo
    python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json --quick    # menos manobras, mais rápido
    python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json --out pasta/validacao-x.md --jobs 4

Grava o relatório (`.md`) e o desenho (`.svg`, mesmo nome) — por padrão em
`memory-palace/04-game-design/estudos/validacao-<pasta do mapa>.md` — e imprime um resumo.

Como funciona (detalhes e limitações no `tools/mapkit/README.md`, seção "Validador"):

1. **Nós.** Acha as PLATAFORMAS (trechos contínuos de chão onde a caixa 2 x 5,5 do corpo fica em pé sem
   tocar Kill/Freeze) e põe alguns pontos em cada uma (as duas bordas e pontos a cada ~20 studs).
   Pendurado num ponto de gancho também vira nó (nó "pendurado"), para correntes de gancho no teto.
2. **Arestas.** De cada nó alcançado, simula com `physics.py` um conjunto pequeno de manobras (andar e
   cair, pulo parado/para os lados, pulo duplo em vários momentos, gancho em cada alvo visível com
   soltar cedo/tarde e pulo duplo no embalo, gancho a partir do topo de um pulo). Cada simulação que
   pousa numa plataforma (ou fica pendurada) vira aresta com custo = tempo, um rótulo do tipo de manobra
   e uma JANELA DE ACERTO (quantas variações vizinhas da mesma manobra também dão certo, em segundos).
   Morte (Kill) e gelo (Freeze, sem parceiro) contam como fracasso daquela variação.
3. **Análises.** Alcançabilidade (spawn -> checkpoints -> chegada), ilhas, armadilhas, "só gancho",
   bifurcações, desafio (janelas), alturas, alcance do gancho e tempo estimado. As rotas escolhidas
   têm as janelas refinadas (cada entrada mexida quadro a quadro).

Tudo sai do `Config.luau` (via `physics.default_params()` e `maps/metrics.json`).
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

if __package__ in (None, ""):
    # Rodado como script (python -I tools/mapkit/validate.py): a raiz do repo entra no sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.mapkit.luau_config import REPO_ROOT, load_config  # noqa: E402
from tools.mapkit.physics import (  # noqa: E402
    GridWorld,
    InputEvent,
    MovementParams,
    SimResult,
    State,
    default_params,
    simulate,
)
from tools.mapkit.tiles import RULES, TileMap  # noqa: E402

METRICS_PATH = REPO_ROOT / "maps" / "metrics.json"
DEFAULT_OUT_DIR = REPO_ROOT / "memory-palace" / "04-game-design" / "estudos"
FRAME = 1 / 60
WINDOW_CAP = 1.0  # s: janela a partir da qual a manobra conta como "sem precisão" (trivial)
INF = math.inf

# Perfis de jogador (erro de tempo = desvio padrão, em segundos) para risco e tempo esperado.
SIGMA_MEDIUM = 0.06  # jogador médio
REACTION = 0.25  # s de "pensar" antes de cada manobra (jogador médio)
RETRY = 4.0  # s perdidos por erro (voltar, refazer)
MOMENTUM_FACTOR = 1.15  # soltar acima de 1,15 x WalkSpeed = embalo
STEP_MAX = 60.0  # studs: desnível máximo que conta como "degrau" (acima disso é parede)

# Estágios do map01 (`tools/map_layout.py`, GROUPS; nomes das placas). A primeira caixa que contém
# o ponto dá o nome. Outros mapas: sem estágios (tudo "Mapa").
STAGES: dict[str, list[tuple[str, float, float, float, float]]] = {
    "Map01": [
        ("R1", 420, 60, 460, 100),
        ("R2", 880, 20, 920, 260),
        ("R3", 1320, 266, 1360, 300),
        ("R4", 1800, 436, 1840, 470),
        ("R5", 1820, 816, 1900, 860),
        ("R6", 1260, 856, 1300, 890),
        ("R7", 800, 830, 840, 890),
        ("R8", 200, 440, 240, 830),
        ("E1", 0, 0, 420, 140),
        ("E2", 460, 0, 880, 280),
        ("E3", 920, 0, 1320, 320),
        ("E4", 1360, 240, 1900, 466),
        ("E5", 1680, 466, 1900, 820),
        ("E6", 1300, 816, 1900, 910),
        ("E7", 800, 830, 1260, 960),
        ("E8", 200, 440, 800, 890),
        ("E9", 0, 440, 200, 1160),
    ]
}
STAGE_NAMES = {
    "E1": "Clareira dos Troncos",
    "E2": "Copa e Raízes",
    "E3": "Garganta Gelada",
    "E4": "Escombros Flutuantes",
    "E5": "Torre Partida",
    "E6": "Pontes Quebradas",
    "E7": "Galeria dos Cristais",
    "E8": "Coração da Montanha",
    "E9": "Torre do Mago",
}


# --------------------------------------------------------------------------------------------------
# Configuração das manobras
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    node_spacing: int = 10  # células entre pontos de uma plataforma
    max_nodes_per_platform: int = 8
    jump_offsets: tuple[int, ...] = (-6, -3, -1, 0, 1, 3, 6)  # células: onde pular, em volta do ponto
    jump_stop_times: tuple[float, ...] = (0.15, 0.3, 0.5, 0.75)  # solta A/D no ar
    dj_times: tuple[float, ...] = (0.2, 0.35, 0.5, 0.7, 0.9)
    hook_sectors: int = 7  # setores de -30 a 210 graus; 1 alvo (o mais longe) por setor
    release_times: tuple[float, ...] = (0.15, 0.25, 0.35, 0.45, 0.6, 0.8, 1.1)  # denso no começo (subidas)
    apex_targets: int = 3
    apex_release: tuple[float, ...] = (0.35, 0.7)
    hang_targets: int = 4
    hang_release: tuple[float, ...] = (0.3, 0.6)
    hang_per_bucket: int = 4  # nós pendurados por quadrado de 40 x 40 studs (limita a densidade)
    walk_variants: bool = True

    @staticmethod
    def quick() -> "Settings":
        return Settings(
            node_spacing=16,
            max_nodes_per_platform=6,
            jump_offsets=(-3, -1, 0, 1, 3),
            jump_stop_times=(0.2, 0.5),
            dj_times=(0.3, 0.55, 0.8),
            hook_sectors=5,
            release_times=(0.2, 0.3, 0.4, 0.55, 0.7, 0.9),
            apex_targets=2,
            apex_release=(0.5,),
            hang_targets=3,
            hang_release=(0.5,),
            hang_per_bucket=2,
            walk_variants=False,
        )


def load_metrics() -> dict[str, Any]:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text(encoding="utf8"))
    from tools.mapkit.metrics import compute_metrics  # só se o arquivo não existir

    return {"metrics": compute_metrics(quick=True)}


def screen_limits(metrics: dict[str, Any], p: MovementParams) -> dict[str, float]:
    """Alvo do gancho na tela (do root) e o que a câmera mostra abaixo dos pés."""
    m = metrics["metrics"]
    hook = m.get("hook", {})
    cam = m.get("camera", {})
    up = float(hook.get("on_screen_up", cam.get("visible_up_from_root", 35.8)))
    down = float(hook.get("on_screen_down", cam.get("visible_down_from_root", 23.8)))
    side = float(hook.get("on_screen_side", p.hook_range))
    return {
        "up": up,
        "down": down,
        "side": side,
        "below_feet": float(cam.get("visible_down_from_root", 23.8)) - p.feet_offset,
    }


def rules_by_id(metrics: dict[str, Any]) -> dict[str, float]:
    return {r["id"]: float(r["studs"]) for r in metrics["metrics"].get("rules", [])}


# --------------------------------------------------------------------------------------------------
# Mundo rápido para o simulador (grade do TileMap com as consultas de caixa do GridWorld)
# --------------------------------------------------------------------------------------------------

_ELEMENT_KIND = {
    "Block": "block",
    "Unhookable": "nohook",
    "HookOnce": "once",
    "HookThrough": "hookthrough",
    "OneWay": "oneway",
}


class TileSimWorld(GridWorld):
    """`GridWorld` montado de um `TileMap`, com zonas sólidas (`collide` do arquivo, mapas antigos).

    Usa as consultas de caixa do GridWorld (`sweep_box`, `box_overlaps`, `zones_in_box`) — bem mais
    rápidas que o caminho genérico do simulador. Regras iguais às do `TileWorld` (tiles.py): mão única
    atravessável (como no simulador), zona sólida sem tag de gancho segura o gancho. Fora da grade = ar.
    """

    def __init__(self, tiles: TileMap):
        super().__init__(float(tiles.cell), (float(tiles.origin[0]), float(tiles.origin[1])))
        self.tiles = tiles
        self.kind_props: dict[str, tuple[bool, str | None, str | None]] = {
            "block": (True, "hook", None),
            "nohook": (True, "nohook", None),
            "once": (True, "once", None),
            "hookthrough": (True, None, None),
            "oneway": (False, None, None),
        }
        names: dict[str, str] = {}
        for element, rule in RULES.items():
            if element in _ELEMENT_KIND:
                names[element] = _ELEMENT_KIND[element]
                continue
            solid = tiles.collides(element)
            kind = f"zone:{element}"
            surface = (rule.hook or "hook") if solid and rule.hook != "through" else None
            self.kind_props[kind] = (solid, surface, rule.zone)
            names[element] = kind
        self.cells = {cell: names[element] for cell, element in tiles.cells.items()}
        # conjuntos para as consultas quentes do simulador
        self.solid = {c for c, k in self.cells.items() if self.kind_props[k][0]}
        self.zone_cells = {c: self.kind_props[k][2] for c, k in self.cells.items() if self.kind_props[k][2]}

    def _props(self, kind: str | None) -> tuple[bool, str | None, str | None]:
        if kind is None:
            return (False, None, None)
        return self.kind_props[kind]

    def _solid_cell(self, ix: int, iy: int) -> bool:  # usado pelo sweep_box do GridWorld
        return (ix, iy) in self.solid

    def box_overlaps(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        ix0, ix1, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
        solid = self.solid
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                if (ix, iy) in solid:
                    return True
        return False

    def zones_in_box(self, x0: float, y0: float, x1: float, y1: float) -> set[str]:
        ix0, ix1, iy0, iy1 = self._cell_range(x0, y0, x1, y1)
        zc = self.zone_cells
        found: set[str] = set()
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                z = zc.get((ix, iy))
                if z:
                    found.add(z)
        return found

    def solid_cell(self, i: int, j: int) -> bool:
        return (i, j) in self.solid

    def surface_cell(self, i: int, j: int) -> str | None:
        kind = self.cells.get((i, j))
        return None if kind is None else self.kind_props[kind][1]

    def zone_cell(self, i: int, j: int) -> str | None:
        kind = self.cells.get((i, j))
        return None if kind is None else self.kind_props[kind][2]


# --------------------------------------------------------------------------------------------------
# Geometria: plataformas, zonas de checkpoint, área jogável
# --------------------------------------------------------------------------------------------------


@dataclass
class Platform:
    pid: int
    j: int  # linha da célula onde ficam os pés (o chão é a linha j - 1)
    i0: int  # primeira coluna
    i1: int  # última coluna (inclusive)
    floor_y: float  # studs
    x0: float  # root mais à esquerda (centro da coluna i0)
    x1: float  # root mais à direita
    in_region: bool = True  # ligada por ar ao spawn (senão é um bolsão fechado na rocha)
    zone_x: dict[str, float] = field(default_factory=dict)  # zona -> x (root) mais perto do meio
    stage: str = "Mapa"

    @property
    def width(self) -> float:
        return self.x1 - self.x0 + 2.0  # studs de chão

    def label(self) -> str:
        return f"x {self.x0 - 1:.0f}..{self.x1 + 1:.0f}, chão y {self.floor_y:.0f}"


@dataclass(frozen=True)
class ZoneBox:
    """Peça de checkpoint/chegada: conta com o root na coluna acima dela (Zones.isAbove)."""

    zid: str  # "cp1", "cp2", ..., "fin"
    order: int
    x0: float
    x1: float
    y0: float
    y1: float  # topo da peça + ZoneHeight

    def contains(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass
class Geometry:
    tiles: TileMap
    world: TileSimWorld
    params: MovementParams
    platforms: list[Platform]
    plat_at: dict[tuple[int, int], int]  # (coluna, j dos pés) -> pid
    zones: list[ZoneBox]  # na ordem da corrida (a chegada por último)
    spawn: tuple[float, float]  # root x, chão y
    spawn_pid: int | None
    region_size: int
    stages: list[tuple[str, float, float, float, float]]

    def stage_of(self, x: float, y: float) -> str:
        for name, x1, y1, x2, y2 in self.stages:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return "Mapa"

    def col_x(self, i: int) -> float:
        return self.tiles.origin[0] + (i + 0.5) * self.tiles.cell

    def platform_of(self, x: float, feet_y: float) -> int | None:
        """Plataforma em que o corpo está apoiado (x do root, y dos pés)."""
        t = self.tiles
        j = round((feet_y - t.origin[1]) / t.cell)
        i = math.floor((x - t.origin[0]) / t.cell)
        for di in (0, -1, 1):
            pid = self.plat_at.get((i + di, j))
            if pid is not None:
                return pid
        return None


def _zone_boxes(tm: TileMap, cfg: Any) -> list[ZoneBox]:
    zh = float(cfg.get("Checkpoint.ZoneHeight", 10))
    fh = float(cfg.get("Race.FinishZoneHeight", 10))
    groups: dict[tuple[str, int], list[tuple[int, int]]] = defaultdict(list)
    for (i, j), element in tm.cells.items():
        if element == "Checkpoint":
            order = int(tm.attributes.get((i, j), {}).get("Order", 0))
            groups[("cp", order)].append((i, j))
        elif element == "FinishLine":
            groups[("fin", 0)].append((i, j))
    boxes: list[ZoneBox] = []
    cps = sorted(order for kind, order in groups if kind == "cp")
    for kind, order in sorted(groups, key=lambda k: (k[0] == "fin", k[1])):
        cells = groups[(kind, order)]
        for comp in _components(set(cells)):
            i0 = min(c[0] for c in comp)
            i1 = max(c[0] for c in comp)
            j0 = min(c[1] for c in comp)
            j1 = max(c[1] for c in comp)
            x0, y0 = tm.cell_min(i0, j0)
            x1, y1 = tm.cell_min(i1 + 1, j1 + 1)
            if kind == "cp":
                boxes.append(ZoneBox(f"cp{order}", order, x0, x1, y0, y1 + zh))
            else:
                boxes.append(ZoneBox("fin", (cps[-1] + 1) if cps else 1, x0, x1, y0, y1 + fh))
    return boxes


def _components(cells: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    out = []
    seen: set[tuple[int, int]] = set()
    for start in sorted(cells):
        if start in seen:
            continue
        comp = [start]
        seen.add(start)
        stack = [start]
        while stack:
            i, j = stack.pop()
            for nb in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    comp.append(nb)
                    stack.append(nb)
        out.append(comp)
    return out


def build_geometry(
    tm: TileMap,
    params: MovementParams | None = None,
    cfg: Any = None,
    stages: list[tuple[str, float, float, float, float]] | None = None,
) -> Geometry:
    """`stages`: caixas (nome, x1, y1, x2, y2) em studs que dão nome aos trechos; padrão = `STAGES[tm.name]`
    (só o map01 tem). O montador (`assemble.py`) passa uma caixa por trecho."""
    p = params or default_params()
    cfg = cfg if cfg is not None else load_config()
    world = TileSimWorld(tm)
    solid = world.solid_cell
    cell = float(tm.cell)
    body_cells = max(1, math.ceil(p.box_height / cell - 1e-9))  # 3 células de 2 studs
    zones = _zone_boxes(tm, cfg)
    stages = list(stages) if stages is not None else STAGES.get(tm.name, [])

    # Colunas em pé: chão sólido embaixo, corpo cabe, sem tocar zona que mata/congela.
    standable: set[tuple[int, int]] = set()
    for (i, jb), kind in world.cells.items():
        if not world.kind_props[kind][0]:
            continue
        j = jb + 1
        if j + body_cells > tm.height or i < 0 or i >= tm.width:
            continue
        if any(solid(i, j + k) for k in range(body_cells)):
            continue
        x = tm.origin[0] + (i + 0.5) * cell
        feet = tm.origin[1] + j * cell
        m = p.touch_margin
        bad = world.zones_in_box(x - p.half_width - m, feet - m, x + p.half_width + m, feet + p.box_height + m)
        if "kill" in bad or "freeze" in bad:
            continue
        standable.add((i, j))

    # Área jogável: posições do corpo (1 x 3 células livres) ligadas ao spawn.
    def fits(i: int, j: int) -> bool:
        if not (0 <= i < tm.width and 0 <= j <= tm.height - body_cells):
            return False
        return not any(solid(i, j + k) for k in range(body_cells))

    region: set[tuple[int, int]] = set()
    if tm.spawn is not None and fits(*tm.spawn):
        region.add(tm.spawn)
        stack = [tm.spawn]
        while stack:
            i, j = stack.pop()
            for nb in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if nb not in region and fits(*nb):
                    region.add(nb)
                    stack.append(nb)

    platforms: list[Platform] = []
    plat_at: dict[tuple[int, int], int] = {}
    for i, j in sorted(standable, key=lambda c: (c[1], c[0])):
        if (i, j) in plat_at:
            continue
        k = i
        while (k + 1, j) in standable:
            k += 1
        pid = len(platforms)
        x0 = tm.origin[0] + (i + 0.5) * cell
        x1 = tm.origin[0] + (k + 0.5) * cell
        floor_y = tm.origin[1] + j * cell
        plat = Platform(pid, j, i, k, floor_y, x0, x1)
        plat.in_region = any((c, j) in region for c in range(i, k + 1)) if region else True
        plat.stage = _stage_of(stages, (x0 + x1) / 2, floor_y + 1)
        root_y = floor_y + p.feet_offset
        mid = (x0 + x1) / 2
        for z in zones:
            best = None
            for c in range(i, k + 1):
                x = tm.origin[0] + (c + 0.5) * cell
                if z.contains(x, root_y) and (best is None or abs(x - mid) < abs(best - mid)):
                    best = x
            if best is not None and z.zid not in plat.zone_x:
                plat.zone_x[z.zid] = best
        for c in range(i, k + 1):
            plat_at[(c, j)] = pid
        platforms.append(plat)

    spawn_pid = None
    spawn = (0.0, 0.0)
    if tm.spawn is not None:
        sx, sy = tm.cell_min(*tm.spawn)
        spawn = (sx + cell / 2, sy)
        spawn_pid = plat_at.get(tm.spawn)
    return Geometry(tm, world, p, platforms, plat_at, zones, spawn, spawn_pid, len(region), stages)


def _stage_of(stages: list, x: float, y: float) -> str:
    for name, x1, y1, x2, y2 in stages:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return name
    return "Mapa"


def node_positions(plat: Platform, s: Settings, cell: float) -> list[float]:
    """Pontos (x do root) de uma plataforma: as bordas e pontos espaçados no meio."""
    n_cols = plat.i1 - plat.i0 + 1
    if n_cols == 1:
        return [plat.x0]
    xs = [plat.x0, plat.x1]
    inner = max(0, min(s.max_nodes_per_platform - 2, n_cols // s.node_spacing))
    for k in range(1, inner + 1):
        c = plat.i0 + round(k * (n_cols - 1) / (inner + 1))
        xs.append(plat.x0 + (c - plat.i0) * cell)
    return sorted(set(xs))


# --------------------------------------------------------------------------------------------------
# Simulação de uma manobra (spec) e classificação
# --------------------------------------------------------------------------------------------------

Event = tuple[float, str, Any]


@dataclass
class Outcome:
    result: SimResult
    time: float  # total (inclui a fase do pulo antes do gancho)
    jumped: bool
    doubled: bool
    hooked: bool
    momentum: bool
    anchors: list[tuple[float, float]]
    touched: list[str]  # zonas (cp1, cp2, fin) na ordem em que o root entrou nelas
    dj_times: list[float]  # pulos duplos, em t relativo à fase principal
    trajectory: list[tuple[float, float]]


class _Ctx:
    """O que uma simulação precisa (no processo principal ou num trabalhador)."""

    def __init__(self, geo: Geometry):
        self.geo = geo
        self.world = geo.world
        self.p = geo.params
        self.kill_y = geo.tiles.origin[1] - 40.0


def _events(raw: Iterable[Event]) -> list[InputEvent]:
    return [InputEvent(float(t), kind, value) for t, kind, value in raw]


def _touched(ctx: _Ctx, pts: list[tuple[float, float, float]]) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    if not ctx.geo.zones or not pts:
        return out
    xs = [q[1] for q in pts]
    ys = [q[2] for q in pts]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    for z in ctx.geo.zones:
        if hi_x < z.x0 or lo_x > z.x1 or hi_y < z.y0 or lo_y > z.y1:
            continue
        for t, x, y in pts:
            if z.contains(x, y):
                out.append((t, z.zid))
                break
    return out


def start_state(ctx: _Ctx, start: tuple) -> State | None:
    kind = start[0]
    p = ctx.p
    if kind in ("stand", "apex"):
        x, floor_y = float(start[1]), float(start[2])
        st = State.standing(x, floor_y, p)
        x0, y0, x1, y1 = st.box(p)
        if ctx.world.box_overlaps(x0, y0 + 1e-3, x1, y1):
            return None
        if not ctx.world.box_overlaps(x0 + 1e-6, y0 - 0.05, x1 - 1e-6, y0):
            return None  # sem chão embaixo
        return st
    if kind == "state":
        return start[1]
    raise ValueError(f"início desconhecido: {kind}")


def run_spec(ctx: _Ctx, spec: dict[str, Any], record_every: int = 1) -> Outcome | None:
    """Simula uma manobra descrita por `spec` (dados puros, reproduzível).

    spec = {"start": ("stand", x, chão) | ("apex", x, chão, d, t_fogo) | ("state", State),
            "events": [(t, tipo, valor)], "dj_apex": bool (pulo duplo no topo depois de soltar),
            "max_time": s, "hooked_start": bool}
    Em "apex", a fase 1 é pular (com A/D = d) por t_fogo segundos; os eventos valem a partir daí.
    """
    p = ctx.p
    st = start_state(ctx, spec["start"])
    if st is None:
        return None
    pre_time = 0.0
    pre_traj: list[tuple[float, float, float]] = []
    jumped = False
    if spec["start"][0] == "apex":
        d, t_fire = float(spec["start"][3]), float(spec["start"][4])
        ev = [InputEvent(0.0, "move", d), InputEvent(0.0, "jump")] if d else [InputEvent(0.0, "jump")]
        r1 = simulate(st, ev, ctx.world, t_fire, params=p, kill_y=ctx.kill_y, record_every=record_every)
        if r1.dead or r1.frozen:
            return None
        jumped = bool(r1.event_times("jump"))
        pre_time = r1.time
        pre_traj = [(s.t, s.x, s.y) for s in r1.trajectory]
        st = r1.final
    anchors: list[tuple[float, float]] = []
    release_speeds: list[float] = []
    dj_apex = bool(spec.get("dj_apex"))
    memo = {"attached": st.hook_attached, "released_at": None, "dj": False}

    def controller(s: State, t: float):
        attached = s.hook_attached
        if attached and not memo["attached"] and s.hook.anchor is not None:
            anchors.append(s.hook.anchor)
        if memo["attached"] and not attached:
            release_speeds.append(math.hypot(s.vx, s.vy))
            memo["released_at"] = t
        memo["attached"] = attached
        if dj_apex and not memo["dj"] and memo["released_at"] is not None and not attached:
            if s.vy <= 0 and not s.grounded:
                memo["dj"] = True
                return [InputEvent(t, "jump")]
        return None

    res = simulate(
        st,
        _events(spec["events"]),
        ctx.world,
        float(spec["max_time"]),
        params=p,
        controller=controller,
        stop_on_land=True,
        kill_y=ctx.kill_y,
        record_every=record_every,
    )
    if res.final.hook_attached and res.final.hook.anchor is not None:
        if not anchors or anchors[-1] != res.final.hook.anchor:
            anchors.append(res.final.hook.anchor)
    # O controlador vê a soltura um quadro depois; a velocidade do embalo é a do quadro seguinte.
    pts = pre_traj + [(pre_time + s.t, s.x, s.y) for s in res.trajectory]
    touched = [z for _, z in sorted(_touched(ctx, pts))]
    jumped = jumped or bool(res.event_times("jump"))
    doubled = bool(res.event_times("double_jump"))
    hooked = bool(spec.get("hooked_start")) or bool(res.event_times("hook_attach"))
    momentum = any(v > p.walk_speed * MOMENTUM_FACTOR for v in release_speeds)
    return Outcome(
        result=res,
        time=pre_time + res.time,
        jumped=jumped,
        doubled=doubled,
        hooked=hooked,
        momentum=momentum and not res.final.hook_attached,
        anchors=anchors,
        touched=touched,
        dj_times=res.event_times("double_jump"),
        trajectory=[(x, y) for _, x, y in pts],
    )


def kind_label(o: Outcome) -> str:
    """Rótulo da manobra: walk, jump, double, hook, jump+hook, hook+momentum, hook+double."""
    if not o.hooked:
        if o.doubled:
            return "double"
        return "jump" if o.jumped else "walk"
    if o.doubled:
        return "hook+double"
    if o.momentum:
        return "hook+momentum"
    if o.jumped:
        return "jump+hook"
    return "hook"


def is_hang(ctx: _Ctx, o: Outcome) -> bool:
    s = o.result.final
    return s.hook_attached and not s.grounded and math.hypot(s.vx, s.vy) < 4.0 and not o.result.dead


def hang_key(anchor: tuple[float, float]) -> tuple[int, int]:
    """Pontos pendurados a menos de ~6 studs um do outro contam como o mesmo nó."""
    return (round(anchor[0] / 6.0), round(anchor[1] / 6.0))


# --------------------------------------------------------------------------------------------------
# Alvos do gancho
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    angle: float  # graus
    direction: tuple[float, float]
    point: tuple[float, float]
    distance: float
    aim_window: float  # graus de raios vizinhos que também prendem


def visible_targets(
    ctx: _Ctx,
    x: float,
    y: float,
    limits: dict[str, float],
    sectors: int,
    lo_deg: float = -30.0,
    hi_deg: float = 210.0,
    step_deg: float = 5.0,
) -> list[Target]:
    """Leque de raios do root: pontos prendíveis no alcance E na tela; o mais longe de cada setor."""
    p = ctx.p
    rays = []
    n = int(round((hi_deg - lo_deg) / step_deg)) + 1
    for k in range(n):
        a = lo_deg + k * step_deg
        rad = math.radians(a)
        d = (math.cos(rad), math.sin(rad))
        hit = ctx.world.raycast_hook((x, y), d, p.hook_range)
        ok = None
        if hit is not None and hit[1] in ("hook", "once"):
            px, py = hit[0]
            dx, dy = px - x, py - y
            if -limits["down"] <= dy <= limits["up"] and abs(dx) <= limits["side"]:
                ok = (a, d, (px, py), math.hypot(dx, dy))
        rays.append(ok)
    # janela de mira: raios seguidos que prendem
    windows = [0.0] * n
    k = 0
    while k < n:
        if rays[k] is None:
            k += 1
            continue
        e = k
        while e + 1 < n and rays[e + 1] is not None:
            e += 1
        for q in range(k, e + 1):
            windows[q] = (e - k + 1) * step_deg
        k = e + 1
    width = (hi_deg - lo_deg) / sectors
    best: dict[int, tuple[float, int]] = {}
    for k, ray in enumerate(rays):
        if ray is None:
            continue
        sec = min(sectors - 1, int((ray[0] - lo_deg) / width))
        if sec not in best or ray[3] > best[sec][0]:
            best[sec] = (ray[3], k)
    out = []
    for sec in sorted(best):
        k = best[sec][1]
        a, d, pt, dist = rays[k]  # type: ignore[misc]
        out.append(Target(a, d, pt, dist, windows[k]))
    return out


def ledge_targets(ctx: _Ctx, x: float, y: float, limits: dict[str, float], per_side: int = 1) -> list[Target]:
    """Quinas de cima (bordas de laje/parede) no alcance e na tela, vistas do root: o ponto clássico para
    puxar por cima de uma borda, que o leque de raios quase nunca acerta. Por lado (esquerda, direita,
    em cima), as mais altas."""
    p = ctx.p
    w = ctx.world
    t = ctx.geo.tiles
    c = float(t.cell)
    reach = p.hook_range
    i_lo, j_lo = t.cell_at(x - reach, y - limits["down"])
    i_hi, j_hi = t.cell_at(x + reach, y + limits["up"])
    sides: dict[int, list[tuple[float, float, Target]]] = defaultdict(list)
    for i in range(i_lo, i_hi + 1):
        for j in range(j_lo, j_hi + 1):
            if w.surface_cell(i, j) not in ("hook", "once") or w.solid_cell(i, j + 1):
                continue
            open_l, open_r = not w.solid_cell(i - 1, j), not w.solid_cell(i + 1, j)
            if not (open_l or open_r):
                continue
            cx0, cy0 = t.cell_min(i, j)
            tx = cx0 + (0.5 if open_l and not open_r else c - 0.5 if open_r and not open_l else c / 2)
            ty = cy0 + c - 0.5
            dx, dy = tx - x, ty - y
            dist = math.hypot(dx, dy)
            if dist > reach - 0.5 or dist < 3 or not (-limits["down"] <= dy <= limits["up"]):
                continue
            hit = w.raycast_hook((x, y), (dx, dy), reach)
            if hit is None or hit[1] not in ("hook", "once"):
                continue
            if math.hypot(hit[0][0] - tx, hit[0][1] - ty) > 1.5:
                continue
            side = 0 if abs(dx) < 4 else (1 if dx > 0 else -1)
            sides[side].append((ty, -dist, Target(math.degrees(math.atan2(dy, dx)), (dx / dist, dy / dist), hit[0], dist, 0.0)))
    out = []
    for side in sorted(sides):
        for _, _, tg in sorted(sides[side], key=lambda q: (q[0], q[1]), reverse=True)[:per_side]:
            out.append(tg)
    return out


def merged_targets(fan: list[Target], extra: list[Target]) -> list[Target]:
    out = list(fan)
    for tg in extra:
        if all(math.hypot(tg.point[0] - o.point[0], tg.point[1] - o.point[1]) > 3 for o in out):
            out.append(tg)
    return out


# --------------------------------------------------------------------------------------------------
# Famílias de manobras a partir de um nó
# --------------------------------------------------------------------------------------------------


@dataclass
class NodeTask:
    nid: int
    kind: str  # "stand" | "hang"
    x: float
    floor_y: float  # stand: chão; hang: y do root
    x_min: float  # stand: limites da plataforma (root)
    x_max: float
    is_left_edge: bool
    is_right_edge: bool
    state: State | None = None  # hang


@dataclass
class Candidate:
    src: int
    dst: tuple  # ("p", pid, x_pouso) | ("h", chave, State, âncora)
    time: float
    window: float
    label: str
    jumped: bool
    doubled: bool
    hooked: bool
    momentum: bool
    touched: tuple[str, ...]
    anchors: tuple[tuple[float, float], ...]
    spec: dict[str, Any]
    aim_window: float | None = None


def _families_stand(ctx: _Ctx, task: NodeTask, s: Settings, limits: dict[str, float]):
    """Gera (nome da família, [(spec, peso)]) para um nó em pé. Peso = largura (s) da variação."""
    p = ctx.p
    x, fy = task.x, task.floor_y
    cell = float(ctx.geo.tiles.cell)
    fams: list[tuple[str, list[tuple[dict, float]], float | None]] = []

    def spec(start, events, max_time=3.0, dj_apex=False):
        return {"start": start, "events": events, "max_time": max_time, "dj_apex": dj_apex}

    # andar e cair (só nas bordas, para fora)
    for d, edge in ((-1, task.is_left_edge), (1, task.is_right_edge)):
        if not edge:
            continue
        fams.append(("walk", [(spec(("stand", x, fy), [(0, "move", d)], 4.0), WINDOW_CAP)], None))
        if s.walk_variants:
            for t_s in (0.1, 0.3):
                ev = [(0, "move", d), (t_s, "move", 0)]
                fams.append(("walk-stop", [(spec(("stand", x, fy), ev, 4.0), WINDOW_CAP)], None))
            for t_s in (0.15, 0.35):
                ev = [(0, "move", d), (t_s, "move", -d)]
                fams.append(("walk-back", [(spec(("stand", x, fy), ev, 4.0), 0.3)], None))
    # pulo: onde pular (em volta do ponto), parado e para os lados
    offs = sorted(s.jump_offsets)
    for d in (-1, 0, 1):
        variants = []
        for k, off in enumerate(offs):
            # peso = pedaço do chão que esta variação representa (metade da distância até as vizinhas)
            left = (off - offs[k - 1]) / 2 if k > 0 else (offs[1] - off) / 2 if len(offs) > 1 else 0.5
            right = (offs[k + 1] - off) / 2 if k + 1 < len(offs) else left
            weight = (left + right) * cell / p.walk_speed
            x2 = x + off * cell
            if x2 < task.x_min - 1e-6 or x2 > task.x_max + 1e-6:
                variants.append((None, weight))
                continue
            ev = ([(0, "move", d)] if d else []) + [(0, "jump", None)]
            variants.append((spec(("stand", x2, fy), ev), weight))
        fams.append((f"jump{d:+d}", variants, None))
    # pulo e soltar A/D no ar (para cair em plataforma pequena)
    for d in (-1, 1):
        variants = []
        prev = 0.0
        for t_s in s.jump_stop_times:
            ev = [(0, "move", d), (0, "jump", None), (t_s, "move", 0)]
            variants.append((spec(("stand", x, fy), ev), t_s - prev))
            prev = t_s
        fams.append((f"jumpstop{d:+d}", variants, None))
    # pulo duplo em vários momentos
    for d in (-1, 0, 1):
        variants = []
        prev = 0.0
        for t2 in s.dj_times:
            ev = ([(0, "move", d)] if d else []) + [(0, "jump", None), (t2, "jump", None)]
            variants.append((spec(("stand", x, fy), ev, 3.5), t2 - prev if prev else 0.15))
            prev = t2
        fams.append((f"double{d:+d}", variants, None))
    # gancho em cada alvo visível
    y_root = fy + p.feet_offset
    targets = merged_targets(visible_targets(ctx, x, y_root, limits, s.hook_sectors), ledge_targets(ctx, x, y_root, limits))
    for tg in targets:
        dirs = (-1, 1) if abs(tg.point[0] - x) < 6 else (1 if tg.point[0] > x else -1,)
        aim = ("dir", tg.direction[0], tg.direction[1])
        for d in dirs:
            base = [(0, "move", d), (0, "hook", aim)]
            fams.append(
                (f"hookhold{d:+d}", [(spec(("stand", x, fy), base, 3.0) | {"hooked_start": False}, WINDOW_CAP)], tg.aim_window)
            )
            for dj in (False, True):
                variants = []
                prev = 0.0
                for t_r in s.release_times:
                    ev = base + [(t_r, "unhook", None)]
                    variants.append((spec(("stand", x, fy), ev, t_r + 3.0, dj), t_r - prev if prev else 0.15))
                    prev = t_r
                fams.append((f"hook{d:+d}{'dj' if dj else ''}", variants, tg.aim_window))
    return fams


def _families_apex(ctx: _Ctx, task: NodeTask, s: Settings, limits: dict[str, float]):
    """Gancho a partir do topo de um pulo (parado e para os lados)."""
    p = ctx.p
    x, fy = task.x, task.floor_y
    fams = []
    t_fire = round(p.jump_power / p.gravity / FRAME) * FRAME
    st = start_state(ctx, ("stand", x, fy))
    if st is None:
        return fams
    for d in (-1, 0, 1):
        ev = [InputEvent(0.0, "move", float(d)), InputEvent(0.0, "jump")] if d else [InputEvent(0.0, "jump")]
        r1 = simulate(st, ev, ctx.world, t_fire, params=p, kill_y=ctx.kill_y)
        if r1.dead or r1.frozen or r1.final.grounded:
            continue
        ax, ay = r1.final.x, r1.final.y
        targets = visible_targets(ctx, ax, ay, limits, max(3, s.apex_targets + 1), lo_deg=0.0, hi_deg=180.0)
        targets = sorted(targets, key=lambda t: -t.distance)[: s.apex_targets]
        targets = merged_targets(targets, ledge_targets(ctx, ax, ay, limits))
        for tg in targets:
            aim = ("dir", tg.direction[0], tg.direction[1])
            dm = d if d else (1 if tg.point[0] > ax else -1)
            start = ("apex", x, fy, d, t_fire)
            base = [(0, "move", dm), (0, "hook", aim)]
            fams.append((f"apexhold{d:+d}", [({"start": start, "events": base, "max_time": 3.0}, WINDOW_CAP)], tg.aim_window))
            for dj in (False, True):
                variants = []
                prev = 0.0
                for t_r in s.apex_release:
                    ev = base + [(t_r, "unhook", None)]
                    variants.append(
                        ({"start": start, "events": ev, "max_time": t_r + 3.0, "dj_apex": dj}, t_r - prev if prev else 0.2)
                    )
                    prev = t_r
                fams.append((f"apex{d:+d}{'dj' if dj else ''}", variants, tg.aim_window))
    return fams


def _families_hang(ctx: _Ctx, task: NodeTask, s: Settings, limits: dict[str, float]):
    """Pendurado: soltar e cair (com/sem pulo duplo), balançar e soltar, prender no próximo alvo."""
    st = task.state
    assert st is not None
    fams = []
    start = ("state", st)

    def spec(events, max_time=3.0, dj_apex=False):
        return {"start": start, "events": events, "max_time": max_time, "dj_apex": dj_apex, "hooked_start": True}

    for d in (-1, 0, 1):
        fams.append(("drop", [(spec([(0, "move", d), (0, "unhook", None)]), WINDOW_CAP)], None))
        variants = []
        prev = 0.0
        for t2 in (0.15, 0.35, 0.6):
            variants.append((spec([(0, "move", d), (0, "unhook", None), (t2, "jump", None)]), t2 - prev if prev else 0.15))
            prev = t2
        fams.append(("dropdouble", variants, None))
    for d in (-1, 1):
        for dj in (False, True):
            variants = []
            prev = 0.0
            for t_r in (0.4, 0.8):
                variants.append((spec([(0, "move", d), (t_r, "unhook", None)], t_r + 3.0, dj), t_r - prev if prev else 0.3))
                prev = t_r
            fams.append(("swing", variants, None))
    targets = visible_targets(ctx, st.x, st.y, limits, max(3, s.hang_targets), lo_deg=-30.0, hi_deg=210.0)
    targets = sorted(targets, key=lambda t: -t.distance)[: s.hang_targets]
    targets = merged_targets(targets, ledge_targets(ctx, st.x, st.y, limits))
    for tg in targets:
        if math.hypot(tg.point[0] - (st.hook.anchor or (0, 0))[0], tg.point[1] - (st.hook.anchor or (0, 0))[1]) < 3:
            continue  # o mesmo ponto
        aim = ("dir", tg.direction[0], tg.direction[1])
        d = 1 if tg.point[0] > st.x else -1
        base = [(0, "move", d), (0, "unhook", None), (0, "hook", aim)]
        fams.append(("hanghold", [(spec(base, 3.0), WINDOW_CAP)], tg.aim_window))
        for dj in (False, True):
            variants = []
            prev = 0.0
            for t_r in s.hang_release:
                variants.append((spec(base + [(t_r, "unhook", None)], t_r + 3.0, dj), t_r - prev if prev else 0.2))
                prev = t_r
            fams.append((f"hang{'dj' if dj else ''}", variants, tg.aim_window))
    return fams


def _outcome_key(ctx: _Ctx, o: Outcome | None, src_pid: int | None) -> tuple | None:
    """Destino de uma simulação: ("p", pid, x) pousou; ("h", chave, State, âncora) pendurou; None."""
    if o is None:
        return None
    r = o.result
    if r.dead or r.frozen:
        return None
    if r.final.grounded and r.stop_reason == "landed":
        pid = ctx.geo.platform_of(r.final.x, r.final.y - ctx.p.feet_offset)
        if pid is None:
            return None
        return ("p", pid, r.final.x)
    if is_hang(ctx, o):
        anchor = r.final.hook.anchor
        assert anchor is not None
        return ("h", hang_key(anchor), r.final, anchor)
    return None


def expand_node(ctx: _Ctx, task: NodeTask, s: Settings, limits: dict[str, float], src_pid: int | None):
    """Simula as famílias de um nó e devolve (candidatos, estatísticas)."""
    if task.kind == "stand":
        fams = _families_stand(ctx, task, s, limits) + _families_apex(ctx, task, s, limits)
    else:
        fams = _families_hang(ctx, task, s, limits)
    out: list[Candidate] = []
    stats = {"sims": 0, "dead": 0, "frozen": 0, "landed": 0}
    for _name, variants, aim_window in fams:
        results = []
        for sp, weight in variants:
            if sp is None:
                results.append((None, None, weight, None))
                continue
            o = run_spec(ctx, sp, record_every=3)
            stats["sims"] += 1
            if o is not None:
                if o.result.dead:
                    stats["dead"] += 1
                elif o.result.frozen:
                    stats["frozen"] += 1
            key = _outcome_key(ctx, o, src_pid)
            if key is not None and key[0] == "p" and key[1] == src_pid and not o.touched:
                key = None  # voltou para a mesma plataforma
            if key is not None and key[0] == "h" and task.kind == "hang" and task.state is not None:
                if task.state.hook.anchor is not None and hang_key(task.state.hook.anchor) == key[1]:
                    key = None
            results.append((sp, o, weight, key))
        # janela: variações vizinhas (seguidas) com o mesmo destino
        dest = [None if k is None else (k[0], k[1], tuple(o.touched)) for _, o, _, k in results]
        for idx, (sp, o, weight, key) in enumerate(results):
            if key is None or o is None:
                continue
            stats["landed"] += 1
            lo = idx
            while lo - 1 >= 0 and dest[lo - 1] == dest[idx]:
                lo -= 1
            hi = idx
            while hi + 1 < len(results) and dest[hi + 1] == dest[idx]:
                hi += 1
            window = min(WINDOW_CAP, sum(results[q][2] for q in range(lo, hi + 1)))
            out.append(
                Candidate(
                    src=task.nid,
                    dst=key,
                    time=o.time,
                    window=window,
                    label=kind_label(o),
                    jumped=o.jumped,
                    doubled=o.doubled,
                    hooked=o.hooked,
                    momentum=o.momentum,
                    touched=tuple(o.touched),
                    anchors=tuple(o.anchors),
                    spec=sp,
                    aim_window=aim_window,
                )
            )
    return out, stats


# --------------------------------------------------------------------------------------------------
# Trabalhadores (multiprocessing)
# --------------------------------------------------------------------------------------------------

_WORKER: dict[str, Any] = {}


def _init_worker(tm_dict: dict, settings: Settings, limits: dict[str, float]) -> None:
    tm = TileMap.from_dict(tm_dict)
    geo = build_geometry(tm)
    _WORKER["ctx"] = _Ctx(geo)
    _WORKER["settings"] = settings
    _WORKER["limits"] = limits


def _work(args: tuple[NodeTask, int | None]):
    task, src_pid = args
    return expand_node(_WORKER["ctx"], task, _WORKER["settings"], _WORKER["limits"], src_pid)


# --------------------------------------------------------------------------------------------------
# Grafo
# --------------------------------------------------------------------------------------------------


@dataclass
class Node:
    nid: int
    kind: str  # stand | hang
    x: float
    y: float  # root
    pid: int | None = None
    hkey: tuple[int, int] | None = None
    state: State | None = None
    anchor: tuple[float, float] | None = None
    expanded: bool = False


@dataclass
class Edge:
    src: int
    dst: int
    time: float
    window: float
    label: str  # walk, jump, double, hook, jump+hook, hook+momentum, hook+double, plat (andar na plataforma)
    jumped: bool = False
    doubled: bool = False
    hooked: bool = False
    momentum: bool = False
    touched: tuple[str, ...] = ()
    anchors: tuple[tuple[float, float], ...] = ()
    spec: dict[str, Any] | None = None
    x_land: float | None = None
    aim_window: float | None = None
    refined: dict[str, Any] | None = None

    @property
    def maneuver(self) -> bool:
        return self.label != "plat"

    @property
    def w_eff(self) -> float:
        """Janela usada nos custos: a refinada (se houver), senão a da família."""
        if self.refined and "window" in self.refined:
            return self.refined["window"]
        return self.window


@dataclass
class Graph:
    geo: Geometry
    nodes: list[Node]
    edges: list[Edge]
    out: dict[int, list[int]]  # nó -> índices de arestas
    plat_nodes: dict[int, list[int]]
    reached: set[int]  # plataformas alcançadas
    stats: dict[str, Any]

    def node_stage(self, nid: int) -> str:
        n = self.nodes[nid]
        return self.geo.stage_of(n.x, n.y)


def build_graph(
    geo: Geometry,
    settings: Settings,
    limits: dict[str, float],
    jobs: int = 1,
    progress: Callable[[str], None] | None = None,
) -> Graph:
    p = geo.params
    nodes: list[Node] = []
    plat_nodes: dict[int, list[int]] = {}
    hang_index: dict[tuple[int, int], int] = {}
    hang_bucket: dict[tuple[int, int], int] = defaultdict(int)
    edges: list[Edge] = []
    reached: set[int] = set()
    queue: list[int] = []
    stats: dict[str, Any] = {"sims": 0, "dead": 0, "frozen": 0, "landed": 0, "hang_capped": 0}

    def plat_node_ids(pid: int) -> list[int]:
        if pid not in plat_nodes:
            plat = geo.platforms[pid]
            ids = []
            for x in node_positions(plat, settings, float(geo.tiles.cell)):
                nid = len(nodes)
                nodes.append(Node(nid, "stand", x, plat.floor_y + p.feet_offset, pid=pid))
                ids.append(nid)
            plat_nodes[pid] = ids
            for a, b in zip(ids, ids[1:]):
                dt = abs(nodes[b].x - nodes[a].x) / p.walk_speed
                for u, v in ((a, b), (b, a)):
                    edges.append(Edge(u, v, dt, INF, "plat"))
        return plat_nodes[pid]

    def reach_platform(pid: int) -> None:
        if pid in reached:
            return
        reached.add(pid)
        queue.extend(plat_node_ids(pid))

    if geo.spawn_pid is None:
        raise ValueError("o mapa não tem spawn em pé (campo `spawn` do tiles.json)")
    reach_platform(geo.spawn_pid)

    def task_of(nid: int) -> tuple[NodeTask, int | None]:
        n = nodes[nid]
        if n.kind == "stand":
            assert n.pid is not None
            plat = geo.platforms[n.pid]
            return (
                NodeTask(nid, "stand", n.x, plat.floor_y, plat.x0, plat.x1, n.x <= plat.x0 + 1e-6, n.x >= plat.x1 - 1e-6),
                n.pid,
            )
        return (NodeTask(nid, "hang", n.x, n.y, n.x, n.x, False, False, n.state), None)

    best: dict[tuple[int, int, str], tuple[int, int]] = {}  # (src, dst, label) -> (aresta mais rápida, mais larga)

    def add_candidate(c: Candidate) -> None:
        if c.dst[0] == "p":
            pid, x_land = c.dst[1], c.dst[2]
            ids = plat_node_ids(pid)
            dst = min(ids, key=lambda q: abs(nodes[q].x - x_land))
            extra = abs(nodes[dst].x - x_land) / p.walk_speed
            reach_platform(pid)
        else:
            key, st, anchor = c.dst[1], c.dst[2], c.dst[3]
            if key not in hang_index:
                bucket = (int(anchor[0] // 40), int(anchor[1] // 40))
                if hang_bucket[bucket] >= settings.hang_per_bucket:
                    stats["hang_capped"] += 1
                    return
                hang_bucket[bucket] += 1
                nid = len(nodes)
                nodes.append(Node(nid, "hang", st.x, st.y, hkey=key, state=st, anchor=anchor))
                hang_index[key] = nid
                queue.append(nid)
            dst = hang_index[key]
            extra = 0.0
            x_land = None
        if dst == c.src:
            return
        e = Edge(
            c.src,
            dst,
            c.time + extra,
            c.window,
            c.label,
            c.jumped,
            c.doubled,
            c.hooked,
            c.momentum,
            c.touched,
            c.anchors,
            c.spec,
            x_land,
            c.aim_window,
        )
        k = (c.src, dst, c.label + "|" + ",".join(c.touched))
        if k not in best:
            edges.append(e)
            best[k] = (len(edges) - 1, len(edges) - 1)
            return
        fi, wi = best[k]
        if e.time < edges[fi].time - 1e-9:
            if fi == wi:
                edges.append(e)
                fi = len(edges) - 1
            else:
                edges[fi] = e
        if e.window > edges[wi].window + 1e-9:
            if fi == wi:
                edges.append(e)
                wi = len(edges) - 1
            else:
                edges[wi] = e
        best[k] = (fi, wi)

    ctx = _Ctx(geo)
    pool = None
    if jobs > 1:
        import multiprocessing as mp

        pool = mp.get_context("spawn").Pool(jobs, initializer=_init_worker, initargs=(geo.tiles.to_dict(), settings, limits))
    t0 = time.time()
    rounds = 0
    try:
        while queue:
            rounds += 1
            batch = [nid for nid in queue if not nodes[nid].expanded]
            queue.clear()
            for nid in batch:
                nodes[nid].expanded = True
            tasks = [task_of(nid) for nid in batch]
            if pool is not None:
                results = pool.imap_unordered(_work, tasks, chunksize=1)
            else:
                results = (expand_node(ctx, t, settings, limits, pid) for t, pid in tasks)
            for cands, st in results:
                for k in ("sims", "dead", "frozen", "landed"):
                    stats[k] += st[k]
                for c in cands:
                    add_candidate(c)
            if progress:
                progress(
                    f"  rodada {rounds}: {len(batch)} nós expandidos, {len(reached)} plataformas, "
                    f"{len(hang_index)} pendurados, {stats['sims']} simulações, {time.time() - t0:.0f} s"
                )
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    out: dict[int, list[int]] = defaultdict(list)
    for idx, e in enumerate(edges):
        out[e.src].append(idx)
    stats["rounds"] = rounds
    stats["nodes"] = len(nodes)
    stats["hang_nodes"] = len(hang_index)
    stats["edges"] = sum(1 for e in edges if e.maneuver)
    stats["build_seconds"] = time.time() - t0
    return Graph(geo, nodes, edges, dict(out), plat_nodes, reached, stats)


# --------------------------------------------------------------------------------------------------
# Rotas (Dijkstra em camadas: nó x quantos checkpoints já foram)
# --------------------------------------------------------------------------------------------------


def p_success(window: float, sigma: float = SIGMA_MEDIUM) -> float:
    if window == INF or window >= WINDOW_CAP:
        return 1.0
    return max(1e-4, math.erf(window / 2 / (sigma * math.sqrt(2))))


def cost_fastest(e: Edge) -> float:
    return e.time


def cost_medium(e: Edge) -> float:
    """Tempo esperado do jogador médio: pensa antes, erra com chance 1 - p e perde RETRY por erro."""
    if not e.maneuver:
        return e.time
    ps = p_success(e.w_eff)
    return (e.time + REACTION) / ps + (1 / ps - 1) * RETRY


def cost_safest(e: Edge) -> float:
    """Maximiza a chance de fazer sem errar (soma de -ln p), com o tempo só de desempate."""
    if not e.maneuver:
        return e.time * 0.01
    return -math.log(p_success(e.w_eff)) * 10 + e.time * 0.01


EdgeFilter = Callable[[Edge], bool]

FILTERS: dict[str, EdgeFilter] = {
    "tudo": lambda e: True,
    "só gancho (sem pulo nenhum)": lambda e: not e.maneuver or (not e.jumped and not e.doubled),
    "sem gancho": lambda e: not e.maneuver or not e.hooked,
    "sem pulo duplo": lambda e: not e.maneuver or not e.doubled,
    "sem embalo": lambda e: not e.maneuver or not e.momentum,
}


@dataclass
class Route:
    steps: list[tuple[int, int, int | None]]  # (nó, estágio, aresta usada para chegar; None = transição)
    cost: float

    def edge_ids(self) -> list[int]:
        return [e for _, _, e in self.steps if e is not None]


def _advance(stage: int, touched: Iterable[str], order: list[str]) -> int:
    for z in touched:
        if stage < len(order) and z == order[stage]:
            stage += 1
    return stage


def layered_route(
    g: Graph,
    cost: Callable[[Edge], float],
    allow: EdgeFilter = FILTERS["tudo"],
    sources: Iterable[tuple[int, int]] | None = None,
    goal_stage: int | None = None,
) -> Route | None:
    """Menor custo de (nó, estágio) até o estágio final (todas as zonas na ordem)."""
    order = [z.zid for z in g.geo.zones]
    seen_ids: list[str] = []
    for z in order:
        if z not in seen_ids:
            seen_ids.append(z)
    order = seen_ids
    goal = len(order) if goal_stage is None else goal_stage
    if sources is None:
        spawn_pid = -1 if g.geo.spawn_pid is None else g.geo.spawn_pid
        sources = [(nid, 0) for nid in g.plat_nodes.get(spawn_pid, [])]
        if g.geo.spawn_pid is not None:
            spawn_x = g.geo.spawn[0]
            sources = sorted(sources, key=lambda s: abs(g.nodes[s[0]].x - spawn_x))[:1]
    p = g.geo.params
    dist: dict[tuple[int, int], float] = {}
    prev: dict[tuple[int, int], tuple[tuple[int, int], int | None]] = {}
    heap: list[tuple[float, int, int]] = []
    for nid, st in sources:
        dist[(nid, st)] = 0.0
        heapq.heappush(heap, (0.0, nid, st))
    end = None
    while heap:
        d, nid, st = heapq.heappop(heap)
        if d > dist.get((nid, st), INF) + 1e-12:
            continue
        if st >= goal:
            end = (nid, st)
            break
        # transição parada: a plataforma (ou o ponto pendurado) está na zona seguinte
        n = g.nodes[nid]
        if st < len(order):
            zid = order[st]
            extra = None
            if n.kind == "stand" and n.pid is not None:
                zx = g.geo.platforms[n.pid].zone_x.get(zid)
                if zx is not None:
                    extra = 2 * abs(zx - n.x) / p.walk_speed
            elif n.kind == "hang":
                for z in g.geo.zones:
                    if z.zid == zid and z.contains(n.x, n.y):
                        extra = 0.0
            if extra is not None:
                key = (nid, st + 1)
                nd = d + extra
                if nd < dist.get(key, INF) - 1e-12:
                    dist[key] = nd
                    prev[key] = ((nid, st), None)
                    heapq.heappush(heap, (nd, nid, st + 1))
        for ei in g.out.get(nid, ()):
            e = g.edges[ei]
            if not allow(e):
                continue
            ns = _advance(st, e.touched, order)
            key = (e.dst, ns)
            nd = d + cost(e)
            if nd < dist.get(key, INF) - 1e-12:
                dist[key] = nd
                prev[key] = ((nid, st), ei)
                heapq.heappush(heap, (nd, e.dst, ns))
    if end is None:
        return None
    steps: list[tuple[int, int, int | None]] = []
    cur = end
    while cur in prev:
        (pn, ps_), ei = prev[cur]
        steps.append((cur[0], cur[1], ei))
        cur = (pn, ps_)
    steps.append((cur[0], cur[1], None))
    steps.reverse()
    return Route(steps, dist[end])


def zone_order(g: Graph) -> list[str]:
    order: list[str] = []
    for z in g.geo.zones:
        if z.zid not in order:
            order.append(z.zid)
    return order


def reachable_nodes(g: Graph, sources: Iterable[int], allow: EdgeFilter = FILTERS["tudo"]) -> set[int]:
    seen = set(sources)
    stack = list(seen)
    while stack:
        nid = stack.pop()
        for ei in g.out.get(nid, ()):
            e = g.edges[ei]
            if allow(e) and e.dst not in seen:
                seen.add(e.dst)
                stack.append(e.dst)
    return seen


# --------------------------------------------------------------------------------------------------
# Refinamento da janela (só nas arestas das rotas)
# --------------------------------------------------------------------------------------------------

_SHIFT_FRAMES = (1, 2, 3, 4, 6, 8, 12, 18)
_SHIFT_STUDS = (1, 2, 3, 4, 6, 8, 12)
_SHIFT_DEG = (1, 2, 4, 6, 10, 15)


def _explicit(spec: dict[str, Any], o: Outcome) -> dict[str, Any]:
    """Troca o pulo duplo automático (controlador) por um evento com o tempo que ele aconteceu."""
    sp = dict(spec)
    events = list(spec["events"])
    if spec.get("dj_apex"):
        for t in o.dj_times:
            events.append((t, "jump", None))
        sp["dj_apex"] = False
    sp["events"] = sorted(events, key=lambda ev: ev[0])
    return sp


REFINE_TOLERANCE = 1.0  # s: a variação "dá certo" se não deixa o resto da corrida mais de 1 s mais longo


def unit_of_key(key: tuple) -> tuple:
    """Plataforma ("p", pid) ou ponto pendurado ("h", chave) de um destino de simulação."""
    return ("p", key[1]) if key[0] == "p" else ("h", key[1])


def unit_of_node(n: "Node") -> tuple:
    return ("p", n.pid) if n.kind == "stand" else ("h", n.hkey)


@dataclass(frozen=True)
class RefineJob:
    edge: int
    spec: dict[str, Any]
    stage: int  # estágio (checkpoints já feitos) antes da manobra
    target: tuple  # unidade de destino
    togo: float  # tempo da rota mais rápida do destino até a chegada
    anchor: tuple[float, float] | None  # destino pendurado: o ponto


def refine_edge(ctx: _Ctx, job: RefineJob, togo_unit: dict[tuple, float], order: list[str]) -> dict[str, Any]:
    """Mexe em cada entrada da manobra (quando pular, quando soltar, onde pular, mira) e mede a janela em
    que ela ainda "dá certo": pousa numa plataforma de onde o resto da corrida não fica mais que
    REFINE_TOLERANCE segundos mais longo (ou no mesmo destino)."""
    base = run_spec(ctx, job.spec)
    if base is None:
        return {"note": "não reproduziu"}

    def ok_outcome(o: Outcome | None) -> bool:
        key = _outcome_key(ctx, o, None)
        if key is None or o is None:
            return False
        unit = unit_of_key(key)
        st = _advance(job.stage, o.touched, order)
        if unit == job.target:
            return True
        if key[0] == "h" and job.anchor is not None:
            if math.hypot(key[3][0] - job.anchor[0], key[3][1] - job.anchor[1]) <= 8:
                return True
        return togo_unit.get((unit, st), INF) <= job.togo + REFINE_TOLERANCE

    if not ok_outcome(base):
        return {"note": "não reproduziu"}
    sp = _explicit(job.spec, base)

    def ok(spec2: dict[str, Any] | None) -> bool:
        return spec2 is not None and ok_outcome(run_spec(ctx, spec2, record_every=3))

    def extent(make: Callable[[float], dict[str, Any] | None], shifts: tuple[float, ...]) -> tuple[float, float]:
        out = []
        for sgn in (-1, 1):
            last = 0.0
            for sh in shifts:
                if not ok(make(sgn * sh)):
                    break
                last = sh
            out.append(last)
        return out[0], out[1]

    dims: dict[str, float] = {}
    labels = {"unhook": "soltar o gancho", "hook": "disparar o gancho"}
    for idx, (t, kind, _value) in enumerate(sp["events"]):
        # o instante 0 (começar a manobra) é medido pelo "lugar do pulo"
        if kind not in ("jump", "unhook", "hook") or t <= 1e-9:
            continue

        def make(shift_frames: float, idx: int = idx) -> dict[str, Any] | None:
            evs = list(sp["events"])
            t0_, k0, v0 = evs[idx]
            nt = t0_ + shift_frames * FRAME
            if nt < 0:
                return None
            evs[idx] = (nt, k0, v0)
            return dict(sp, events=sorted(evs, key=lambda ev: ev[0]))

        lo, hi = extent(make, _SHIFT_FRAMES)
        name = "pulo duplo" if kind == "jump" else labels[kind]  # pulo em t > 0 é no ar
        dims[name] = min(dims.get(name, INF), (lo + hi + 1) * FRAME)
    start = sp["start"]
    if start[0] == "apex":

        def make_apex(shift_frames: float) -> dict[str, Any] | None:
            nt = start[4] + shift_frames * FRAME
            if nt <= FRAME:
                return None
            return dict(sp, start=(start[0], start[1], start[2], start[3], nt))

        lo, hi = extent(make_apex, _SHIFT_FRAMES)
        dims["disparar o gancho"] = min(dims.get("disparar o gancho", INF), (lo + hi + 1) * FRAME)
    has_jump0 = any(k == "jump" and t <= 1e-9 for t, k, _ in sp["events"]) or start[0] == "apex"
    if start[0] in ("stand", "apex") and has_jump0:

        def make_pos(shift: float) -> dict[str, Any] | None:
            return dict(sp, start=(start[0], start[1] + shift, *start[2:]))

        lo, hi = extent(make_pos, _SHIFT_STUDS)
        dims["lugar do pulo"] = (lo + hi + 1) / ctx.p.walk_speed
    aim_deg = None
    for idx, (t, kind, value) in enumerate(sp["events"]):
        if kind != "hook" or value[0] != "dir":
            continue

        def make_aim(deg: float, idx: int = idx) -> dict[str, Any]:
            evs = list(sp["events"])
            t0_, k0, v0 = evs[idx]
            a = math.atan2(v0[2], v0[1]) + math.radians(deg)
            evs[idx] = (t0_, k0, ("dir", math.cos(a), math.sin(a)))
            return dict(sp, events=evs)

        lo, hi = extent(make_aim, _SHIFT_DEG)
        aim_deg = lo + hi + 1
        break
    timing = min(dims.values()) if dims else INF
    return {
        "dims": dims,
        "window": min(timing, WINDOW_CAP),
        "hardest": min(dims, key=lambda k: dims[k]) if dims else None,
        "aim_deg": aim_deg,
    }


_REFINE: dict[str, Any] = {}


def _init_refine(tm_dict: dict, togo_unit: dict[tuple, float], order: list[str]) -> None:
    _REFINE["ctx"] = _Ctx(build_geometry(TileMap.from_dict(tm_dict)))
    _REFINE["togo"] = togo_unit
    _REFINE["order"] = order


def _refine_work(job: RefineJob) -> tuple[int, dict[str, Any]]:
    return job.edge, refine_edge(_REFINE["ctx"], job, _REFINE["togo"], _REFINE["order"])


def togo_tables(g: "Graph") -> tuple[dict[tuple[int, int], float], dict[tuple, float]]:
    """Tempo da rota mais rápida de cada (nó, estágio) até a chegada; e o mesmo por unidade."""
    order = zone_order(g)
    n_st = len(order)
    p = g.geo.params
    rev: dict[tuple[int, int], list[tuple[tuple[int, int], float]]] = defaultdict(list)
    for e in g.edges:
        for st in range(n_st):
            rev[(e.dst, _advance(st, e.touched, order))].append(((e.src, st), e.time))
    for n in g.nodes:
        for st in range(n_st):
            zid = order[st]
            extra = None
            if n.kind == "stand" and n.pid is not None:
                zx = g.geo.platforms[n.pid].zone_x.get(zid)
                if zx is not None:
                    extra = 2 * abs(zx - n.x) / p.walk_speed
            elif any(z.zid == zid and z.contains(n.x, n.y) for z in g.geo.zones):
                extra = 0.0
            if extra is not None:
                rev[(n.nid, st + 1)].append(((n.nid, st), extra))
    dist: dict[tuple[int, int], float] = {}
    heap: list[tuple[float, int, int]] = []
    for n in g.nodes:
        dist[(n.nid, n_st)] = 0.0
        heap.append((0.0, n.nid, n_st))
    heapq.heapify(heap)
    while heap:
        d, nid, st = heapq.heappop(heap)
        if d > dist.get((nid, st), INF):
            continue
        for (pn, ps_), c in rev.get((nid, st), ()):
            nd = d + c
            if nd < dist.get((pn, ps_), INF) - 1e-12:
                dist[(pn, ps_)] = nd
                heapq.heappush(heap, (nd, pn, ps_))
    by_unit: dict[tuple, float] = {}
    for (nid, st), d in dist.items():
        k = (unit_of_node(g.nodes[nid]), st)
        if d < by_unit.get(k, INF):
            by_unit[k] = d
    return dist, by_unit


def refine_routes(
    g: "Graph",
    routes: dict[str, "Route | None"],
    togo: dict[tuple[int, int], float],
    togo_unit: dict[tuple, float],
    jobs: int,
    progress: Callable[[str], None] | None,
    label: str = "",
) -> int:
    """Refina as manobras das rotas que ainda não foram refinadas; devolve quantas."""
    order = zone_order(g)
    todo: dict[int, RefineJob] = {}
    for r in routes.values():
        if r is None:
            continue
        for (_pn, ps_, _), (_nid, st, ei) in zip(r.steps, r.steps[1:]):
            if ei is None or ei in todo:
                continue
            e = g.edges[ei]
            if not e.maneuver or e.refined is not None or e.spec is None:
                continue
            dst = g.nodes[e.dst]
            todo[ei] = RefineJob(ei, e.spec, ps_, unit_of_node(dst), togo.get((e.dst, st), INF), dst.anchor)
    if not todo:
        return 0
    if progress:
        progress(f"  refinando {len(todo)} manobras das rotas{label}")
    jobs_list = list(todo.values())
    if jobs > 1 and len(jobs_list) > 8:
        import multiprocessing as mp

        with mp.get_context("spawn").Pool(
            jobs, initializer=_init_refine, initargs=(g.geo.tiles.to_dict(), togo_unit, order)
        ) as pool:
            for ei, info in pool.imap_unordered(_refine_work, jobs_list, chunksize=2):
                g.edges[ei].refined = info
    else:
        ctx = _Ctx(g.geo)
        for job in jobs_list:
            g.edges[job.edge].refined = refine_edge(ctx, job, togo_unit, order)
    return len(todo)


# --------------------------------------------------------------------------------------------------
# Análises
# --------------------------------------------------------------------------------------------------


def _route_summary(g: Graph, route: Route | None, refined: bool = True) -> dict[str, Any] | None:
    if route is None:
        return None
    order = zone_order(g)
    edges = [g.edges[ei] for ei in route.edge_ids()]
    man = [e for e in edges if e.maneuver]
    total = sum(e.time for e in edges)
    # tempo parado nas transições (andar até a zona)
    p = g.geo.params
    trans = 0.0
    for (nid, st, ei), (nid2, st2, ei2) in zip(route.steps, route.steps[1:]):
        if ei2 is None and nid == nid2:
            n = g.nodes[nid]
            zx = g.geo.platforms[n.pid].zone_x.get(order[st]) if n.pid is not None else None
            if zx is not None:
                trans += 2 * abs(zx - n.x) / p.walk_speed
    total += trans
    by_kind: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "time": 0.0})
    for e in man:
        by_kind[e.label]["count"] += 1
        by_kind[e.label]["time"] += e.time

    def win(e: Edge) -> float:
        return e.w_eff if refined else e.window

    # trechos (entre zonas)
    sections = []
    cur = {"edges": [], "start_node": route.steps[0][0]}
    first_stage = route.steps[0][1]
    for nid, st, ei in route.steps[1:]:
        if ei is not None:
            cur["edges"].append(ei)
        while first_stage + len(sections) < st:
            cur["end_node"] = nid
            cur["zone"] = order[first_stage + len(sections)]
            sections.append(cur)
            cur = {"edges": [], "start_node": nid}
    exp_medium = 0.0
    p_all = 1.0
    errors = 0.0
    for e in man:
        ps = p_success(win(e))
        p_all *= ps
        errors += 1 / ps - 1  # tentativas erradas esperadas
        exp_medium += (e.time + REACTION) / ps + (1 / ps - 1) * RETRY
    exp_medium += sum(e.time for e in edges if not e.maneuver) + trans
    sec_out = []
    for sec in sections:
        es = [g.edges[ei] for ei in sec["edges"]]
        ms = [e for e in es if e.maneuver]
        t = sum(e.time for e in es)
        wins = [win(e) for e in ms]
        pm = 1.0
        em = 0.0
        for e in ms:
            ps = p_success(win(e))
            pm *= ps
            em += (e.time + REACTION) / ps + (1 / ps - 1) * RETRY
        em += sum(e.time for e in es if not e.maneuver)
        kinds: dict[str, int] = defaultdict(int)
        for e in ms:
            kinds[e.label] += 1
        sec_out.append(
            {
                "zone": sec["zone"],
                "start_node": sec["start_node"],
                "end_node": sec["end_node"],
                "edges": sec["edges"],
                "time": t,
                "maneuvers": len(ms),
                "min_window": min(wins) if wins else INF,
                "p_clean": pm,
                "expected_medium": em,
                "kinds": dict(kinds),
                "hard": sum(1 for w in wins if w < 0.15),
            }
        )
    return {
        "time": total,
        "maneuvers": len(man),
        "by_kind": {k: dict(v) for k, v in by_kind.items()},
        "sections": sec_out,
        "p_clean": p_all,
        "expected_errors": errors,
        "expected_medium": exp_medium,
        "edges": route.edge_ids(),
        "nodes": [nid for nid, _, _ in route.steps],
        "min_window": min((win(e) for e in man), default=INF),
    }


def section_sources(g: Graph, route: Route, k: int) -> int | None:
    """Nó onde a rota entra no trecho k (0 = spawn)."""
    for nid, st, _ in route.steps:
        if st == k:
            return nid
    return None


def section_reachable(g: Graph, src: int, k: int, allow: EdgeFilter) -> Route | None:
    return layered_route(g, cost_fastest, allow, sources=[(src, k)], goal_stage=k + 1)


def disjoint_between(g: Graph, src: int, dst: int, max_routes: int = 5) -> list[dict[str, Any]]:
    """Caminhos de src a dst por plataformas (e pontos pendurados) diferentes. Guloso: acha o mais
    rápido, proíbe as unidades do meio dele e procura de novo."""
    banned: set[tuple] = set()
    keep = {unit_of_node(g.nodes[src]), unit_of_node(g.nodes[dst])}
    out: list[dict[str, Any]] = []
    first: list[tuple[float, float]] | None = None
    for _ in range(max_routes):
        found = _node_route(g, src, dst, lambda e: unit_of_node(g.nodes[e.dst]) not in banned, with_path=True)
        if found is None:
            break
        t, path = found
        es = [g.edges[ei] for ei in path]
        ms = [e for e in es if e.maneuver]
        nodes = [src] + [e.dst for e in es]
        pts = [(g.nodes[n].x, g.nodes[n].y) for n in nodes]
        if first is None:
            first = pts
            spread = 0.0
        else:
            spread = sum(min(math.hypot(a[0] - b[0], a[1] - b[1]) for b in first) for a in pts) / max(1, len(pts))
        kinds: dict[str, int] = defaultdict(int)
        for e in ms:
            kinds[e.label] += 1
        out.append(
            {
                "time": t,
                "maneuvers": len(ms),
                "min_window": min((e.w_eff for e in ms), default=INF),
                "p_clean": math.prod(p_success(e.w_eff) for e in ms),
                "kinds": dict(kinds),
                "spread": spread,
                "edges": path,
            }
        )
        inner = {unit_of_node(g.nodes[n]) for n in nodes} - keep
        if not inner:
            break
        banned |= inner
    return out


@dataclass
class AnchorInfo:
    cid: int
    kind: str  # "HookOnce" | "solto" (bloco pequeno solto) | "nível 2"
    cells: list[tuple[int, int]]
    center: tuple[float, float]
    status: str = ""  # usado | alcançável | fora da tela | fora do alcance
    best_distance: float = INF
    used: int = 0
    stage: str = "Mapa"


def anchor_analysis(g: Graph, limits: dict[str, float]) -> list[AnchorInfo]:
    """Pontos de gancho "de propósito": peças HookOnce, blocos pequenos soltos (até 40 células) e peças
    com RequiresHookLevel. Para cada um: usado por alguma aresta? alcançável (no alcance e na tela) de
    algum ponto alcançado (em pé, no topo do pulo ou pendurado)?"""
    geo = g.geo
    tm = geo.tiles
    w = geo.world
    p = geo.params
    solid_cells = {c for c, k in w.cells.items() if w.kind_props[k][0]}
    comps = _components(solid_cells)
    cell_comp: dict[tuple[int, int], int] = {}
    infos: list[AnchorInfo] = []
    for comp in comps:
        once = [c for c in comp if tm.cells.get(c) == "HookOnce"]
        level = [c for c in comp if "RequiresHookLevel" in tm.attributes.get(c, {})]
        hookable = [c for c in comp if w.surface_cell(*c) in ("hook", "once")]
        if not hookable:
            continue
        if once:
            kind, cells = "HookOnce", once
        elif level:
            kind, cells = "nível 2", level
        elif len(comp) <= 40:
            kind, cells = "solto", comp
        else:
            continue
        cx = sum(tm.cell_center(*c)[0] for c in cells) / len(cells)
        cy = sum(tm.cell_center(*c)[1] for c in cells) / len(cells)
        info = AnchorInfo(len(infos), kind, cells, (cx, cy), stage=geo.stage_of(cx, cy))
        for c in comp:
            cell_comp[c] = info.cid
        infos.append(info)
    if not infos:
        return infos
    # usado: âncoras presas em arestas
    for e in g.edges:
        for ax, ay in e.anchors:
            for dx in (-0.05, 0.05):
                for dy in (-0.05, 0.05):
                    cid = cell_comp.get(tm.cell_at(ax + dx, ay + dy))
                    if cid is not None:
                        infos[cid].used += 1
                        break
                else:
                    continue
                break
    # pontos de onde o jogador pode mirar: cada coluna das plataformas alcançadas (em pé, topo do pulo
    # e topo do pulo duplo) e os nós pendurados
    jump_h = p.jump_power**2 / (2 * p.gravity)
    dj_h = jump_h + p.double_jump_velocity**2 / (2 * p.gravity)
    eyes: list[tuple[float, float]] = []
    for pid in g.reached:
        plat = geo.platforms[pid]
        for c in range(plat.i0, plat.i1 + 1):
            x = geo.col_x(c)
            y = plat.floor_y + p.feet_offset
            eyes.append((x, y))
            for h in (jump_h, dj_h):
                if not w.box_overlaps(x - p.half_width, y - p.feet_offset + h, x + p.half_width, y + p.head_offset + h):
                    eyes.append((x, y + h))
    for n in g.nodes:
        if n.kind == "hang":
            eyes.append((n.x, n.y))
    # grade espacial dos olhos
    bucket: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    bs = 40.0
    for ex, ey in eyes:
        bucket[(int(ex // bs), int(ey // bs))].append((ex, ey))
    for info in infos:
        cells = info.cells if len(info.cells) <= 24 else info.cells[:: max(1, len(info.cells) // 24)]
        best_on = INF
        best_any = INF
        bx, by = int(info.center[0] // bs), int(info.center[1] // bs)
        cands = [e for dxb in (-2, -1, 0, 1, 2) for dyb in (-2, -1, 0, 1, 2) for e in bucket.get((bx + dxb, by + dyb), [])]
        for ex, ey in cands:
            for c in cells:
                tx, ty = tm.cell_center(*c)
                dist = math.hypot(tx - ex, ty - ey)
                if dist > p.hook_range + 2 or dist >= best_on:
                    continue
                hit = w.raycast_hook((ex, ey), (tx - ex, ty - ey), p.hook_range)
                if hit is None or hit[1] not in ("hook", "once"):
                    continue
                if cell_comp.get(tm.cell_at(hit[0][0] + (tx - ex) / dist * 0.05, hit[0][1] + (ty - ey) / dist * 0.05)) != info.cid:
                    continue
                d = math.hypot(hit[0][0] - ex, hit[0][1] - ey)
                dy = hit[0][1] - ey
                best_any = min(best_any, d)
                if -limits["down"] <= dy <= limits["up"]:
                    best_on = min(best_on, d)
        info.best_distance = best_on if best_on < INF else best_any
        if info.used:
            info.status = "usado"
        elif best_on < INF:
            info.status = "alcançável, não usado"
        elif best_any < INF:
            info.status = "só fora da tela"
        else:
            info.status = "fora do alcance"
    return infos


def step_analysis(g: Graph, rules: dict[str, float]) -> list[dict[str, Any]]:
    """Degraus: fim de plataforma encostado numa parede cujo topo é outra plataforma."""
    geo = g.geo
    p = geo.params
    out = []
    w = geo.world
    for plat in geo.platforms:
        if not plat.in_region:
            continue
        for d, col in ((-1, plat.i0 - 1), (1, plat.i1 + 1)):
            if not w.solid_cell(col, plat.j):
                continue  # borda aberta (queda), não degrau
            j = plat.j
            while w.solid_cell(col, j) and j < geo.tiles.height:
                j += 1
            pid = geo.plat_at.get((col, j))
            if pid is None:
                continue
            up = geo.platforms[pid]
            h = up.floor_y - plat.floor_y
            if h <= 0 or h > STEP_MAX:
                continue  # acima de STEP_MAX é parede (do mapa, da torre), não degrau
            if h <= rules.get("step_jump_max", 10):
                cls = "pulo"
            elif h <= rules.get("step_double_jump_max", 20):
                cls = "pulo duplo"
            elif h < rules.get("step_needs_hook", 24):
                cls = "no limite do pulo duplo"
            elif h <= rules.get("wall_needs_two_hooks", 38):
                cls = "só gancho"
            else:
                cls = "2+ ganchos"
            edge_kinds = sorted(
                {
                    g.edges[ei].label
                    for nid in g.plat_nodes.get(plat.pid, [])
                    for ei in g.out.get(nid, ())
                    if g.edges[ei].maneuver and g.nodes[g.edges[ei].dst].pid == pid
                }
            )
            out.append(
                {
                    "from": plat.pid,
                    "to": pid,
                    "height": h,
                    "class": cls,
                    "x": geo.col_x(col) - d * 1.0,
                    "y": plat.floor_y,
                    "stage": plat.stage,
                    "reached_from": plat.pid in g.reached,
                    "climbed_with": edge_kinds,
                }
            )
    return out


def drop_analysis(g: Graph, limits: dict[str, float]) -> dict[str, Any]:
    """Quedas às cegas: o destino fica mais baixo que o que a câmera mostra abaixo dos pés."""
    blind = limits["below_feet"]
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    for e in g.edges:
        if not e.maneuver:
            continue
        a, b = g.nodes[e.src], g.nodes[e.dst]
        if b.kind != "stand":
            continue
        drop = (a.y - b.y) if a.kind == "stand" else (a.y - g.geo.params.feet_offset - (b.y - g.geo.params.feet_offset))
        if drop <= blind:
            continue
        key = (-1 if a.pid is None else a.pid, -1 if b.pid is None else b.pid)
        if key not in pairs or drop > pairs[key]["drop"]:
            pairs[key] = {"drop": drop, "x": a.x, "y": a.y - g.geo.params.feet_offset, "to_x": b.x, "to_y": b.y - 3, "stage": g.node_stage(a.nid), "label": e.label}
    return {"limit": blind, "pairs": sorted(pairs.values(), key=lambda d: -d["drop"])}


@dataclass
class Validation:
    geo: Geometry
    graph: Graph
    settings: Settings
    limits: dict[str, float]
    rules: dict[str, float]
    results: dict[str, Any]
    seconds: float


def validate(
    tm: TileMap,
    settings: Settings | None = None,
    jobs: int = 1,
    progress: Callable[[str], None] | None = None,
    refine: bool = True,
    bifurcations: bool = True,
    stages: list[tuple[str, float, float, float, float]] | None = None,
) -> Validation:
    t_start = time.time()
    settings = settings or Settings()
    p = default_params()
    metrics = load_metrics()
    limits = screen_limits(metrics, p)
    rules = rules_by_id(metrics)
    geo = build_geometry(tm, p, stages=stages)
    if progress:
        progress(
            f"  geometria: {len(geo.platforms)} plataformas ({sum(1 for q in geo.platforms if q.in_region)} na área jogável), "
            f"{len(geo.zones)} zonas, spawn na plataforma {geo.spawn_pid}"
        )
    g = build_graph(geo, settings, limits, jobs, progress)
    ctx = _Ctx(geo)
    order = zone_order(g)
    res: dict[str, Any] = {"order": order}

    # alcançabilidade em camadas
    stage_reach = []
    for k in range(len(order)):
        r = layered_route(g, cost_fastest, goal_stage=k + 1)
        stage_reach.append(r is not None)
    res["stage_reach"] = stage_reach

    def pick_routes() -> dict[str, Route | None]:
        return {
            "fastest": layered_route(g, cost_fastest),
            "safest": layered_route(g, cost_safest),
            "medium": layered_route(g, cost_medium),
        }

    routes = pick_routes()
    togo, togo_unit = togo_tables(g)
    # refinamento das janelas nas rotas; a janela da família é só uma estimativa, então as rotas segura
    # e do jogador médio são escolhidas de novo com as janelas refinadas (até estabilizar)
    if refine:
        for it in range(4):
            if not refine_routes(g, routes, togo, togo_unit, jobs, progress, f" (passada {it + 1})"):
                break
            routes = pick_routes()
        # as rotas finais ficam com todas as manobras refinadas (sem escolher de novo)
        refine_routes(g, routes, togo, togo_unit, jobs, progress, " (final)")
    res["routes"] = {k: _route_summary(g, r) for k, r in routes.items()}
    res["route_objs"] = routes

    # filtros: dá para terminar sem X?
    res["filters"] = {}
    for name, allow in FILTERS.items():
        if name == "tudo":
            continue
        r = layered_route(g, cost_fastest, allow)
        res["filters"][name] = _route_summary(g, r, refined=False)

    # por trecho (a partir do começo do trecho na rota mais rápida)
    base_route = routes["fastest"] or routes["medium"]
    sections = []
    if base_route is not None:
        for k, zid in enumerate(order):
            src = section_sources(g, base_route, k)
            if src is None:
                continue
            sec = {"zone": zid, "src": src, "filters": {}}
            for name, allow in FILTERS.items():
                if name == "tudo":
                    continue
                rr = section_reachable(g, src, k, allow)
                sec["filters"][name] = None if rr is None else _route_summary(g, rr, refined=False)["time"]
            sections.append(sec)
    res["sections"] = sections

    # por estágio (E1..E9) na rota mais rápida: dá para passar só com gancho / sem gancho?
    res["stages"] = stage_analysis(g, base_route, bifurcations) if base_route else []

    # ilhas e armadilhas
    finish_from = finish_reachers(g)
    res["islands"] = [q for q in geo.platforms if q.in_region and q.pid not in g.reached]
    res["traps"] = [
        q for q in geo.platforms if q.pid in g.reached and not any(n in finish_from for n in g.plat_nodes.get(q.pid, []))
    ]
    res["anchors"] = anchor_analysis(g, limits)
    res["steps"] = step_analysis(g, rules)
    res["drops"] = drop_analysis(g, limits)
    # trajetórias das rotas (para o desenho)
    traj: dict[int, list[tuple[float, float]]] = {}
    for r in routes.values():
        if r is None:
            continue
        for ei in r.edge_ids():
            e = g.edges[ei]
            if ei in traj:
                continue
            if e.spec is None:
                a, b = g.nodes[e.src], g.nodes[e.dst]
                traj[ei] = [(a.x, a.y), (b.x, b.y)]
            else:
                o = run_spec(ctx, e.spec, record_every=2)
                traj[ei] = o.trajectory if o else []
    res["trajectories"] = traj
    return Validation(geo, g, settings, limits, rules, res, time.time() - t_start)


def finish_reachers(g: Graph) -> set[int]:
    """Nós de onde se chega à chegada (sem contar a ordem dos checkpoints)."""
    rev: dict[int, list[int]] = defaultdict(list)
    for e in g.edges:
        rev[e.dst].append(e.src)
    goal: set[int] = set()
    for e in g.edges:
        if "fin" in e.touched:
            goal.add(e.src)
    for pid, ids in g.plat_nodes.items():
        if "fin" in g.geo.platforms[pid].zone_x:
            goal.update(ids)
    seen = set(goal)
    stack = list(goal)
    while stack:
        n = stack.pop()
        for m in rev.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return seen


def stage_analysis(g: Graph, route: Route, bifurcations: bool = True) -> list[dict[str, Any]]:
    """Para cada estágio cruzado pela rota: tempo, manobras e se dá para passar com filtros."""
    steps = route.steps
    out = []
    i = 0
    while i < len(steps):
        st_name = g.node_stage(steps[i][0])
        j = i
        while j + 1 < len(steps) and g.node_stage(steps[j + 1][0]) == st_name:
            j += 1
        entry = steps[i]
        exit_ = steps[j + 1] if j + 1 < len(steps) else steps[j]
        edges = [steps[q][2] for q in range(i + 1, min(j + 2, len(steps))) if steps[q][2] is not None]
        es = [g.edges[ei] for ei in edges]
        ms = [e for e in es if e.maneuver]
        kinds: dict[str, int] = defaultdict(int)
        for e in ms:
            kinds[e.label] += 1
        wins = [e.w_eff for e in ms]
        info = {
            "stage": st_name,
            "time": sum(e.time for e in es),
            "maneuvers": len(ms),
            "kinds": dict(kinds),
            "min_window": min(wins) if wins else INF,
            "filters": {},
            "entry": entry[0],
            "exit": exit_[0],
        }
        if exit_[0] != entry[0]:
            for name, allow in FILTERS.items():
                if name == "tudo":
                    continue
                info["filters"][name] = _node_route(g, entry[0], exit_[0], allow)
            if bifurcations:
                info["disjoint"] = disjoint_between(g, entry[0], exit_[0])
        out.append(info)
        i = j + 1
    # junta pedaços repetidos do mesmo estágio (a rota pode entrar e sair) só na apresentação
    return out


def _node_route(g: Graph, src: int, dst: int, allow: EdgeFilter, with_path: bool = False) -> Any:
    """Tempo do caminho mais rápido de src a dst usando só arestas permitidas (ou None).
    Com `with_path`, devolve (tempo, [arestas])."""
    dist = {src: 0.0}
    prev: dict[int, int] = {}
    heap = [(0.0, src)]
    while heap:
        d, n = heapq.heappop(heap)
        if n == dst:
            if not with_path:
                return d
            path = []
            while n in prev:
                ei = prev[n]
                path.append(ei)
                n = g.edges[ei].src
            return d, path[::-1]
        if d > dist.get(n, INF):
            continue
        for ei in g.out.get(n, ()):
            e = g.edges[ei]
            if not allow(e):
                continue
            nd = d + e.time
            if nd < dist.get(e.dst, INF):
                dist[e.dst] = nd
                prev[e.dst] = ei
                heapq.heappush(heap, (nd, e.dst))
    return None


# --------------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Valida um mapa simulando o movimento (ADR 0052, etapa 3).")
    ap.add_argument("tiles", help="maps/<mapa>/tiles.json")
    ap.add_argument("--out", help="relatório .md (o .svg vai junto, mesmo nome)")
    ap.add_argument("--quick", action="store_true", help="menos manobras por ponto (mais rápido, menos completo)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1), help="processos (padrão: CPUs - 1)")
    ap.add_argument("--no-refine", action="store_true", help="não refina as janelas das rotas")
    args = ap.parse_args(argv)

    from tools.mapkit import report  # noqa: PLC0415

    path = Path(args.tiles)
    tm = TileMap.load(path)
    settings = Settings.quick() if args.quick else Settings()
    out = Path(args.out) if args.out else DEFAULT_OUT_DIR / f"validacao-{path.resolve().parent.name}.md"
    print(f"Validando {path} ({tm.width} x {tm.height} células, {len(tm.rects())} retângulos)"
          f"{' [rápido]' if args.quick else ''} com {args.jobs} processo(s)...")
    v = validate(tm, settings, jobs=args.jobs, progress=print, refine=not args.no_refine)
    md, svg = report.render(v, svg_name=out.with_suffix(".svg").name, tiles_path=path.as_posix())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf8", newline="\n")
    out.with_suffix(".svg").write_text(svg, encoding="utf8", newline="\n")
    print(report.console_summary(v))
    print(f"Gravado: {out} e {out.with_suffix('.svg').name} ({v.seconds:.0f} s)")
    return 0


if __name__ == "__main__":
    # Roda pelo módulo do pacote (não por __main__) para os processos trabalhadores e o report.py
    # verem as mesmas classes.
    from tools.mapkit.validate import main as _main

    sys.exit(_main())
