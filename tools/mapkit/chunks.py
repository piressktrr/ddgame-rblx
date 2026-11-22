"""Biblioteca de TRECHOS (ADR 0052, etapa 4): formato `race-and-escape/chunk@1`.

Um trecho é um pedaço de mapa (grade `tiles@1`, mesma legenda) com metadados: tema, padrão, mecânicas,
dificuldade alvo, portas de entrada/saída e, se for o caso, as faixas (rotas) em que ele se divide.
O formato está documentado em `maps/trechos/README.md`.

Rodar da raiz do repositório (valida cada trecho SOZINHO, da entrada até a saída, e grava as prévias):

    python -I -X utf8 tools/mapkit/chunks.py                         # todos de maps/trechos
    python -I -X utf8 tools/mapkit/chunks.py maps/trechos/ex-vao-gancho.json --out pasta/
    python -I -X utf8 tools/mapkit/chunks.py --static                # só a conferência estática (rápida)

Em código:

    from tools.mapkit.chunks import Chunk, load_library, check_chunk, validate_chunk
    lib = load_library()                       # id -> Chunk
    problems = check_chunk(lib["ex-corredor"])   # portas, chão das portas, metadados
    rep = validate_chunk(lib["ex-corredor"])     # ChunkReport: rota solo, tempos, janelas, caminhos, faixas

Como o trecho é validado sozinho: ele vai para um mapa de teste com "almofadas" em volta (corredor de
entrada com o spawn, corredor/sala de saída com a FinishLine, o resto das laterais fechado com bloco sem
gancho) e o `validate.py` joga esse mapa. As almofadas são uma aproximação do vizinho; a verdade é a
validação do mapa montado (`assemble.py`).
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    # Rodado como script (python -I tools/mapkit/chunks.py): a raiz do repo entra no sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.mapkit import validate as V  # noqa: E402
from tools.mapkit.luau_config import REPO_ROOT  # noqa: E402
from tools.mapkit.tiles import FORMAT as TILES_FORMAT  # noqa: E402
from tools.mapkit.tiles import TileMap  # noqa: E402
from tools.mapkit.tiles import dumps as tiles_dumps  # noqa: E402

CHUNK_FORMAT = "race-and-escape/chunk@1"
SCALE_PATH = REPO_ROOT / "maps" / "scale.json"
LIBRARY_DIR = REPO_ROOT / "maps" / "trechos"
BASE_CELL = 2  # studs: célula do MapBuilder (UNIT do plugin)
DEFAULT_BLOCK_CELLS = 2  # bloco padrão enquanto maps/scale.json não existir (2 células = 4 studs)
SIDES = ("L", "R", "T", "B")
OPPOSITE = {"L": "R", "R": "L", "T": "B", "B": "T"}
SIDE_PT = {"L": "esquerda", "R": "direita", "T": "cima", "B": "baixo"}
RHYTHMS = ("apertado", "amplo", "gargalo", "respiro")
LANE_KINDS = ("rapida", "segura", "outra")
PAD = 8  # células (de 2 studs) de almofada em volta do trecho no mapa de teste

# Mecânicas que um trecho pode declarar (exigidas/opcionais). As 5 primeiras + hookonce/oneway/unfreeze
# o validador consegue ver na rota; as outras são só conferidas pela presença do elemento na grade.
MECHANICS: dict[str, str] = {
    "walk": "andar",
    "jump": "pulo",
    "double": "pulo duplo",
    "hook": "gancho",
    "momentum": "embalo do gancho",
    "hookonce": "gancho único (verde)",
    "hookthrough": "gancho atravessa (preto)",
    "unhookable": "sem gancho (xadrez)",
    "freeze": "gelo",
    "unfreeze": "degelo",
    "oneway": "mão única",
    "kill": "zona mortal (vermelho)",
    "solo": "zona solo",
    "hammer": "martelo",
    "bouncer": "bouncer",
}
# mecânica -> elementos que precisam existir na grade (conferência estática)
MECHANIC_ELEMENTS: dict[str, tuple[str, ...]] = {
    "hookonce": ("HookOnce",),
    "hookthrough": ("HookThrough",),
    "unhookable": ("Unhookable",),
    "freeze": ("Freeze",),
    "unfreeze": ("Unfreeze",),
    "oneway": ("OneWay",),
    "kill": ("Kill",),
    "solo": ("SoloStart", "SoloEnd"),
}
# rótulo da manobra do validador -> mecânicas
LABEL_MECHANICS: dict[str, tuple[str, ...]] = {
    "walk": ("walk",),
    "jump": ("jump",),
    "double": ("jump", "double"),
    "hook": ("hook",),
    "jump+hook": ("jump", "hook"),
    "hook+momentum": ("hook", "momentum"),
    "hook+double": ("hook", "double"),
}
SEEN_BY_VALIDATOR = ("walk", "jump", "double", "hook", "momentum", "hookonce", "oneway", "unfreeze")
# elementos que o montador põe (o trecho não deve trazer)
ASSEMBLER_ELEMENTS = ("StartLine", "FinishLine", "Checkpoint", "RaceStart")


class ChunkError(ValueError):
    """Trecho mal formado (não dá nem para carregar)."""


# --------------------------------------------------------------------------------------------------
# Bloco padrão (maps/scale.json)
# --------------------------------------------------------------------------------------------------


def _find_key(data: Any, key: str) -> Any:
    if isinstance(data, dict):
        if key in data and isinstance(data[key], (int, float)) and not isinstance(data[key], bool):
            return data[key]
        for v in data.values():
            found = _find_key(v, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for v in data:
            found = _find_key(v, key)
            if found is not None:
                return found
    return None


def default_block_cells(path: Path | None = None) -> int:
    """Células (de 2 studs) por bloco padrão. Lê `maps/scale.json` (chave `block_cells` ou `block_studs`,
    em qualquer nível do JSON); sem arquivo ou sem chave válida: 2 células = 4 studs."""
    path = path or SCALE_PATH
    if not path.exists():
        return DEFAULT_BLOCK_CELLS
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return DEFAULT_BLOCK_CELLS
    cells = _find_key(data, "block_cells")
    if cells is not None and float(cells).is_integer() and cells >= 1:
        return int(cells)
    studs = _find_key(data, "block_studs")
    if studs is not None and studs >= BASE_CELL and float(studs / BASE_CELL).is_integer():
        return int(studs // BASE_CELL)
    return DEFAULT_BLOCK_CELLS


# --------------------------------------------------------------------------------------------------
# Modelo
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Door:
    """Abertura na borda do trecho. L/R: `pos` = linha (j, de baixo) do pé, a 1ª linha livre logo acima
    do chão da porta; `width` = linhas livres (altura). T/B: `pos` = 1ª coluna (i) livre; `width` = colunas."""

    id: str
    role: str  # entry | exit
    side: str  # L | R | T | B
    pos: int
    width: int

    @property
    def horizontal(self) -> bool:
        return self.side in ("L", "R")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "role": self.role, "side": self.side, "pos": self.pos, "width": self.width}


@dataclass(frozen=True)
class Lane:
    """Faixa (rota) de um trecho que se divide: passa pela área [i0..i1] x [j0..j1] (células, inclusive)."""

    id: str
    name: str
    kind: str  # rapida | segura | outra
    area: tuple[int, int, int, int]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "kind": self.kind, "area": list(self.area)}


@dataclass
class Chunk:
    id: str
    name: str
    tiles: TileMap
    doors: list[Door]
    theme: str = ""
    pattern: str = ""
    rhythm: str | None = None
    difficulty: int = 1
    solo: bool = True
    checkpoint_end: bool = False
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    lanes: list[Lane] = field(default_factory=list)
    notes: str = ""
    generated: bool = False  # peça gerada pelo montador (respiro, degraus, curva...)
    mirrored: bool = False
    path: Path | None = None

    # ------------------------------------------------------------------ acesso

    @property
    def width(self) -> int:
        return self.tiles.width

    @property
    def height(self) -> int:
        return self.tiles.height

    @property
    def cell(self) -> float:
        return float(self.tiles.cell)

    def entries(self) -> list[Door]:
        return [d for d in self.doors if d.role == "entry"]

    def exits(self) -> list[Door]:
        return [d for d in self.doors if d.role == "exit"]

    def door(self, door_id: str) -> Door:
        for d in self.doors:
            if d.id == door_id:
                return d
        raise KeyError(f"trecho {self.id}: porta {door_id!r} não existe")

    # ------------------------------------------------------------------ transformações

    def scaled(self, base_cell: float = BASE_CELL) -> "Chunk":
        """O mesmo trecho em células de `base_cell` studs (cada caractere vira k x k células)."""
        k = self.cell / base_cell
        if abs(k - round(k)) > 1e-9 or k < 1:
            raise ChunkError(f"trecho {self.id}: célula {self.cell} não é múltiplo de {base_cell}")
        k = int(round(k))
        if k == 1:
            return self
        t = self.tiles
        nt = TileMap(
            name=t.name,
            cell=base_cell,
            origin=t.origin,
            width=t.width * k,
            height=t.height * k,
            source=t.source,
            collide=dict(t.collide),
        )
        for (i, j), el in t.cells.items():
            for a in range(k):
                for b in range(k):
                    nt.cells[(i * k + a, j * k + b)] = el
                    if (i, j) in t.directions:
                        nt.directions[(i * k + a, j * k + b)] = t.directions[(i, j)]
                    if (i, j) in t.attributes:
                        nt.attributes[(i * k + a, j * k + b)] = dict(t.attributes[(i, j)])
        if t.spawn:
            nt.spawn = (t.spawn[0] * k, t.spawn[1] * k)
        doors = [Door(d.id, d.role, d.side, d.pos * k, d.width * k) for d in self.doors]
        lanes = [
            Lane(ln.id, ln.name, ln.kind, (ln.area[0] * k, ln.area[1] * k, ln.area[2] * k + k - 1, ln.area[3] * k + k - 1))
            for ln in self.lanes
        ]
        return self._copy(nt, doors, lanes)

    def mirrored_copy(self) -> "Chunk":
        """Espelho na horizontal (o trecho passa a correr para o outro lado): L <-> R e mão única Left <-> Right."""
        t = self.tiles
        w = t.width
        nt = TileMap(name=t.name, cell=t.cell, origin=t.origin, width=w, height=t.height, source=t.source, collide=dict(t.collide))
        swap = {"Left": "Right", "Right": "Left"}
        for (i, j), el in t.cells.items():
            nt.cells[(w - 1 - i, j)] = el
        for (i, j), d in t.directions.items():
            nt.directions[(w - 1 - i, j)] = swap.get(d, d)
        for (i, j), a in t.attributes.items():
            nt.attributes[(w - 1 - i, j)] = dict(a)
        if t.spawn:
            nt.spawn = (w - 1 - t.spawn[0], t.spawn[1])
        doors = []
        for d in self.doors:
            if d.horizontal:
                doors.append(Door(d.id, d.role, OPPOSITE[d.side], d.pos, d.width))
            else:
                doors.append(Door(d.id, d.role, d.side, w - d.pos - d.width, d.width))
        lanes = [Lane(ln.id, ln.name, ln.kind, (w - 1 - ln.area[2], ln.area[1], w - 1 - ln.area[0], ln.area[3])) for ln in self.lanes]
        c = self._copy(nt, doors, lanes)
        c.mirrored = not self.mirrored
        return c

    def with_roles(self, entry: str, exit_: str) -> "Chunk":
        """Cópia com só duas portas: `entry` vira entrada e `exit_` saída (peças geradas usam nos dois sentidos)."""
        a, b = self.door(entry), self.door(exit_)
        doors = [Door(a.id, "entry", a.side, a.pos, a.width), Door(b.id, "exit", b.side, b.pos, b.width)]
        return self._copy(self.tiles, doors, list(self.lanes))

    def _copy(self, tiles: TileMap, doors: list[Door], lanes: list[Lane]) -> "Chunk":
        return Chunk(
            id=self.id,
            name=self.name,
            tiles=tiles,
            doors=doors,
            theme=self.theme,
            pattern=self.pattern,
            rhythm=self.rhythm,
            difficulty=self.difficulty,
            solo=self.solo,
            checkpoint_end=self.checkpoint_end,
            required=self.required,
            optional=self.optional,
            lanes=lanes,
            notes=self.notes,
            generated=self.generated,
            mirrored=self.mirrored,
            path=self.path,
        )

    # ------------------------------------------------------------------ JSON

    @classmethod
    def from_dict(cls, data: dict, path: Path | None = None, block_cells: int | None = None) -> "Chunk":
        where = f" ({path})" if path else ""
        if data.get("format") != CHUNK_FORMAT:
            raise ChunkError(f"formato não suportado{where}: {data.get('format')!r} (esperado {CHUNK_FORMAT})")
        if not data.get("id"):
            raise ChunkError(f"trecho sem id{where}")
        tdata = dict(data.get("tiles") or {})
        if not tdata:
            raise ChunkError(f"trecho {data['id']} sem grade (`tiles`){where}")
        tdata.setdefault("format", TILES_FORMAT)
        tdata.setdefault("name", data["id"])
        tdata.setdefault("origin", [0, 0])
        if "cell" not in tdata:
            tdata["cell"] = BASE_CELL * (block_cells or default_block_cells())
        rows = tdata.get("rows") or []
        tdata.setdefault("height", len(rows))
        tdata.setdefault("width", len(rows[0]) if rows else 0)
        try:
            tiles = TileMap.from_dict(tdata)
        except (KeyError, ValueError) as exc:
            raise ChunkError(f"trecho {data['id']}: grade inválida{where}: {exc}") from exc
        doors = []
        for n, d in enumerate(data.get("doors") or []):
            try:
                door = Door(str(d.get("id") or f"p{n + 1}"), str(d["role"]), str(d["side"]), int(d["pos"]), int(d["width"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ChunkError(f"trecho {data['id']}: porta {n + 1} inválida{where}: {exc}") from exc
            if door.role not in ("entry", "exit"):
                raise ChunkError(f"trecho {data['id']}: porta {door.id} com role {door.role!r} (entry/exit){where}")
            if door.side not in SIDES:
                raise ChunkError(f"trecho {data['id']}: porta {door.id} com lado {door.side!r} (L/R/T/B){where}")
            doors.append(door)
        lanes = []
        for n, ln in enumerate(data.get("lanes") or []):
            try:
                area = tuple(int(v) for v in ln["area"])
                assert len(area) == 4
            except (KeyError, TypeError, ValueError, AssertionError) as exc:
                raise ChunkError(f"trecho {data['id']}: faixa {n + 1} sem `area` [i0, j0, i1, j1]{where}") from exc
            i0, j0, i1, j1 = area
            lanes.append(
                Lane(str(ln.get("id") or f"f{n + 1}"), str(ln.get("name") or ""), str(ln.get("kind") or "outra"),
                     (min(i0, i1), min(j0, j1), max(i0, i1), max(j0, j1)))
            )
        mech = data.get("mechanics") or {}
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or data["id"]),
            tiles=tiles,
            doors=doors,
            theme=str(data.get("theme") or ""),
            pattern=str(data.get("pattern") or ""),
            rhythm=data.get("rhythm"),
            difficulty=int(data.get("difficulty", 1)),
            solo=bool(data.get("solo", True)),
            checkpoint_end=bool(data.get("checkpoint_end", False)),
            required=tuple(mech.get("required") or ()),
            optional=tuple(mech.get("optional") or ()),
            lanes=lanes,
            notes=str(data.get("notes") or ""),
            path=path,
        )

    @classmethod
    def load(cls, path: str | Path, block_cells: int | None = None) -> "Chunk":
        p = Path(path)
        try:
            data = json.loads(p.read_text(encoding="utf8"))
        except ValueError as exc:
            raise ChunkError(f"JSON inválido em {p}: {exc}") from exc
        return cls.from_dict(data, p, block_cells)

    def to_dict(self) -> dict[str, Any]:
        tiles = self.tiles.to_dict()
        tiles.pop("format", None)
        tiles.pop("name", None)
        tiles.pop("source", None)
        if tiles.get("spawn") is None:
            tiles.pop("spawn", None)
        for k in ("directions", "attributes"):
            if not tiles.get(k):
                tiles.pop(k, None)
        return {
            "format": CHUNK_FORMAT,
            "id": self.id,
            "name": self.name,
            "theme": self.theme,
            "pattern": self.pattern,
            "rhythm": self.rhythm,
            "difficulty": self.difficulty,
            "solo": self.solo,
            "checkpoint_end": self.checkpoint_end,
            "mechanics": {"required": list(self.required), "optional": list(self.optional)},
            "doors": [d.to_dict() for d in self.doors],
            "lanes": [ln.to_dict() for ln in self.lanes],
            "notes": self.notes,
            "tiles": tiles,
        }

    def dumps(self) -> str:
        return dumps_chunk(self.to_dict())

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.dumps(), encoding="utf8", newline="\n")


def _one(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))


def dumps_chunk(data: dict[str, Any]) -> str:
    """JSON estável do trecho: metadados um por linha, portas/faixas uma por linha, grade como o tiles@1."""
    lines = ["{"]
    items = list(data.items())
    for n, (key, value) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        if key == "tiles":
            sub = tiles_dumps(value).rstrip("\n").split("\n")
            lines.append(f" {_one(key)}: {sub[0]}")
            lines.extend(" " + s for s in sub[1:-1])
            lines.append(f" {sub[-1]}{comma}")
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            lines.append(f" {_one(key)}: [")
            for m, v in enumerate(value):
                lines.append(f"  {_one(v)}{',' if m < len(value) - 1 else ''}")
            lines.append(f" ]{comma}")
        else:
            lines.append(f" {_one(key)}: {_one(value)}{comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def load_library(paths: Iterable[str | Path] | None = None, block_cells: int | None = None) -> dict[str, Chunk]:
    """Carrega os trechos (`*.json` de chunk@1) das pastas/arquivos dados (padrão: maps/trechos, com
    subpastas). Ignora JSON de outro formato. Id repetido = erro."""
    out: dict[str, Chunk] = {}
    files: list[Path] = []
    for p in [Path(x) for x in (paths or [LIBRARY_DIR])]:
        if not p.is_absolute() and not p.exists():
            p = REPO_ROOT / p
        if p.is_dir():
            files.extend(sorted(q for q in p.rglob("*.json") if "previa" not in q.parts))
        elif p.exists():
            files.append(p)
        else:
            raise ChunkError(f"trecho/pasta não encontrado: {p}")
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf8"))
        except ValueError as exc:
            raise ChunkError(f"JSON inválido em {f}: {exc}") from exc
        if not isinstance(data, dict) or data.get("format") != CHUNK_FORMAT:
            continue
        c = Chunk.from_dict(data, f, block_cells)
        if c.id in out:
            raise ChunkError(f"id de trecho repetido: {c.id} ({out[c.id].path} e {f})")
        out[c.id] = c
    return out


# --------------------------------------------------------------------------------------------------
# Conferência estática e encaixe
# --------------------------------------------------------------------------------------------------


def door_cells(c: Chunk, d: Door) -> list[tuple[int, int]]:
    """Células da borda que formam a abertura da porta."""
    if d.side == "L":
        return [(0, j) for j in range(d.pos, d.pos + d.width)]
    if d.side == "R":
        return [(c.width - 1, j) for j in range(d.pos, d.pos + d.width)]
    if d.side == "T":
        return [(i, c.height - 1) for i in range(d.pos, d.pos + d.width)]
    return [(i, 0) for i in range(d.pos, d.pos + d.width)]


def _solid(t: TileMap, i: int, j: int) -> bool:
    el = t.get(i, j)
    return el is not None and el != "OneWay" and t.collides(el)


def check_chunk(c: Chunk) -> list[str]:
    """Problemas que dá para ver sem simular. Cada item começa com "erro:" ou "aviso:"."""
    out: list[str] = []
    p = V.default_params()
    t = c.tiles
    if not c.solo:
        out.append("erro: `solo` é false — todo trecho tem de dar para passar sozinho (ADR 0055)")
    if not 1 <= c.difficulty <= 5:
        out.append(f"erro: dificuldade alvo {c.difficulty} fora de 1–5")
    if c.rhythm is not None and c.rhythm not in RHYTHMS:
        out.append(f"aviso: ritmo {c.rhythm!r} desconhecido ({', '.join(RHYTHMS)})")
    if not c.entries():
        out.append("erro: sem porta de entrada")
    if not c.exits():
        out.append("erro: sem porta de saída")
    ids = [d.id for d in c.doors]
    if len(set(ids)) != len(ids):
        out.append("erro: id de porta repetido")
    for m in c.required + c.optional:
        if m not in MECHANICS:
            out.append(f"aviso: mecânica {m!r} desconhecida")
    for m in c.required:
        els = MECHANIC_ELEMENTS.get(m)
        if els and not any(t.counts().get(e) for e in els):
            out.append(f"aviso: mecânica exigida {m!r}, mas a grade não tem {'/'.join(els)}")
    for el in ASSEMBLER_ELEMENTS:
        if t.counts().get(el):
            out.append(f"aviso: o trecho tem {el}; quem põe largada/checkpoint/chegada é o montador")
    for d in c.doors:
        name = f"porta {d.id} ({SIDE_PT[d.side]})"
        span = c.height if d.horizontal else c.width
        if d.width < 1 or d.pos < 0 or d.pos + d.width > span:
            out.append(f"erro: {name} fora da borda (pos {d.pos}, largura {d.width}, borda de {span} células)")
            continue
        blocked = [cell for cell in door_cells(c, d) if _solid(t, *cell)]
        if blocked:
            out.append(f"erro: {name} tem {len(blocked)} célula(s) sólida(s) na abertura, ex. {blocked[0]}")
        studs = d.width * c.cell
        if d.horizontal:
            if studs < p.box_height:
                out.append(f"erro: {name} com {studs:g} studs de altura; o corpo tem {p.box_height:g}")
            col = 0 if d.side == "L" else c.width - 1
            if d.pos == 0 or not _solid(t, col, d.pos - 1):
                out.append(f"erro: {name} sem chão (a célula ({col}, {d.pos - 1}) tem de ser sólida)")
        elif studs < 2 * p.half_width:
            out.append(f"erro: {name} com {studs:g} studs de largura; o corpo tem {2 * p.half_width:g}")
    for ln in c.lanes:
        i0, j0, i1, j1 = ln.area
        if i0 < 0 or j0 < 0 or i1 >= c.width or j1 >= c.height:
            out.append(f"erro: faixa {ln.id} com área fora da grade")
        if ln.kind not in LANE_KINDS:
            out.append(f"aviso: faixa {ln.id} com tipo {ln.kind!r} ({', '.join(LANE_KINDS)})")
    if len(c.lanes) == 1:
        out.append("aviso: só 1 faixa declarada (bifurcação precisa de 2+)")
    return out


def fit(a: Chunk, exit_door: Door | str, b: Chunk, entry_door: Door | str) -> tuple[bool, str]:
    """A saída `exit_door` de `a` encaixa na entrada `entry_door` de `b`? Lados opostos e aberturas que
    deixam o corpo passar (alinhadas pelo chão nas laterais e pela 1ª coluna em cima/embaixo)."""
    ea = a.door(exit_door) if isinstance(exit_door, str) else exit_door
    eb = b.door(entry_door) if isinstance(entry_door, str) else entry_door
    if ea.role != "exit" or eb.role != "entry":
        return False, "a primeira porta tem de ser saída e a segunda, entrada"
    if OPPOSITE[ea.side] != eb.side:
        return False, f"saída pela {SIDE_PT[ea.side]} só encaixa em entrada pela {SIDE_PT[OPPOSITE[ea.side]]} (veio {SIDE_PT[eb.side]})"
    p = V.default_params()
    wa, wb = ea.width * a.cell, eb.width * b.cell
    need = p.box_height if ea.horizontal else 2 * p.half_width
    if min(wa, wb) < need:
        return False, f"abertura comum de {min(wa, wb):g} studs; o corpo precisa de {need:g}"
    return True, "ok"


# --------------------------------------------------------------------------------------------------
# Mapa de teste (trecho sozinho, com almofadas)
# --------------------------------------------------------------------------------------------------


def _pick_doors(c: Chunk, entry: str | None, exit_: str | None) -> tuple[Door, Door]:
    ent = c.door(entry) if entry else (c.entries() or [None])[0]
    ex = c.door(exit_) if exit_ else (c.exits() or [None])[0]
    if ent is None or ex is None:
        raise ChunkError(f"trecho {c.id}: precisa de uma entrada e uma saída")
    return ent, ex


def isolated_map(c: Chunk, entry: str | None = None, exit_: str | None = None) -> TileMap:
    """Mapa de teste: o trecho (em células de 2 studs) com almofadas de PAD células em volta.

    - laterais (fora do trecho): bloco sem gancho, com um corredor aberto em cada porta L/R usada;
    - entrada L/R: o spawn fica no corredor; T: numa sala em cima, ao lado do buraco; B: numa sala embaixo,
      bem debaixo do buraco;
    - saída L/R: FinishLine no chão do corredor; T: sala em cima (chão com buraco, chegada em volta);
      B: sala embaixo (cai pelo buraco na chegada);
    - em cima/embaixo do trecho (fora das salas) é ar, como o céu do MapBuilder.
    A origem é escolhida para que a célula (0, 0) do trecho fique em (0, 0) studs.
    Largada/checkpoint/chegada que o trecho trouxer são tirados (quem põe é o montador)."""
    c = c.scaled(BASE_CELL)
    ent, ex = _pick_doors(c, entry, exit_)
    W, H = c.width, c.height
    ox, oy = PAD, PAD
    TW, TH = W + 2 * PAD, H + 2 * PAD
    cells: dict[tuple[int, int], str] = {}

    def fill(i0: int, j0: int, i1: int, j1: int, el: str | None) -> None:  # [i0, i1) x [j0, j1)
        for i in range(max(0, i0), min(TW, i1)):
            for j in range(max(0, j0), min(TH, j1)):
                if el is None:
                    cells.pop((i, j), None)
                else:
                    cells[(i, j)] = el

    fill(0, 0, ox, TH, "Unhookable")
    fill(ox + W, 0, TW, TH, "Unhookable")
    spawn = None
    for d in (ent, ex):
        if d.side in ("L", "R"):
            i0, i1 = (0, ox) if d.side == "L" else (ox + W, TW)
            fill(i0, oy + d.pos, i1, oy + d.pos + d.width, None)
            if d is ent:
                spawn = (2, oy + d.pos) if d.side == "L" else (TW - 3, oy + d.pos)
            else:
                fill(i0 + 1, oy + d.pos, i1 - 1, oy + d.pos + 1, "FinishLine")
        elif d.side == "T":
            r0 = oy + H  # chão da sala (encostado no topo do trecho)
            a0, a1 = ox + d.pos, ox + d.pos + d.width  # buraco
            fill(a0 - 6, r0, a1 + 6, r0 + 8, "Unhookable")
            fill(a0 - 5, r0 + 1, a1 + 5, r0 + 7, None)
            fill(a0, r0, a1, r0 + 1, None)
            if d is ent:
                spawn = (a0 - 3, r0 + 1)
            else:
                fill(a0 - 5, r0 + 1, a1 + 5, r0 + 2, "FinishLine")
        else:  # B
            a0, a1 = ox + d.pos, ox + d.pos + d.width
            fill(a0 - 6, 0, a1 + 6, oy, "Unhookable")
            fill(a0 - 5, 2, a1 + 5, oy - 1, None)
            fill(a0, oy - 1, a1, oy, None)
            if d is ent:
                spawn = (a0 + d.width // 2, 2)
            else:
                fill(a0 - 5, 2, a1 + 5, 3, "FinishLine")
    tm = TileMap(name=f"trecho:{c.id}", cell=BASE_CELL, origin=(-ox * BASE_CELL, -oy * BASE_CELL), width=TW, height=TH)
    tm.collide = dict(c.tiles.collide)
    for (i, j), el in cells.items():
        tm.cells[(i, j)] = el
    for (i, j), el in c.tiles.cells.items():
        if el in ASSEMBLER_ELEMENTS:
            continue
        tm.cells[(i + ox, j + oy)] = el
        if el == "OneWay":
            tm.directions[(i + ox, j + oy)] = c.tiles.directions.get((i, j), "Up")
    for (i, j), a in c.tiles.attributes.items():
        if c.tiles.get(i, j) not in ASSEMBLER_ELEMENTS:
            tm.attributes[(i + ox, j + oy)] = dict(a)
    tm.spawn = spawn
    return tm


# --------------------------------------------------------------------------------------------------
# Métricas a partir de uma validação (servem para o trecho sozinho e para o mapa montado)
# --------------------------------------------------------------------------------------------------


def difficulty_level(min_window: float, hard: int = 0) -> int:
    """Dificuldade 1–5 pela menor janela de acerto (as faixas do relatório do validador):
    sem precisão (livre) = 1, >= 0,4 s = 2, 0,2–0,4 = 3, 0,1–0,2 = 4, < 0,1 = 5; +1 se 3+ manobras com
    janela < 0,2 s no mesmo trecho (sequência apertada)."""
    if min_window >= V.WINDOW_CAP:
        level = 1
    elif min_window >= 0.4:
        level = 2
    elif min_window >= 0.2:
        level = 3
    elif min_window >= 0.1:
        level = 4
    else:
        level = 5
    if hard >= 3 and level < 5:
        level += 1
    return level


def edge_stats(edges: list[V.Edge], refined: bool = True) -> dict[str, Any]:
    """Tempo, tempo esperado do jogador médio, menor janela etc. de uma sequência de arestas. `refined=False`
    usa a janela da família (a mesma régua para todas as arestas; a refinada só existe nas rotas)."""
    ms = [e for e in edges if e.maneuver]
    wins = [e.w_eff if refined else e.window for e in ms]
    kinds: dict[str, int] = {}
    for e in ms:
        kinds[e.label] = kinds.get(e.label, 0) + 1
    return {
        "time": sum(e.time for e in edges),
        "expected_medium": sum(_medium_cost(e, refined) for e in edges),
        "maneuvers": len(ms),
        "min_window": min(wins, default=V.INF),
        "hard": sum(1 for w in wins if w < 0.2),
        "p_clean": math.prod(V.p_success(w) for w in wins) if wins else 1.0,
        "kinds": kinds,
    }


def _medium_cost(e: V.Edge, refined: bool) -> float:
    if refined or not e.maneuver:
        return V.cost_medium(e)
    ps = V.p_success(e.window)
    return (e.time + V.REACTION) / ps + (1 / ps - 1) * V.RETRY


def mechanics_of(v: V.Validation, edge_ids: Iterable[int]) -> set[str]:
    """Mecânicas que as manobras usaram: rótulos + gancho em HookOnce + passar por mão única/degelo."""
    g = v.graph
    t = v.geo.tiles
    out: set[str] = set()
    traj = v.results.get("trajectories", {})
    for ei in edge_ids:
        e = g.edges[ei]
        if not e.maneuver:
            if abs(g.nodes[e.dst].x - g.nodes[e.src].x) > 1e-6:
                out.add("walk")  # andar na plataforma
            continue
        out.update(LABEL_MECHANICS.get(e.label, ()))
        for ax, ay in e.anchors:
            for dx in (-0.05, 0.05):
                for dy in (-0.05, 0.05):
                    if t.get(*t.cell_at(ax + dx, ay + dy)) == "HookOnce":
                        out.add("hookonce")
        for x, y in traj.get(ei, ()):
            el = t.get(*t.cell_at(x, y))
            if el == "OneWay":
                out.add("oneway")
            elif el == "Unfreeze":
                out.add("unfreeze")
    return out


def _in_box(x: float, y: float, box: tuple[float, float, float, float]) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


Box = tuple[float, float, float, float]


def _safe_cost(e: V.Edge) -> float:
    """Custo "mais seguro" com a janela da família (como `validate.cost_safest`)."""
    if not e.maneuver:
        return e.time * 0.01
    return -math.log(V.p_success(e.window)) * 10 + e.time * 0.01


def lane_route(
    g: V.Graph, src: int, dst: int, box: Box, avoid: Iterable[Box] = (), cost: Any = None
) -> tuple[float, list[int]] | None:
    """Caminho mais rápido de src a dst que passa pela área `box` (studs: x1, y1, x2, y2) — algum nó com o
    pé (ou o root) dentro dela, ou algum gancho preso dentro dela — sem passar (nó ou gancho) pelas áreas
    `avoid` (as outras faixas). Dijkstra em 2 camadas; `cost` = custo da aresta (padrão: tempo)."""
    fo = g.geo.params.feet_offset
    cost = cost or (lambda e: e.time)
    avoid = list(avoid)

    def node_at(nid: int, b: Box) -> bool:
        n = g.nodes[nid]
        return _in_box(n.x, n.y - fo + 0.1, b) or _in_box(n.x, n.y, b)

    def node_in(nid: int) -> bool:
        return node_at(nid, box)

    def edge_in(e: V.Edge) -> bool:
        return any(_in_box(ax, ay, box) for ax, ay in e.anchors)

    def banned(e: V.Edge) -> bool:
        return any(node_at(e.dst, b) or any(_in_box(ax, ay, b) for ax, ay in e.anchors) for b in avoid)

    if any(node_at(src, b) for b in avoid):
        return None

    start = (src, 1 if node_in(src) else 0)
    dist = {start: 0.0}
    prev: dict[tuple[int, int], tuple[tuple[int, int], int]] = {}
    heap = [(0.0, src, start[1])]
    while heap:
        d, n, layer = heapq.heappop(heap)
        if d > dist.get((n, layer), V.INF) + 1e-12:
            continue
        if n == dst and layer == 1:
            path = []
            cur = (n, layer)
            while cur in prev:
                cur, ei = prev[cur]
                path.append(ei)
            return d, path[::-1]
        for ei in g.out.get(n, ()):
            e = g.edges[ei]
            if avoid and banned(e):
                continue
            nl = 1 if (layer or node_in(e.dst) or edge_in(e)) else 0
            key = (e.dst, nl)
            nd = d + cost(e)
            if nd < dist.get(key, V.INF) - 1e-12:
                dist[key] = nd
                prev[key] = ((n, layer), ei)
                heapq.heappush(heap, (nd, e.dst, nl))
    return None


def lane_results(v: V.Validation, src: int, dst: int, lanes: list[Lane], offset: tuple[float, float] = (0.0, 0.0)) -> list[dict[str, Any]]:
    """Mede cada faixa (área em células de `BASE_CELL`, a partir de `offset` em studs) entre src e dst: o
    caminho mais rápido que passa pela área dela SEM passar pelas áreas das outras faixas (bifurcação de
    verdade). Tempo = do caminho mais rápido; risco (`p_clean`, `min_window`, `safe_time`) = do caminho mais
    seguro da faixa. Janelas da família (mesma régua para as faixas)."""
    out = []
    g = v.graph
    boxes = [
        (offset[0] + ln.area[0] * BASE_CELL, offset[1] + ln.area[1] * BASE_CELL,
         offset[0] + (ln.area[2] + 1) * BASE_CELL, offset[1] + (ln.area[3] + 1) * BASE_CELL)
        for ln in lanes
    ]
    for n, ln in enumerate(lanes):
        found = lane_route(g, src, dst, boxes[n], [b for m, b in enumerate(boxes) if m != n])
        info: dict[str, Any] = {"id": ln.id, "name": ln.name, "kind": ln.kind, "ok": found is not None}
        if found is not None:
            info.update(edge_stats([g.edges[ei] for ei in found[1]], refined=False))
            info["edges"] = found[1]
            safe = lane_route(g, src, dst, boxes[n], [b for m, b in enumerate(boxes) if m != n], _safe_cost)
            if safe is not None:
                st = edge_stats([g.edges[ei] for ei in safe[1]], refined=False)
                info["p_clean"] = st["p_clean"]
                info["min_window"] = st["min_window"]
                info["hard"] = st["hard"]
                info["safe_time"] = st["time"]
        out.append(info)
    return out


def branch_count(paths: list[dict[str, Any]], lanes: list[dict[str, Any]]) -> int:
    """Caminhos de verdade: as faixas que passam sozinhas (sem tocar as outras), se forem 2+; senão, os
    caminhos por plataformas diferentes do validador (guloso: é um piso)."""
    ok = sum(1 for ln in lanes if ln["ok"])
    return max(ok if ok >= 2 else 0, len(paths))


def lane_problems(lanes: list[dict[str, Any]]) -> list[str]:
    out = []
    for ln in lanes:
        if not ln["ok"]:
            out.append(f"erro: a faixa {ln['id']} ({ln['name'] or ln['kind']}) não tem rota solo da entrada à saída")
    fast = [ln for ln in lanes if ln["ok"] and ln["kind"] == "rapida"]
    safe = [ln for ln in lanes if ln["ok"] and ln["kind"] == "segura"]
    for f in fast:
        for s in safe:
            if f["time"] >= s["time"] - 0.05:
                out.append(f"aviso: a faixa rápida {f['id']} não é mais rápida que a segura {s['id']} ({f['time']:.2f} s × {s['time']:.2f} s)")
            if s["p_clean"] < f["p_clean"] - 0.02:  # 2 pontos percentuais de folga (janelas da família são grosseiras)
                out.append(f"aviso: a faixa segura {s['id']} é mais arriscada que a rápida {f['id']} (chance sem erro {s['p_clean']:.0%} × {f['p_clean']:.0%})")
    return out


def route_points(v: V.Validation, key: str = "fastest") -> list[tuple[float, float]]:
    r = v.results.get("route_objs", {}).get(key)
    if r is None:
        return []
    traj = v.results.get("trajectories", {})
    g = v.graph
    pts: list[tuple[float, float]] = []
    for ei in r.edge_ids():
        seg = traj.get(ei)
        if not seg:
            a, b = g.nodes[g.edges[ei].src], g.nodes[g.edges[ei].dst]
            seg = [(a.x, a.y), (b.x, b.y)]
        pts.extend(seg)
    return pts


# --------------------------------------------------------------------------------------------------
# Validação de um trecho sozinho
# --------------------------------------------------------------------------------------------------


@dataclass
class ChunkReport:
    id: str
    entry: str
    exit: str
    ok: bool  # existe rota solo da entrada à saída
    problems: list[str]
    target: int
    measured: int | None
    routes: dict[str, dict[str, Any] | None]  # fastest/medium/safest: time, expected_medium, min_window, hard, kinds
    mechanics_used: list[str]
    paths: int  # caminhos de verdade: faixas exclusivas que passam, ou caminhos por plataformas diferentes
    path_list: list[dict[str, Any]]
    lanes: list[dict[str, Any]]
    seconds: float
    sims: int
    route: list[tuple[float, float]] = field(default_factory=list)  # rota mais rápida, studs do trecho
    validation: Any = None  # V.Validation (só no processo que validou)

    def summary(self) -> str:
        if not self.ok:
            return f"{self.id}: SEM ROTA SOLO ({self.seconds:.1f} s)"
        f = self.routes["fastest"] or {}
        m = self.routes["medium"] or {}
        return (
            f"{self.id}: rota solo ok · rápida {f.get('time', 0):.1f} s · jogador médio {m.get('expected_medium', 0):.1f} s · "
            f"dificuldade alvo {self.target} / medida {self.measured} · {self.paths} caminho(s) · {self.seconds:.1f} s"
        )


def _route_stats(v: V.Validation, key: str) -> dict[str, Any] | None:
    r = v.results.get("route_objs", {}).get(key)
    if r is None:
        return None
    st = edge_stats([v.graph.edges[ei] for ei in r.edge_ids()])
    summ = v.results["routes"].get(key) or {}
    st["time"] = summ.get("time", st["time"])
    st["expected_medium"] = summ.get("expected_medium", st["expected_medium"])
    st["by_kind"] = summ.get("by_kind", {})
    return st


def validate_chunk(
    c: Chunk,
    entry: str | None = None,
    exit_: str | None = None,
    settings: V.Settings | None = None,
    refine: bool = True,
    jobs: int = 1,
    keep_validation: bool = True,
) -> ChunkReport:
    """Valida o trecho sozinho: monta o mapa de teste (`isolated_map`), joga com o `validate.py` e mede."""
    t0 = time.time()
    settings = settings or V.Settings.quick()
    problems = [p for p in check_chunk(c)]
    sc = c.scaled(BASE_CELL)
    ent, ex = _pick_doors(sc, entry, exit_)
    tm = isolated_map(c, ent.id, ex.id)
    stage = [(c.id, 0.0, 0.0, sc.width * BASE_CELL, sc.height * BASE_CELL)]
    v = V.validate(tm, settings, jobs=jobs, refine=refine, bifurcations=False, stages=stage)
    fastest = v.results["route_objs"].get("fastest")
    ok = fastest is not None and all(v.results.get("stage_reach", [False]))
    routes = {k: _route_stats(v, k) for k in ("fastest", "medium", "safest")}
    used: set[str] = set()
    paths: list[dict[str, Any]] = []
    lanes: list[dict[str, Any]] = []
    measured = None
    if ok:
        for k in ("fastest", "medium", "safest"):
            r = v.results["route_objs"].get(k)
            if r is not None:
                used |= mechanics_of(v, r.edge_ids())
        src = fastest.steps[0][0]
        dst = fastest.steps[-1][0]
        paths = V.disjoint_between(v.graph, src, dst)
        lanes = lane_results(v, src, dst, sc.lanes)
        problems += lane_problems(lanes)
        safe = routes["safest"] or routes["fastest"]
        measured = difficulty_level(safe["min_window"], safe["hard"])
        if abs(measured - c.difficulty) >= 2:
            problems.append(f"aviso: dificuldade medida {measured} longe da alvo {c.difficulty}")
        for m in c.required:
            if m in SEEN_BY_VALIDATOR and m not in used:
                problems.append(f"aviso: mecânica exigida {m!r} não foi usada por nenhuma rota do validador (dá para passar sem ela)")
        if sc.lanes and branch_count(paths, lanes) < 2:
            problems.append("aviso: faixas declaradas, mas não há 2 faixas que passem sem tocar as outras")
    else:
        problems.insert(0, "erro: o validador não achou rota solo da entrada até a saída")
    rep = ChunkReport(
        id=c.id,
        entry=ent.id,
        exit=ex.id,
        ok=ok,
        problems=problems,
        target=c.difficulty,
        measured=measured,
        routes=routes,
        mechanics_used=sorted(used),
        paths=branch_count(paths, lanes) if ok else 0,
        path_list=[{k: q[k] for k in ("time", "maneuvers", "min_window", "p_clean", "kinds")} for q in paths],
        lanes=[{k: q for k, q in ln.items() if k != "edges"} for ln in lanes],
        seconds=time.time() - t0,
        sims=v.graph.stats.get("sims", 0),
        route=route_points(v, "fastest"),
        validation=v if keep_validation else None,
    )
    return rep


# --------------------------------------------------------------------------------------------------
# Vários trechos em paralelo
# --------------------------------------------------------------------------------------------------


def _validate_job(args: tuple[dict, str, str, bool, bool]) -> ChunkReport:
    data, path, block, full, refine = args
    c = Chunk.from_dict(data, Path(path) if path else None, int(block))
    s = V.Settings() if full else V.Settings.quick()
    return validate_chunk(c, settings=s, refine=refine, keep_validation=False)


def validate_many(chunks: list[Chunk], full: bool = False, refine: bool = True, jobs: int = 1,
                  progress: Any = None) -> list[ChunkReport]:
    """Valida vários trechos (um processo por trecho quando `jobs` > 1). Sem o objeto da validação."""
    block = default_block_cells()
    args = [(c.to_dict(), str(c.path or ""), str(block), full, refine) for c in chunks]
    if jobs <= 1 or len(chunks) <= 1:
        out = []
        for a in args:
            out.append(_validate_job(a))
            if progress:
                progress(out[-1].summary())
        return out
    import multiprocessing as mp

    with mp.get_context("spawn").Pool(min(jobs, len(chunks))) as pool:
        out = []
        for rep in pool.imap(_validate_job, args):
            out.append(rep)
            if progress:
                progress(rep.summary())
    return out


# --------------------------------------------------------------------------------------------------
# Relatório da biblioteca
# --------------------------------------------------------------------------------------------------


def _br(v: float | None, d: int = 1) -> str:
    from tools.mapkit.report import br

    return br(v, d)


def _win(w: float | None) -> str:
    from tools.mapkit.report import win_txt

    return "—" if w is None else win_txt(w)


def library_markdown(chunks: list[Chunk], reports: dict[str, ChunkReport], static: dict[str, list[str]], svg_dir: str = "") -> str:
    lines = [
        "# Biblioteca de trechos — conferência",
        "",
        "Gerado por `python -I -X utf8 tools/mapkit/chunks.py` (ADR 0052, etapa 4). Cada trecho foi jogado "
        "SOZINHO pelo validador, da entrada até a saída, com almofadas em volta (ver `maps/trechos/README.md`). "
        "Tempos incluem ~0,5 s dos corredores de teste.",
        "",
        "| Trecho | Tema | Ritmo | Mecânicas exigidas | Rota solo | Rápida | Jogador médio | Menor janela (segura) | "
        "Dificuldade alvo / medida | Caminhos | Faixas |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in chunks:
        r = reports.get(c.id)
        if r is None:
            lines.append(f"| {c.id} | {c.theme} | {c.rhythm or '—'} | {', '.join(c.required) or '—'} | (não validado) | | | | {c.difficulty} / — | | |")
            continue
        f = r.routes.get("fastest") or {}
        m = r.routes.get("medium") or {}
        s = r.routes.get("safest") or {}
        lanes = "; ".join(
            f"{ln['id']} {'ok' if ln['ok'] else 'SEM ROTA'}" + (f" {_br(ln['time'])} s, janela {_win(ln['min_window'])}" if ln["ok"] else "")
            for ln in r.lanes
        ) or "—"
        lines.append(
            f"| {c.id} | {c.theme or '—'} | {c.rhythm or '—'} | {', '.join(c.required) or '—'} | {'sim' if r.ok else '**não**'} | "
            f"{_br(f.get('time'))} s | {_br(m.get('expected_medium'))} s | {_win(s.get('min_window'))} | "
            f"{c.difficulty} / {r.measured if r.measured is not None else '—'} | {r.paths} | {lanes} |"
        )
    lines.append("")
    for c in chunks:
        r = reports.get(c.id)
        probs = (r.problems if r else static.get(c.id, []))
        lines.append(f"## {c.id} — {c.name}")
        lines.append("")
        meta = [
            f"tema {c.theme or '—'}",
            f"padrão {c.pattern or '—'}",
            f"{c.width} × {c.height} células de {c.cell:g} studs",
            "portas: " + ", ".join(f"{d.id} ({'entrada' if d.role == 'entry' else 'saída'}, {SIDE_PT[d.side]}, pos {d.pos}, largura {d.width})" for d in c.doors),
        ]
        if c.checkpoint_end:
            meta.append("fecha trecho temático (checkpoint depois)")
        lines.append("- " + " · ".join(meta))
        if r and r.ok:
            used = ", ".join(MECHANICS.get(m, m) for m in r.mechanics_used) or "—"
            lines.append(f"- mecânicas usadas pelas rotas do validador: {used}")
            for key, label in (("fastest", "mais rápida"), ("medium", "jogador médio"), ("safest", "mais segura")):
                st = r.routes.get(key)
                if st:
                    kinds = ", ".join(f"{k} ×{n}" for k, n in sorted(st["kinds"].items())) or "só andar"
                    lines.append(f"- rota {label}: {_br(st['time'])} s ({_br(st['expected_medium'])} s esperado), menor janela {_win(st['min_window'])}, manobras: {kinds}")
        if svg_dir:
            lines.append(f"- prévia: [{c.id}.svg]({svg_dir}{c.id}.svg)")
        if probs:
            lines.append("- problemas:")
            lines.extend(f"  - {q}" for q in probs)
        else:
            lines.append("- problemas: nenhum")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Confere e valida trechos (ADR 0052, etapa 4).")
    ap.add_argument("paths", nargs="*", help="arquivos de trecho ou pastas (padrão: maps/trechos)")
    ap.add_argument("--out", help="pasta das prévias e do trechos.md (padrão: maps/trechos/previa)")
    ap.add_argument("--static", action="store_true", help="só a conferência estática (sem simular)")
    ap.add_argument("--full", action="store_true", help="validador completo (mais manobras, mais lento)")
    ap.add_argument("--no-refine", action="store_true", help="não refina as janelas das rotas")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1), help="processos (um trecho por processo)")
    args = ap.parse_args(argv)

    from tools.mapkit import preview  # noqa: PLC0415

    lib = load_library(args.paths or None)
    chunks = list(lib.values())
    out = Path(args.out) if args.out else LIBRARY_DIR / "previa"
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(chunks)} trecho(s); bloco padrão = {default_block_cells()} células")
    static = {c.id: check_chunk(c) for c in chunks}
    reports: dict[str, ChunkReport] = {}
    if not args.static:
        t0 = time.time()
        for r in validate_many(chunks, full=args.full, refine=not args.no_refine, jobs=args.jobs, progress=print):
            reports[r.id] = r
        print(f"validação: {time.time() - t0:.1f} s")
    else:
        for c in chunks:
            print(f"{c.id}: " + ("; ".join(static[c.id]) or "sem problemas"))
    for c in chunks:
        r = reports.get(c.id)
        (out / f"{c.id}.svg").write_text(preview.chunk_svg(c, r), encoding="utf8", newline="\n")
        preview.chunk_png(c, r, out / f"{c.id}.png")
    (out / "trechos.md").write_text(library_markdown(chunks, reports, static, "./"), encoding="utf8", newline="\n")
    print(f"Gravado: {out}/trechos.md e as prévias .svg/.png")
    bad = [r.id for r in reports.values() if not r.ok] + [cid for cid, ps in static.items() if any(p.startswith("erro") for p in ps)]
    return 1 if bad else 0


if __name__ == "__main__":
    from tools.mapkit.chunks import main as _main

    sys.exit(_main())
