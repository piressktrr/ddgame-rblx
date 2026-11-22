"""Mapa como dados: grade de blocos `race-and-escape/tiles@1` (ADR 0052, etapa 2).

Formato documentado em `tools/mapkit/README.md`. Resumo das convenções:

- célula (i, j): i = coluna da esquerda para a direita, j = linha DE BAIXO PARA CIMA (j = 0 é a
  linha mais baixa). A célula cobre x em [x0 + i*cell, x0 + (i+1)*cell) e y em
  [y0 + j*cell, y0 + (j+1)*cell), em studs, no plano Z = 0.
- `rows[0]` é a linha MAIS ALTA (j = height - 1): o arquivo se lê como o mapa visto de frente.
- `directions`, `attributes` e `spawn` usam (i, j), com chave de texto "i,j".

Sem dependências fora da biblioteca padrão. Uso típico:

    from tools.mapkit.tiles import TileMap
    tm = TileMap.load("maps/map01/tiles.json")
    world = tm.to_world()
    world.is_solid(10.0, 3.0)
    world.raycast_hook((10.0, 3.0), (1.0, 1.0), 60.0)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

FORMAT = "race-and-escape/tiles@1"

# Caractere -> id do elemento (src/shared/MapElements.luau) ou None (vazio). Checkpoint e RaceStart
# não são elementos do MapBuilder: existem para mapas antigos (map01).
DEFAULT_LEGEND: dict[str, str | None] = {
    ".": None,
    "#": "Block",
    "x": "Unhookable",
    "h": "HookThrough",
    "f": "Freeze",
    "u": "Unfreeze",
    "o": "OneWay",
    "k": "Kill",
    "g": "HookOnce",
    "S": "StartLine",
    "F": "FinishLine",
    "s": "SoloStart",
    "e": "SoloEnd",
    "c": "Checkpoint",
    "R": "RaceStart",
}

DIRECTIONS = ("Up", "Down", "Left", "Right")
DIRECTION_VECTOR = {"Up": (0.0, 1.0), "Down": (0.0, -1.0), "Left": (-1.0, 0.0), "Right": (1.0, 0.0)}


@dataclass(frozen=True)
class ElementRule:
    """Como um elemento age, espelhando MapElements.luau, HookController e ZoneService."""

    collide: bool  # CanCollide padrão (o corpo bate)
    hook: str | None  # superfície para o gancho quando a peça é consultada: hook/nohook/once/through
    zone: str | None  # efeito ao tocar


RULES: dict[str, ElementRule] = {
    "Block": ElementRule(True, "hook", None),
    "Unhookable": ElementRule(True, "nohook", None),
    "HookThrough": ElementRule(True, "through", None),
    "Freeze": ElementRule(False, None, "freeze"),
    "Unfreeze": ElementRule(False, None, "unfreeze"),
    "OneWay": ElementRule(False, "through", None),  # sólido só contra a seta (OneWayController)
    "Kill": ElementRule(True, "hook", "kill"),  # sólido e prende o gancho (ADR 0049, 0053)
    "HookOnce": ElementRule(True, "once", None),
    "StartLine": ElementRule(False, None, "start"),
    "FinishLine": ElementRule(False, None, "finish"),
    "SoloStart": ElementRule(False, None, "solo_start"),
    "SoloEnd": ElementRule(False, None, "solo_end"),
    "Checkpoint": ElementRule(False, None, "checkpoint"),
    "RaceStart": ElementRule(False, None, "start"),
}


def cell_key(i: int, j: int) -> str:
    return f"{i},{j}"


def parse_key(key: str) -> tuple[int, int]:
    a, b = key.split(",")
    return int(a), int(b)


@dataclass(frozen=True)
class Rect:
    """Retângulo de células iguais: [i, i+w) x [j, j+h)."""

    i: int
    j: int
    w: int
    h: int
    element: str
    direction: str | None = None


@dataclass(frozen=True)
class HookHit:
    point: tuple[float, float]  # onde o raio entra na célula (studs)
    surface: str  # "hook" | "nohook" | "once"
    cell: tuple[int, int]
    distance: float


@dataclass
class TileMap:
    name: str
    cell: float
    origin: tuple[float, float]
    width: int
    height: int
    cells: dict[tuple[int, int], str] = field(default_factory=dict)  # só as não vazias
    directions: dict[tuple[int, int], str] = field(default_factory=dict)
    attributes: dict[tuple[int, int], dict] = field(default_factory=dict)
    spawn: tuple[int, int] | None = None
    source: str = ""
    collide: dict[str, bool] = field(default_factory=dict)  # sobrescreve RULES[...].collide

    # ------------------------------------------------------------------ acesso

    def in_bounds(self, i: int, j: int) -> bool:
        return 0 <= i < self.width and 0 <= j < self.height

    def get(self, i: int, j: int) -> str | None:
        return self.cells.get((i, j))

    def set(self, i: int, j: int, element: str | None, direction: str | None = None) -> None:
        if not self.in_bounds(i, j):
            raise IndexError(f"célula fora da grade: ({i}, {j})")
        if element is None:
            self.cells.pop((i, j), None)
            self.directions.pop((i, j), None)
            return
        if element not in RULES:
            raise ValueError(f"elemento desconhecido: {element}")
        self.cells[(i, j)] = element
        if element == "OneWay":
            self.directions[(i, j)] = direction or "Up"
        else:
            self.directions.pop((i, j), None)

    def direction(self, i: int, j: int) -> str | None:
        return self.directions.get((i, j))

    def collides(self, element: str) -> bool:
        return self.collide.get(element, RULES[element].collide)

    # ------------------------------------------------------------------ células <-> studs

    def cell_at(self, x: float, y: float) -> tuple[int, int]:
        """Célula que contém o ponto (pode estar fora da grade)."""
        return (math.floor((x - self.origin[0]) / self.cell), math.floor((y - self.origin[1]) / self.cell))

    def cell_min(self, i: int, j: int) -> tuple[float, float]:
        return (self.origin[0] + i * self.cell, self.origin[1] + j * self.cell)

    def cell_center(self, i: int, j: int) -> tuple[float, float]:
        return (self.origin[0] + (i + 0.5) * self.cell, self.origin[1] + (j + 0.5) * self.cell)

    def bounds(self) -> tuple[float, float, float, float]:
        """(x1, y1, x2, y2) da grade inteira, em studs."""
        x0, y0 = self.origin
        return (x0, y0, x0 + self.width * self.cell, y0 + self.height * self.cell)

    # ------------------------------------------------------------------ contagens e retângulos

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for element in self.cells.values():
            out[element] = out.get(element, 0) + 1
        return dict(sorted(out.items()))

    def kind(self, i: int, j: int) -> tuple[str, str | None] | None:
        element = self.cells.get((i, j))
        if element is None:
            return None
        return (element, self.directions.get((i, j)) if element == "OneWay" else None)

    def rects(self) -> list[Rect]:
        """Junta células vizinhas iguais (elemento e direção) em retângulos, como o
        src/shared/Logic/GridMerge.luau: ordena por (j, i), estende para a direita e depois sobe
        enquanto a linha inteira bate. Mesmo resultado que o MapBuilder monta."""
        used: set[tuple[int, int]] = set()
        out: list[Rect] = []

        def free(i: int, j: int, kind: tuple[str, str | None]) -> bool:
            return (i, j) not in used and self.kind(i, j) == kind

        for i, j in sorted(self.cells, key=lambda c: (c[1], c[0])):
            if (i, j) in used:
                continue
            kind = self.kind(i, j)
            assert kind is not None
            w = 1
            while free(i + w, j, kind):
                w += 1
            h = 1
            while all(free(i + d, j + h, kind) for d in range(w)):
                h += 1
            for di in range(w):
                for dj in range(h):
                    used.add((i + di, j + dj))
            out.append(Rect(i, j, w, h, kind[0], kind[1]))
        return out

    # ------------------------------------------------------------------ JSON

    @classmethod
    def from_dict(cls, data: dict) -> "TileMap":
        if data.get("format") != FORMAT:
            raise ValueError(f"formato não suportado: {data.get('format')!r} (esperado {FORMAT})")
        legend: dict[str, str | None] = data.get("legend") or DEFAULT_LEGEND
        width, height = int(data["width"]), int(data["height"])
        rows = data["rows"]
        if len(rows) != height:
            raise ValueError(f"rows tem {len(rows)} linhas, height = {height}")
        tm = cls(
            name=data.get("name", ""),
            cell=data.get("cell", 2),
            origin=(data["origin"][0], data["origin"][1]),
            width=width,
            height=height,
            source=data.get("source", ""),
            collide=dict(data.get("collide") or {}),
        )
        for r, row in enumerate(rows):
            if len(row) != width:
                raise ValueError(f"linha {r} tem {len(row)} colunas, width = {width}")
            j = height - 1 - r
            for i, ch in enumerate(row):
                if ch not in legend:
                    raise ValueError(f"caractere {ch!r} fora da legenda (linha {r}, coluna {i})")
                element = legend[ch]
                if element is not None:
                    if element not in RULES:
                        raise ValueError(f"elemento desconhecido na legenda: {element}")
                    tm.cells[(i, j)] = element
        for key, direction in (data.get("directions") or {}).items():
            if direction not in DIRECTIONS:
                raise ValueError(f"direção inválida em {key}: {direction!r}")
            tm.directions[parse_key(key)] = direction
        for (i, j), element in tm.cells.items():
            if element == "OneWay":
                tm.directions.setdefault((i, j), "Up")
        for key, attrs in (data.get("attributes") or {}).items():
            tm.attributes[parse_key(key)] = dict(attrs)
        spawn = data.get("spawn")
        tm.spawn = (int(spawn[0]), int(spawn[1])) if spawn else None
        return tm

    @classmethod
    def load(cls, path: str | Path) -> "TileMap":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf8")))

    def rows(self, legend: dict[str, str | None] | None = None) -> list[str]:
        reverse = {v: k for k, v in (legend or DEFAULT_LEGEND).items()}
        out = []
        for j in range(self.height - 1, -1, -1):
            out.append("".join(reverse[self.cells.get((i, j))] for i in range(self.width)))
        return out

    def to_dict(self) -> dict:
        def sorted_keys(d: dict) -> list[tuple[int, int]]:
            return sorted(d, key=lambda c: (c[1], c[0]))

        data: dict = {
            "format": FORMAT,
            "name": self.name,
            "source": self.source,
            "cell": _num(self.cell),
            "origin": [_num(self.origin[0]), _num(self.origin[1])],
            "width": self.width,
            "height": self.height,
            "legend": dict(DEFAULT_LEGEND),
        }
        if self.collide:
            data["collide"] = dict(sorted(self.collide.items()))
        data["spawn"] = list(self.spawn) if self.spawn else None
        data["directions"] = {
            cell_key(*c): self.directions[c] for c in sorted_keys(self.directions) if self.get(*c) == "OneWay"
        }
        data["attributes"] = {cell_key(*c): dict(sorted(self.attributes[c].items())) for c in sorted_keys(self.attributes)}
        data["rows"] = self.rows()
        return data

    def dumps(self) -> str:
        """JSON estável: chaves numa ordem fixa, uma linha por linha da grade e por entrada de
        directions/attributes/legend (diffs pequenos e legíveis)."""
        return dumps(self.to_dict())

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.dumps(), encoding="utf8", newline="\n")

    # ------------------------------------------------------------------ mundo para o simulador

    def to_world(self, outside_solid: bool = False) -> "TileWorld":
        return TileWorld(self, outside_solid)


def _num(v: float) -> float | int:
    return int(v) if float(v).is_integer() else v


def _one(v) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))


def dumps(data: dict) -> str:
    """Serializa um dicionário de mapa: objetos e listas de 1º nível com um item por linha."""
    lines = ["{"]
    items = list(data.items())
    for n, (key, value) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        if isinstance(value, dict) and value:
            lines.append(f" {_one(key)}: {{")
            sub = list(value.items())
            for m, (k, v) in enumerate(sub):
                lines.append(f"  {_one(k)}: {_one(v)}{',' if m < len(sub) - 1 else ''}")
            lines.append(f" }}{comma}")
        elif key == "rows" and isinstance(value, list) and value:
            lines.append(f" {_one(key)}: [")
            for m, v in enumerate(value):
                lines.append(f"  {_one(v)}{',' if m < len(value) - 1 else ''}")
            lines.append(f" ]{comma}")
        else:
            lines.append(f" {_one(key)}: {_one(value)}{comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


class TileWorld:
    """Consultas de um TileMap em studs, para o simulador (etapa 3 do ADR 0052).

    Aproximações (documentadas no README):
    - tudo é decidido pela célula que contém o ponto; nada de peças giradas ou rampas (a conversão
      já rasterizou o mapa).
    - `is_solid`: o corpo bate em Block, Unhookable, HookThrough, HookOnce e em elementos com
      `collide` ligado no arquivo (mapas antigos: Kill, Freeze... sólidos). A mão única só é
      sólida quando o movimento (vx, vy) vai contra a seta (produto escalar < 0); parado, não é.
      O jogo decide pelo lado em que o personagem inteiro está (OneWayController); um simulador
      fiel deve usar `one_way_at` e a caixa do corpo.
    - `zone_at`: efeito da célula. Zona sólida (collide) age ao encostar: consulte com a caixa do
      corpo crescida pela folga (Config.Zones.TouchMargin), não só com o centro.
    - `raycast_hook`: raio na grade (DDA). Para em superfície que segura o gancho ou que o barra
      (nohook, once); atravessa HookThrough, mão única e peças sem colisão (zonas atravessáveis,
      linhas), como o HookController (RespectCanCollide + exceção de HookThrough/OneWay). A
      célula de onde o raio sai é ignorada (raycast do Roblox não acerta a peça em que começa).
      Sem a esfera de ajuda da mira nem o "uma vez por peça" do HookOnce (fica com o simulador).
    """

    def __init__(self, tiles: TileMap, outside_solid: bool = False):
        self.tiles = tiles
        self.outside_solid = outside_solid

    def element_at(self, x: float, y: float) -> str | None:
        i, j = self.tiles.cell_at(x, y)
        return self.tiles.get(i, j)

    def _outside(self, i: int, j: int) -> bool:
        return not self.tiles.in_bounds(i, j)

    def is_solid_cell(self, i: int, j: int, vx: float = 0.0, vy: float = 0.0) -> bool:
        if self._outside(i, j):
            return self.outside_solid
        element = self.tiles.get(i, j)
        if element is None:
            return False
        if element == "OneWay":
            dx, dy = DIRECTION_VECTOR[self.tiles.direction(i, j) or "Up"]
            return vx * dx + vy * dy < 0
        return self.tiles.collides(element)

    def is_solid(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0) -> bool:
        return self.is_solid_cell(*self.tiles.cell_at(x, y), vx, vy)

    def one_way_at(self, x: float, y: float) -> str | None:
        i, j = self.tiles.cell_at(x, y)
        return self.tiles.direction(i, j) if self.tiles.get(i, j) == "OneWay" else None

    def zone_at(self, x: float, y: float) -> str | None:
        element = self.element_at(x, y)
        return RULES[element].zone if element else None

    def _surface_cell(self, i: int, j: int) -> str | None:
        if self._outside(i, j):
            return "hook" if self.outside_solid else None
        element = self.tiles.get(i, j)
        if element is None:
            return None
        rule = RULES[element]
        if rule.hook == "through":
            return "through"
        if not self.tiles.collides(element):
            return None  # peça sem colisão: o raio do gancho não a enxerga
        return rule.hook or "hook"  # zona sólida sem tag de gancho = superfície normal

    def hook_surface_at(self, x: float, y: float) -> str | None:
        """"hook" | "nohook" | "once" | "through" | None (o gancho passa reto)."""
        return self._surface_cell(*self.tiles.cell_at(x, y))

    def attributes_at(self, x: float, y: float) -> dict:
        return self.tiles.attributes.get(self.tiles.cell_at(x, y), {})

    def raycast_hook(
        self, origin: tuple[float, float], direction: tuple[float, float], max_dist: float
    ) -> HookHit | None:
        """Primeira célula que para o gancho ao longo do raio, ou None se nada até `max_dist`."""
        dx, dy = direction
        length = math.hypot(dx, dy)
        if length == 0 or max_dist <= 0:
            return None
        dx, dy = dx / length, dy / length
        size = self.tiles.cell
        ox, oy = origin
        i, j = self.tiles.cell_at(ox, oy)
        step_i = 1 if dx > 0 else -1
        step_j = 1 if dy > 0 else -1
        x0, y0 = self.tiles.cell_min(i, j)
        inf = math.inf
        t_max_x = ((x0 + size - ox) / dx if dx > 0 else (x0 - ox) / dx) if dx != 0 else inf
        t_max_y = ((y0 + size - oy) / dy if dy > 0 else (y0 - oy) / dy) if dy != 0 else inf
        t_delta_x = size / abs(dx) if dx != 0 else inf
        t_delta_y = size / abs(dy) if dy != 0 else inf
        # Fora da grade, sem `outside_solid`, não há nada para acertar além da caixa.
        limit = max_dist
        while True:
            if t_max_x < t_max_y:
                t = t_max_x
                t_max_x += t_delta_x
                i += step_i
            else:
                t = t_max_y
                t_max_y += t_delta_y
                j += step_j
            if t > limit:
                return None
            if not self.outside_solid and self._outside(i, j) and self._leaving(i, j, step_i, step_j):
                return None
            surface = self._surface_cell(i, j)
            if surface in ("hook", "nohook", "once"):
                return HookHit((ox + dx * t, oy + dy * t), surface, (i, j), t)

    def _leaving(self, i: int, j: int, step_i: int, step_j: int) -> bool:
        """Já saiu da grade e está se afastando dela (nada mais para acertar)."""
        w, h = self.tiles.width, self.tiles.height
        return (i < 0 and step_i < 0) or (i >= w and step_i > 0) or (j < 0 and step_j < 0) or (j >= h and step_j > 0)


def new_map(name: str, width: int, height: int, cell: float = 2, origin: tuple[float, float] = (0, 0)) -> TileMap:
    return TileMap(name=name, cell=cell, origin=origin, width=width, height=height)


def from_rows(rows: Iterable[str], cell: float = 2, origin: tuple[float, float] = (0, 0), name: str = "") -> TileMap:
    """Atalho para testes e trechos: monta um TileMap a partir das linhas (rows[0] = topo)."""
    rows = list(rows)
    return TileMap.from_dict(
        {
            "format": FORMAT,
            "name": name,
            "cell": cell,
            "origin": list(origin),
            "width": len(rows[0]) if rows else 0,
            "height": len(rows),
            "rows": rows,
        }
    )


def iter_cells(tm: TileMap) -> Iterator[tuple[int, int, str]]:
    for (i, j), element in sorted(tm.cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        yield i, j, element
