"""Montador de mapas (ADR 0052, etapa 4): junta TRECHOS (chunks.py) num mapa candidato e o valida.

Rodar da raiz do repositório:

    python -I -X utf8 tools/mapkit/assemble.py plano.json --out maps/<nome>/          # monta, valida (rápido) e relata
    python -I -X utf8 tools/mapkit/assemble.py plano.json --out maps/<nome>/ --full   # validador completo
    python -I -X utf8 tools/mapkit/assemble.py plano.json --no-validate               # só monta e desenha
    python -I -X utf8 tools/mapkit/assemble.py plano.json --chunks                    # + cada trecho sozinho

Grava em `--out` (padrão `maps/<nome do plano>/`): `tiles.json` (o mapa, tiles@1), `montagem.json` (onde ficou
cada peça), `relatorio.md` (tempo por seção e total, curva de dificuldade, bifurcações, problemas),
`mapa.svg`/`mapa.png` (prévia) e `validacao.md`/`validacao.svg` (relatório completo do validador).

Como monta (detalhes e o formato do plano em `tools/mapkit/README.md`, seção "Trechos e montador"):

1. Largada (StartLine + spawn) no começo; depois os trechos na ordem do plano, cada um encaixado pela
   saída do anterior (a entrada dele fica colada na saída, alinhada pelo chão). O trecho é espelhado
   quando precisa correr para o outro lado.
2. Mapa enrolado: quando a fileira passa de `max_width` studs, entra uma CURVA (torre com patamares em
   zigue-zague) que sobe (ou desce) o suficiente para a próxima fileira não encostar na de baixo, e a
   corrida volta no sentido contrário. Se um trecho encostar em outro, entram DEGRAUS gerados antes dele.
3. No fim de cada seção temática, uma sala de CHECKPOINT (elemento `Checkpoint` com `Order`, `Split = true`,
   `Section` e `Name`: o tempo parcial). No fim, a sala de chegada (FinishLine).
4. O validador joga o mapa inteiro sozinho (1 jogador = o critério "dá para terminar sozinho", ADR 0055).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # Rodado como script (python -I tools/mapkit/assemble.py): a raiz do repo entra no sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.mapkit import validate as V  # noqa: E402
from tools.mapkit.chunks import (  # noqa: E402
    BASE_CELL,
    OPPOSITE,
    Chunk,
    ChunkError,
    Door,
    branch_count,
    default_block_cells,
    difficulty_level,
    door_cells,
    edge_stats,
    lane_results,
    load_library,
    route_points,
)
from tools.mapkit.luau_config import REPO_ROOT  # noqa: E402
from tools.mapkit.tiles import TileMap  # noqa: E402

PLAN_FORMAT = "race-and-escape/plan@1"
TARGET_MINUTES = 8.0
CONNECTORS = ("respiro", "degraus", "curva")


class AssembleError(ValueError):
    """O plano não dá para montar (trecho que não existe, porta que não encaixa...)."""


# --------------------------------------------------------------------------------------------------
# Medidas usadas pelas peças geradas (de maps/metrics.json)
# --------------------------------------------------------------------------------------------------


def _rules() -> dict[str, float]:
    try:
        return V.rules_by_id(V.load_metrics())
    except (OSError, ValueError, KeyError):
        return {}


@dataclass(frozen=True)
class Dims:
    """Medidas das peças geradas, em células de 2 studs."""

    block: int  # células por bloco
    ih: int  # altura livre dos corredores gerados (pulo inteiro sem bater a cabeça)
    step: int  # degrau confortável (só pulo): patamares da curva
    stair: int  # degrau dos degraus gerados (metade do confortável: respiro de verdade)
    tread: int  # comprimento de cada degrau
    tower_inner: int  # largura de dentro da torre da curva
    row_gap: int  # folga entre fileiras

    @staticmethod
    def make(block: int, plan: dict[str, Any] | None = None) -> "Dims":
        plan = plan or {}
        rules = _rules()
        b = max(1, int(block))

        def up_to_block(cells: float) -> int:
            return int(math.ceil(cells / b - 1e-9)) * b

        ih = up_to_block(rules.get("ceiling_jump_free", 20.0) / BASE_CELL)
        step = max(b, int(rules.get("step_jump_comfort", 8.0) // (BASE_CELL * b)) * b)
        tread = up_to_block(max(4 * b, 16.0 / BASE_CELL))
        inner = up_to_block(max(rules.get("shaft_width_hook", 8.0) / BASE_CELL * 2, 8 * b))
        stair = max(b, int(rules.get("step_jump_comfort", 8.0) / 2 // (BASE_CELL * b)) * b)
        gap = int(plan.get("row_gap_blocks", 2)) * b
        return Dims(b, ih, step, stair, tread, inner, gap)


# --------------------------------------------------------------------------------------------------
# Peças geradas (todas em células de 2 studs, desenhadas para correr da esquerda para a direita)
# --------------------------------------------------------------------------------------------------


def _new_chunk(cid: str, name: str, w: int, h: int, doors: list[Door], rhythm: str | None = "respiro") -> Chunk:
    tm = TileMap(name=cid, cell=BASE_CELL, origin=(0, 0), width=w, height=h, source="assemble.py")
    c = Chunk(id=cid, name=name, tiles=tm, doors=doors, theme="gerado", pattern=cid.split("-")[0].lstrip("~"),
              rhythm=rhythm, difficulty=1, generated=True)
    return c


def _fill(c: Chunk, i0: int, j0: int, i1: int, j1: int, el: str | None, attrs: dict | None = None) -> None:
    """Pinta [i0, i1) x [j0, j1) (recortado na grade)."""
    t = c.tiles
    for i in range(max(0, i0), min(t.width, i1)):
        for j in range(max(0, j0), min(t.height, j1)):
            if el is None:
                t.cells.pop((i, j), None)
                t.attributes.pop((i, j), None)
            else:
                t.cells[(i, j)] = el
                if attrs:
                    t.attributes[(i, j)] = dict(attrs)


def gen_tube(cid: str, name: str, length: int, d: Dims, ih: int, closed: str = "", strip: tuple | None = None) -> Chunk:
    """Corredor reto: chão (bloco), `ih` células livres e teto sem gancho. `closed` = "L"/"R": parede no fim.
    `strip` = (elemento, i0, i1, atributos, vertical): faixa no chão (pé) ou coluna de i0 a i1."""
    b = d.block
    w, h = length, b + ih + b
    doors = [Door("a", "entry", "L", b, ih), Door("b", "exit", "R", b, ih)]
    c = _new_chunk(cid, name, w, h, doors)
    _fill(c, 0, 0, w, b, "Block")
    _fill(c, 0, b + ih, w, h, "Unhookable")
    if "L" in closed:
        _fill(c, 0, b, b, b + ih, "Unhookable")
        c.doors = [dd for dd in c.doors if dd.side != "L"]
    if "R" in closed:
        _fill(c, w - b, b, w, b + ih, "Unhookable")
        c.doors = [dd for dd in c.doors if dd.side != "R"]
    if strip:
        el, i0, i1, attrs, vertical = strip
        if vertical:
            _fill(c, i0, b, i1, b + ih, el, attrs)
        else:
            _fill(c, i0, b, i1, b + 1, el, attrs)
    return c


def gen_stairs(cid: str, rise: int, d: Dims, ih: int) -> Chunk:
    """Degraus subindo da esquerda para a direita: porta "low" (L, embaixo) e "high" (R, em cima).
    Degraus de `d.stair` (metade do confortável só com pulo), cada um com `d.tread` de comprimento."""
    b = d.block
    rise = abs(rise)
    n = max(1, math.ceil(rise / d.stair))
    w = (n + 1) * d.tread
    h = b + rise + ih + b
    doors = [Door("low", "entry", "L", b, ih), Door("high", "exit", "R", b + rise, ih)]
    c = _new_chunk(cid, f"degraus ({rise * BASE_CELL:g} studs)", w, h, doors, rhythm=None)
    for k in range(n + 1):
        f = b + min(k * d.stair, rise)  # linha do pé neste degrau
        i0, i1 = k * d.tread, (k + 1) * d.tread
        _fill(c, i0, 0, i1, f, "Block")
        _fill(c, i0, f + ih, i1, h, "Unhookable")
    return c


def gen_tower(cid: str, rise: int, d: Dims, ih: int) -> tuple[Chunk, int]:
    """Torre da curva (as duas portas do lado esquerdo): "bottom" embaixo e "top" `rise` células acima.
    Patamares em zigue-zague a cada `d.step`, cada um com metade da largura menos 1 bloco (o vão do meio).
    Devolve (peça, subida real) — a subida é arredondada para um número par de degraus."""
    b = d.block
    n = max(2, math.ceil(rise / d.step))
    if n % 2:
        n += 1
    rise = n * d.step
    inner = d.tower_inner
    w = inner + 2 * b
    h = b + rise + ih + b
    bottom_w = max(1, min(ih, 2 * d.step - b))
    doors = [Door("bottom", "entry", "L", b, bottom_w), Door("top", "exit", "L", b + rise, ih)]
    c = _new_chunk(cid, f"curva ({rise * BASE_CELL:g} studs)", w, h, doors, rhythm=None)
    _fill(c, 0, 0, w, h, "Unhookable")
    _fill(c, b, b, b + inner, b + rise + ih, None)  # dentro
    _fill(c, 0, 0, w, b, "Block")  # chão
    _fill(c, 0, b, b, b + bottom_w, None)  # porta de baixo
    _fill(c, 0, b + rise, b, b + rise + ih, None)  # porta de cima
    half = inner // 2
    ledge = max(b, half - max(1, b // 2))
    for k in range(1, n + 1):
        f = b + k * d.step
        if k % 2:  # lado de longe (direita)
            _fill(c, b + inner - ledge, f - b, b + inner, f, "Block")
        else:  # lado de perto (esquerda, o das portas)
            _fill(c, 0 if k == n else b, f - b, b + ledge, f, "Block")
    return c, rise


# --------------------------------------------------------------------------------------------------
# Plano
# --------------------------------------------------------------------------------------------------


@dataclass
class Item:
    chunk: str | None = None
    connector: str | None = None
    mirror: bool | None = None
    entry: str | None = None
    exit: str | None = None
    blocks: int | None = None  # respiro: comprimento
    rise: int | None = None  # degraus/curva: subida em blocos (negativa = desce)


@dataclass
class SectionPlan:
    id: str
    name: str
    theme: str
    items: list[Item]


def _item(raw: Any) -> Item:
    if isinstance(raw, str):
        return Item(chunk=raw)
    if not isinstance(raw, dict):
        raise AssembleError(f"item do plano inválido: {raw!r}")
    if "connector" in raw:
        kind = str(raw["connector"])
        if kind not in CONNECTORS:
            raise AssembleError(f"conector desconhecido: {kind!r} ({', '.join(CONNECTORS)})")
        return Item(connector=kind, blocks=raw.get("blocks"), rise=raw.get("rise"))
    if "chunk" not in raw:
        raise AssembleError(f"item do plano sem `chunk` nem `connector`: {raw!r}")
    return Item(chunk=str(raw["chunk"]), mirror=raw.get("mirror"), entry=raw.get("entry"), exit=raw.get("exit"))


def plan_sections(plan: dict[str, Any], library: dict[str, Chunk]) -> list[SectionPlan]:
    """Seções do plano. Sem `sections`, a lista `chunks` vira seções cortadas depois de cada trecho com
    `checkpoint_end` (ou uma seção só)."""
    if plan.get("format") not in (None, PLAN_FORMAT):
        raise AssembleError(f"formato de plano não suportado: {plan.get('format')!r} (esperado {PLAN_FORMAT})")
    out: list[SectionPlan] = []
    if plan.get("sections"):
        for n, s in enumerate(plan["sections"]):
            items = [_item(x) for x in s.get("chunks") or []]
            out.append(SectionPlan(str(s.get("id") or f"s{n + 1}"), str(s.get("name") or f"Seção {n + 1}"),
                                   str(s.get("theme") or ""), items))
    else:
        cur: list[Item] = []
        for raw in plan.get("chunks") or []:
            it = _item(raw)
            cur.append(it)
            if it.chunk and it.chunk in library and library[it.chunk].checkpoint_end:
                out.append(SectionPlan(f"s{len(out) + 1}", f"Seção {len(out) + 1}", library[it.chunk].theme, cur))
                cur = []
        if cur or not out:
            theme = next((library[i.chunk].theme for i in cur if i.chunk in library), "")
            out.append(SectionPlan(f"s{len(out) + 1}", f"Seção {len(out) + 1}", theme, cur))
    for s in out:
        for it in s.items:
            if it.chunk is not None and it.chunk not in library:
                raise AssembleError(f"seção {s.id}: trecho {it.chunk!r} não está na biblioteca")
    if not any(it.chunk for s in out for it in s.items):
        raise AssembleError("o plano não tem nenhum trecho")
    return out


# --------------------------------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------------------------------


@dataclass
class Piece:
    index: int
    kind: str  # trecho | respiro | degraus | curva | largada | checkpoint | chegada
    chunk: Chunk  # em células de 2 studs, já orientado
    x: int  # célula (0, 0) da peça na grade montada (antes de normalizar)
    y: int
    entry: Door | None
    exit: Door | None
    section: int
    label: str
    source: str

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.chunk.width, self.y + self.chunk.height)

    @property
    def generated(self) -> bool:
        return self.kind != "trecho"


@dataclass
class Assembly:
    name: str
    plan: dict[str, Any]
    block: int
    dims: Dims
    tiles: TileMap
    pieces: list[Piece]
    sections: list[SectionPlan]
    problems: list[str]

    def stages(self) -> list[tuple[str, float, float, float, float]]:
        """Uma caixa (studs) por peça, para o validador dar nome aos trechos."""
        x0, y0 = self.tiles.origin
        c = float(self.tiles.cell)
        return [(p.label, x0 + p.x * c, y0 + p.y * c, x0 + (p.x + p.chunk.width) * c, y0 + (p.y + p.chunk.height) * c) for p in self.pieces]

    def piece_origin_studs(self, p: Piece) -> tuple[float, float]:
        return (self.tiles.origin[0] + p.x * float(self.tiles.cell), self.tiles.origin[1] + p.y * float(self.tiles.cell))


def _overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class _Builder:
    def __init__(self, plan: dict[str, Any], library: dict[str, Chunk], block: int):
        self.plan = plan
        self.library = library
        self.d = Dims.make(block, plan)
        self.pieces: list[Piece] = []
        self.problems: list[str] = []
        self.flow = 1
        self.cursor: tuple[str, int, int, int] = ("R", 0, 0, self.d.ih)
        self.turn = str(plan.get("turn", "up"))
        if self.turn not in ("up", "down"):
            raise AssembleError(f"`turn` tem de ser up ou down (veio {self.turn!r})")
        self.max_w = int(math.ceil(float(plan.get("max_width", 1200)) / BASE_CELL))
        self.row_authored = 0
        self.gen_count: dict[str, int] = {}

    # ------------------------------------------------------------------ utilidades

    def gid(self, kind: str) -> str:
        self.gen_count[kind] = self.gen_count.get(kind, 0) + 1
        return f"~{kind}-{self.gen_count[kind]}"

    def flow_side(self) -> str:
        return "R" if self.flow > 0 else "L"

    def position_for(self, c: Chunk, entry: Door) -> tuple[int, int]:
        side, cx, cy, _ = self.cursor
        if side == "R":
            return cx, cy - entry.pos
        if side == "L":
            return cx - c.width, cy - entry.pos
        if side == "T":
            return cx - entry.pos, cy
        return cx - entry.pos, cy - c.height

    def cursor_after(self, p: Piece) -> tuple[str, int, int, int]:
        d = p.exit
        assert d is not None
        if d.side == "R":
            return ("R", p.x + p.chunk.width, p.y + d.pos, d.width)
        if d.side == "L":
            return ("L", p.x, p.y + d.pos, d.width)
        if d.side == "T":
            return ("T", p.x + d.pos, p.y + p.chunk.height, d.width)
        return ("B", p.x + d.pos, p.y, d.width)

    def hits(self, box: tuple[int, int, int, int]) -> list[Piece]:
        return [p for p in self.pieces if _overlaps(box, p.bbox)]

    def ih_for_cursor(self) -> int:
        b = self.d.block
        return max(self.d.ih, int(math.ceil(self.cursor[3] / b)) * b)

    def add(self, kind: str, c: Chunk, entry: Door | None, exit_: Door | None, section: int, label: str, source: str,
            at: tuple[int, int] | None = None) -> Piece:
        if at is None:
            assert entry is not None
            at = self.position_for(c, entry)
        p = Piece(len(self.pieces), kind, c, at[0], at[1], entry, exit_, section, label, source)
        clash = self.hits(p.bbox)
        if clash:
            self.problems.append(f"erro: {label} encosta em {', '.join(q.label for q in clash)} (sobreposição na montagem)")
        self.pieces.append(p)
        if exit_ is not None:
            self.cursor = self.cursor_after(p)
            if exit_.side in ("L", "R"):
                self.flow = 1 if exit_.side == "R" else -1
        return p

    def oriented(self, c: Chunk) -> Chunk:
        """Peça gerada (desenhada para a direita) no sentido atual."""
        return c if self.flow > 0 else c.mirrored_copy()

    def need_horizontal(self, what: str) -> None:
        if self.cursor[0] not in ("L", "R"):
            raise AssembleError(f"{what} precisa de uma saída lateral antes (a peça anterior sai por {self.cursor[0]})")

    # ------------------------------------------------------------------ peças geradas

    def place_start(self) -> None:
        b, ih = self.d.block, self.d.ih
        length = int(self.plan.get("start_blocks", 10)) * b
        c = gen_tube("~largada", "largada", length, self.d, ih, closed="L", strip=("StartLine", length - 2 * b, length - 2 * b + 1, None, True))
        c.tiles.spawn = (2 * b, b)
        self.add("largada", c, None, c.door("b"), 0, "Largada", "~largada", at=(0, 0))

    def place_finish(self, section: int) -> None:
        self.need_horizontal("a chegada")
        b = self.d.block
        length = int(self.plan.get("finish_blocks", 10)) * b
        c = gen_tube("~chegada", "chegada", length, self.d, self.ih_for_cursor(), closed="R",
                     strip=("FinishLine", 2 * b, length - 2 * b, None, False))
        c = self.oriented(c)
        self.add("chegada", c, c.entries()[0], None, section, "Chegada", "~chegada")

    def place_checkpoint(self, section: int, order: int, sec: SectionPlan) -> None:
        self.need_horizontal(f"o checkpoint {order}")
        b = self.d.block
        length = int(self.plan.get("checkpoint_blocks", 8)) * b
        attrs = {"Order": order, "Split": True, "Section": sec.id, "Name": sec.name}
        c = gen_tube(f"~checkpoint-{order}", f"checkpoint {order}", length, self.d, self.ih_for_cursor(),
                     strip=("Checkpoint", 2 * b, length - 2 * b, attrs, False))
        c = self.oriented(c)
        self.add("checkpoint", c, c.door("a"), c.door("b"), section, f"CP{order}", c.id)

    def place_respiro(self, section: int, blocks: int | None) -> None:
        self.need_horizontal("o respiro")
        b = self.d.block
        n = int(blocks or self.plan.get("respiro_blocks", 6))
        cid = self.gid("respiro")
        c = self.oriented(gen_tube(cid, "respiro", n * b, self.d, self.ih_for_cursor()))
        self.place_with_fixes("respiro", c, c.door("a"), c.door("b"), section, cid, cid)

    def place_stairs(self, section: int, rise_cells: int) -> None:
        self.need_horizontal("os degraus")
        cid = self.gid("degraus")
        c = gen_stairs(cid, abs(rise_cells), self.d, self.ih_for_cursor())
        if (self.flow < 0) != (rise_cells < 0):
            c = c.mirrored_copy()
        if rise_cells >= 0:
            c = c.with_roles("low", "high")
        else:
            c = c.with_roles("high", "low")
        self.add("degraus", c, c.entries()[0], c.exits()[0], section, cid, cid)

    def place_turn(self, section: int, depth_below: int, height_above: int, rise_blocks: int | None = None) -> None:
        """Curva: torre que sobe (ou desce) até a próxima fileira não encostar na atual; vira o sentido."""
        self.need_horizontal("a curva")
        _, _, cy, _ = self.cursor
        d = self.d
        if rise_blocks is not None:
            rise = abs(int(rise_blocks)) * d.block
        elif self.turn == "up":
            top = max(p.bbox[3] for p in self.pieces)
            rise = top + d.row_gap + depth_below - cy
        else:
            bottom = min(p.bbox[1] for p in self.pieces)
            rise = cy - (bottom - d.row_gap - height_above)
        cid = self.gid("curva")
        c, _real = gen_tower(cid, max(rise, 2 * d.step), d, self.ih_for_cursor())
        if self.flow < 0:
            c = c.mirrored_copy()
        c = c.with_roles("bottom", "top") if self.turn == "up" else c.with_roles("top", "bottom")
        self.add("curva", c, c.entries()[0], c.exits()[0], section, cid, cid)
        self.row_authored = 0

    # ------------------------------------------------------------------ trechos

    def candidates(self, item: Item) -> list[tuple[float, Chunk, Door, Door]]:
        base = self.library[item.chunk].scaled(BASE_CELL)  # type: ignore[index]
        variants: list[Chunk] = []
        if item.mirror is not True:
            variants.append(base)
        if item.mirror is not False:
            variants.append(base.mirrored_copy())
        need = OPPOSITE[self.cursor[0]]
        up = "T" if self.turn == "up" else "B"
        out = []
        for v in variants:
            for e in v.entries():
                if e.side != need or (item.entry and e.id != item.entry):
                    continue
                for x in v.exits():
                    if item.exit and x.id != item.exit:
                        continue
                    if x.side == self.flow_side():
                        score = 0.0
                    elif x.side == up:
                        score = 1.0
                    elif x.side in ("T", "B"):
                        score = 2.0
                    else:
                        score = 3.0  # trecho em U (volta)
                    out.append((score + (0.1 if v.mirrored else 0.0), v, e, x))
        out.sort(key=lambda q: q[0])
        return out

    def place_with_fixes(self, kind: str, c: Chunk, entry: Door, exit_: Door, section: int, label: str, source: str) -> Piece:
        for _ in range(4):
            x, y = self.position_for(c, entry)
            box = (x, y, x + c.width, y + c.height)
            clash = self.hits(box)
            if not clash or self.cursor[0] not in ("L", "R"):
                break
            mid = y + c.height / 2
            below = [p for p in clash if (p.bbox[1] + p.bbox[3]) / 2 <= mid]
            if below:
                rise = max(p.bbox[3] for p in below) - y + self.d.row_gap
            else:
                rise = -(y + c.height - min(p.bbox[1] for p in clash) + self.d.row_gap)
            self.place_stairs(section, rise)
        return self.add(kind, c, entry, exit_, section, label, source)

    def place_chunk(self, item: Item, section: int, label: str) -> None:
        cands = self.candidates(item)
        if not cands:
            c = self.library[item.chunk]  # type: ignore[index]
            sides = ", ".join(f"{d.id}:{d.side}" for d in c.entries())
            raise AssembleError(
                f"{label} ({item.chunk}): nenhuma entrada encaixa na saída anterior (lado {self.cursor[0]}); "
                f"entradas do trecho: {sides or 'nenhuma'}. Ponha um trecho de transição antes."
            )
        _, c, e, x = cands[0]
        if self.cursor[0] in ("L", "R") and self.row_authored > 0:
            px, _py = self.position_for(c, e)
            over = (self.flow > 0 and px + c.width > self.max_w) or (self.flow < 0 and px < 0)
            if over:
                depth = max(d.pos for d in c.entries())
                above = max(c.height - d.pos for d in c.entries())
                self.place_turn(section, depth, above)
                cands = self.candidates(item)
                if not cands:
                    raise AssembleError(f"{label} ({item.chunk}): depois da curva nenhuma entrada encaixa")
                _, c, e, x = cands[0]
        self.place_with_fixes("trecho", c, e, x, section, label, item.chunk or "")
        self.row_authored += 1

    # ------------------------------------------------------------------ tudo

    def build(self, sections: list[SectionPlan]) -> None:
        self.place_start()
        for s_idx, sec in enumerate(sections):
            n = 0
            for item in sec.items:
                if item.connector == "respiro":
                    self.place_respiro(s_idx, item.blocks)
                elif item.connector == "degraus":
                    self.place_stairs(s_idx, int(item.rise or 2) * self.d.block)
                elif item.connector == "curva":
                    self.place_turn(s_idx, 0, 0, item.rise)
                else:
                    n += 1
                    self.place_chunk(item, s_idx, f"S{s_idx + 1}.{n}")
            if s_idx < len(sections) - 1:
                self.place_checkpoint(s_idx, s_idx + 1, sec)
        self.place_finish(len(sections) - 1)


def plan_library(plan: dict[str, Any], plan_dir: Path | None = None) -> dict[str, Chunk]:
    """Trechos das pastas/arquivos de `plan["library"]` (texto ou lista; relativo à pasta do plano ou à raiz
    do repo). Padrão: maps/trechos."""
    libs = plan.get("library") or ["maps/trechos"]
    if isinstance(libs, str):
        libs = [libs]
    paths = []
    for lib in libs:
        p = Path(lib)
        if not p.is_absolute() and plan_dir is not None and (plan_dir / p).exists():
            p = plan_dir / p
        paths.append(p)
    return load_library(paths)


def assemble(plan: dict[str, Any], library: dict[str, Chunk] | None = None, block: int | None = None,
             plan_dir: Path | None = None) -> Assembly:
    """Monta o mapa do plano (sem validar). `library` padrão: `plan_library(plan)`."""
    if library is None:
        library = plan_library(plan, plan_dir)
    blk = int(block or plan.get("block") or default_block_cells())
    sections = plan_sections(plan, library)
    b = _Builder(plan, library, blk)
    b.build(sections)
    # trecho que fecha tema fora do fim da seção (só aviso)
    for p in b.pieces:
        if p.kind == "trecho" and p.chunk.checkpoint_end:
            nxt = next((q for q in b.pieces[p.index + 1:] if q.kind in ("trecho", "checkpoint", "chegada")), None)
            if nxt is not None and nxt.kind == "trecho":
                b.problems.append(f"aviso: {p.label} ({p.source}) fecha trecho temático, mas a seção continua depois dele")
    # grade única
    x0 = min(p.bbox[0] for p in b.pieces)
    y0 = min(p.bbox[1] for p in b.pieces)
    x1 = max(p.bbox[2] for p in b.pieces)
    y1 = max(p.bbox[3] for p in b.pieces)
    origin = plan.get("origin") or [0, 0]
    tm = TileMap(name=str(plan.get("name") or "montado"), cell=BASE_CELL, origin=(origin[0], origin[1]),
                 width=x1 - x0, height=y1 - y0, source=f"assemble.py ({len(b.pieces)} peças)")
    owner: dict[tuple[int, int], int] = {}
    conflicts = 0
    for p in b.pieces:
        p.x -= x0
        p.y -= y0
        t = p.chunk.tiles
        for (i, j), el in t.cells.items():
            key = (p.x + i, p.y + j)
            if key in owner and owner[key] != p.index:
                conflicts += 1
            owner[key] = p.index
            tm.cells[key] = el
            if el == "OneWay":
                tm.directions[key] = t.directions.get((i, j), "Up")
            if (i, j) in t.attributes:
                tm.attributes[key] = dict(t.attributes[(i, j)])
        if t.spawn is not None and p.kind == "largada":
            tm.spawn = (p.x + t.spawn[0], p.y + t.spawn[1])
    if conflicts:
        b.problems.append(f"erro: {conflicts} célula(s) com duas peças em cima (sobreposição)")
    return Assembly(tm.name, plan, blk, b.d, tm, b.pieces, sections, b.problems)


# --------------------------------------------------------------------------------------------------
# Análise do mapa montado (depois do validador)
# --------------------------------------------------------------------------------------------------


def _route_edges_by_stage(v: V.Validation, key: str) -> dict[str, list[V.Edge]]:
    r = v.results.get("route_objs", {}).get(key)
    out: dict[str, list[V.Edge]] = {}
    if r is None:
        return out
    g = v.graph
    for ei in r.edge_ids():
        e = g.edges[ei]
        out.setdefault(g.node_stage(e.src), []).append(e)
    return out


def analyze(asm: Assembly, v: V.Validation, target_minutes: float | None = None) -> dict[str, Any]:
    """Tempo por seção e total, dificuldade medida por trecho, bifurcações e a curva (alternância)."""
    target = float(target_minutes or asm.plan.get("target_minutes") or TARGET_MINUTES) * 60
    res = v.results
    routes = res.get("routes", {})
    reach = list(res.get("stage_reach", []))
    solo_ok = bool(reach) and all(reach) and routes.get("fastest") is not None
    problems = list(asm.problems)
    if not solo_ok:
        problems.insert(0, "erro: o validador não achou rota solo até a chegada (passando por todos os checkpoints na ordem)")
    groups = {k: _route_edges_by_stage(v, k) for k in ("fastest", "medium", "safest")}
    stage_runs: dict[str, dict[str, Any]] = {}
    for st in res.get("stages", []):
        stage_runs.setdefault(st["stage"], st)
    pieces = []
    for p in asm.pieces:
        f = edge_stats(groups["fastest"].get(p.label, []))
        m = edge_stats(groups["medium"].get(p.label, []))
        s = edge_stats(groups["safest"].get(p.label, []))
        run = stage_runs.get(p.label)
        disjoint = run.get("disjoint", []) if run else []
        lanes = []
        if run and p.chunk.lanes and run["entry"] != run["exit"]:
            lanes = lane_results(v, run["entry"], run["exit"], p.chunk.lanes, asm.piece_origin_studs(p))
        visited = p.label in groups["fastest"] or run is not None
        info = {
            "label": p.label,
            "kind": p.kind,
            "source": p.source,
            "section": p.section,
            "rhythm": p.chunk.rhythm,
            "target": p.chunk.difficulty if not p.generated else None,
            "measured": difficulty_level(s["min_window"], s["hard"]) if visited else None,
            "time": f["time"],
            "expected_medium": m["expected_medium"],
            "min_window": s["min_window"],
            "fast_min_window": f["min_window"],
            "kinds": f["kinds"],
            "branches": branch_count(disjoint, lanes) if visited else 0,
            "lanes": [{k: q for k, q in ln.items() if k != "edges"} for ln in lanes],
            "mirrored": p.chunk.mirrored,
            "visited": visited,
        }
        pieces.append(info)
        if not p.generated and visited and info["target"] is not None and abs(info["measured"] - info["target"]) >= 2:
            problems.append(f"aviso: {p.label} ({p.source}): dificuldade medida {info['measured']} longe da alvo {info['target']}")
        for ln in lanes:
            if not ln["ok"]:
                problems.append(f"aviso: {p.label} ({p.source}): no mapa montado, a faixa {ln['id']} não tem rota solo")
    # seções
    fast_secs = (routes.get("fastest") or {}).get("sections", [])
    med_secs = (routes.get("medium") or {}).get("sections", [])
    sections = []
    for k, sec in enumerate(asm.sections):
        own = [q for q in pieces if q["section"] == k]
        authored = [q for q in own if q["kind"] == "trecho"]
        fs = fast_secs[k] if k < len(fast_secs) else None
        ms = med_secs[k] if k < len(med_secs) else None
        info = {
            "id": sec.id,
            "name": sec.name,
            "theme": sec.theme,
            "chunks": len(authored),
            "time": fs["time"] if fs else None,
            "expected_medium": ms["expected_medium"] if ms else None,
            "min_window": min((q["min_window"] for q in own), default=V.INF),
            "bifurcations": sum(1 for q in authored if q["branches"] >= 2),
            "easy": sum(1 for q in own if q["measured"] is not None and q["measured"] <= 2 and q["kind"] in ("trecho", "respiro")),
            "checkpoint": k + 1 if k < len(asm.sections) - 1 else None,
        }
        sections.append(info)
        if authored and info["bifurcations"] == 0:
            problems.append(f"aviso: seção {sec.id} ({sec.name}) sem bifurcação (ADR 0052)")
        if authored and info["easy"] == 0:
            problems.append(f"aviso: seção {sec.id} ({sec.name}) sem trecho fácil / respiro (ADR 0052)")
    # curva de dificuldade (só trechos do plano e respiros)
    curve = [q for q in pieces if q["kind"] in ("trecho", "respiro") and q["measured"] is not None]
    streak: list[dict[str, Any]] = []
    for q in curve:
        if q["measured"] >= 4:
            streak.append(q)
            if len(streak) == 3:
                problems.append("aviso: 3+ trechos difíceis seguidos sem respiro: " + ", ".join(x["label"] for x in streak))
        else:
            streak = []
    authored_curve = [q for q in curve if q["kind"] == "trecho"]
    run = 1
    for a, b in zip(authored_curve, authored_curve[1:]):
        run = run + 1 if b["measured"] > a["measured"] else 1
        if run == 4:
            problems.append(f"aviso: a dificuldade só sobe por 4 trechos seguidos (até {b['label']}): falta alternar")
    total_fast = (routes.get("fastest") or {}).get("time")
    total_med = (routes.get("medium") or {}).get("expected_medium")
    if total_med is not None and not (0.75 * target <= total_med <= 1.25 * target):
        problems.append(f"aviso: jogador médio leva {total_med / 60:.1f} min; o alvo é ~{target / 60:.0f} min (±25%)".replace(".", ","))
    return {
        "solo_ok": solo_ok,
        "target": target,
        "total_fast": total_fast,
        "total_medium": total_med,
        "sections": sections,
        "pieces": pieces,
        "problems": problems,
        "islands": len(res.get("islands", [])),
        "traps": len(res.get("traps", [])),
        "validator_seconds": v.seconds,
        "stats": dict(v.graph.stats),
    }


# --------------------------------------------------------------------------------------------------
# Saídas
# --------------------------------------------------------------------------------------------------


def assembly_dict(asm: Assembly) -> dict[str, Any]:
    c = float(asm.tiles.cell)
    x0, y0 = asm.tiles.origin
    return {
        "format": "race-and-escape/assembly@1",
        "name": asm.name,
        "block_cells": asm.block,
        "cell": asm.tiles.cell,
        "origin": list(asm.tiles.origin),
        "size_cells": [asm.tiles.width, asm.tiles.height],
        "size_studs": [asm.tiles.width * c, asm.tiles.height * c],
        "sections": [{"id": s.id, "name": s.name, "theme": s.theme,
                      "checkpoint_order": (k + 1 if k < len(asm.sections) - 1 else None)} for k, s in enumerate(asm.sections)],
        "pieces": [
            {
                "label": p.label,
                "kind": p.kind,
                "source": p.source,
                "section": asm.sections[p.section].id,
                "mirrored": p.chunk.mirrored,
                "entry": p.entry.to_dict() if p.entry else None,
                "exit": p.exit.to_dict() if p.exit else None,
                "cells": [p.x, p.y, p.chunk.width, p.chunk.height],
                "studs": [x0 + p.x * c, y0 + p.y * c, x0 + (p.x + p.chunk.width) * c, y0 + (p.y + p.chunk.height) * c],
            }
            for p in asm.pieces
        ],
        "problems": asm.problems,
    }


def _dumps_assembly(data: dict[str, Any]) -> str:
    lines = ["{"]
    items = list(data.items())
    for n, (k, v) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        if isinstance(v, list) and v and isinstance(v[0], (dict, str)):
            lines.append(f" {json.dumps(k)}: [")
            for m, x in enumerate(v):
                lines.append(f"  {json.dumps(x, ensure_ascii=False)}{',' if m < len(v) - 1 else ''}")
            lines.append(f" ]{comma}")
        else:
            lines.append(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}{comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


SECTION_COLORS = ["#ffd166", "#06d6a0", "#ef476f", "#118ab2", "#f78c6b", "#c3a6ff", "#8ac926", "#ff9f1c"]


def assembly_overlay(asm: Assembly, v: V.Validation | None = None, an: dict[str, Any] | None = None):
    from tools.mapkit import preview as P  # noqa: PLC0415
    from tools.mapkit.report import secs  # noqa: PLC0415

    tm = asm.tiles
    ov = P.Overlay(title=f"{asm.name} — mapa montado ({len([p for p in asm.pieces if p.kind == 'trecho'])} trechos, "
                         f"{len(asm.sections)} seções)")
    by_label = {q["label"]: q for q in (an or {}).get("pieces", [])}
    first_of_section: set[int] = set()
    seen: set[int] = set()
    for p in asm.pieces:
        if p.kind == "trecho" and p.section not in seen:
            seen.add(p.section)
            first_of_section.add(p.index)
    for p in asm.pieces:
        col = SECTION_COLORS[p.section % len(SECTION_COLORS)]
        info = by_label.get(p.label)
        if p.kind == "trecho":
            label = f"{p.label} {p.source}" + (" (espelhado)" if p.chunk.mirrored else "")
            if p.index in first_of_section:
                sec = asm.sections[p.section]
                label = f"[{sec.name}] " + label
            sub = f"alvo {p.chunk.difficulty}"
            if info and info["measured"] is not None:
                sub += f" · medida {info['measured']} · {info['branches']} caminho(s) · {secs(info['time'])}"
            ov.boxes.append(P.Box(label, p.x, p.y, p.x + p.chunk.width, p.y + p.chunk.height, col, sub))
            for d in (p.entry, p.exit):
                if d is not None:
                    cells = [(p.x + i, p.y + j) for i, j in door_cells(p.chunk, d)]
                    ov.doors.append(P.DoorMark(cells, d.role))
        else:
            short = {"respiro": "respiro", "degraus": "degraus", "curva": "curva", "largada": "largada",
                     "checkpoint": p.label, "chegada": "chegada"}[p.kind]
            ov.boxes.append(P.Box(short, p.x, p.y, p.x + p.chunk.width, p.y + p.chunk.height, "#8a96a3", "", True))
    cell = float(tm.cell)
    if tm.spawn:
        sx, sy = tm.cell_center(*tm.spawn)
        ov.marks.append(P.Mark(sx, sy, "spawn", "#4a90e2"))
    if v is not None:
        ov.routes.append(P.RouteLine(route_points(v, "medium"), "#ffb347", 2.0, "4,3", "rota do jogador médio"))
        ov.routes.append(P.RouteLine(route_points(v, "fastest"), "#4fc3ff", 1.6, "", "rota mais rápida"))
    if an:
        for k, s in enumerate(an["sections"]):
            if s["checkpoint"] is None:
                continue
            cp = next((p for p in asm.pieces if p.kind == "checkpoint" and p.label == f"CP{s['checkpoint']}"), None)
            if cp is not None:
                x = tm.origin[0] + (cp.x + cp.chunk.width / 2) * cell
                y = tm.origin[1] + (cp.y + asm.dims.block + 6) * cell
                ov.marks.append(P.Mark(x, y, f"CP{s['checkpoint']} parcial {secs(s['time'])}", "#e3b341"))
        ov.notes.append(
            f"rota solo: {'sim' if an['solo_ok'] else 'NÃO'} · mais rápida {secs(an['total_fast'])} · jogador médio "
            f"{secs(an['total_medium'])} (alvo ~{secs(an['target'])})"
        )
        for q in an["problems"][:5]:
            ov.notes.append(q)
    return tm, ov


def render_report(asm: Assembly, an: dict[str, Any] | None, plan_path: str = "", chunk_reports: dict[str, Any] | None = None,
                  settings_name: str = "rápido") -> str:
    from tools.mapkit.report import br, secs, win_txt  # noqa: PLC0415

    tm = asm.tiles
    c = float(tm.cell)
    L = [
        f"# Mapa montado — {asm.name}",
        "",
        f"Gerado por `python -I -X utf8 tools/mapkit/assemble.py {plan_path}` (ADR 0052, etapa 4). **Proposta**: o mapa "
        "só entra no jogo depois de o dono aprovar (ADR 0055).",
        "",
        f"- Tamanho: {tm.width} × {tm.height} células de {c:g} studs ({br(tm.width * c, 0)} × {br(tm.height * c, 0)} studs); "
        f"bloco = {asm.block} células ({asm.block * c:g} studs).",
        f"- Peças: {sum(1 for p in asm.pieces if p.kind == 'trecho')} trechos, "
        + ", ".join(f"{n} {k}" for k, n in _count(asm.pieces).items() if k != "trecho")
        + ".",
        "- Prévia: [mapa.svg](mapa.svg) (rótulos) e [mapa.png](mapa.png); relatório completo do validador: "
        "[validacao.md](validacao.md).",
        "- Checkpoints: elemento `Checkpoint` (fora do MapBuilder por enquanto) com `Order`, `Split = true` (marca de "
        "tempo parcial), `Section` e `Name`; o plugin pula ao importar e avisa.",
        "",
    ]
    if an is None:
        L += ["(Sem validação: rode sem `--no-validate`.)", ""]
    else:
        L += [
            "## Resumo",
            "",
            f"- **Dá para terminar sozinho?** {'sim' if an['solo_ok'] else '**não** (ver problemas)'} — o validador joga com 1 "
            f"jogador ({settings_name}, {an['validator_seconds']:.0f} s, {an['stats'].get('sims', 0)} simulações).",
            f"- **Tempo:** mais rápida {secs(an['total_fast'])}; jogador médio {secs(an['total_medium'])} "
            f"(alvo ~{secs(an['target'])}).",
            f"- Ilhas (plataformas não alcançadas): {an['islands']}; armadilhas (não levam à chegada): {an['traps']}.",
            "",
            "## Seções (tempo parcial em cada checkpoint)",
            "",
            "| Seção | Tema | Trechos | Rápida | Jogador médio | % do total | Menor janela | Bifurcações | Fáceis | Fim |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        tot = an["total_medium"] or 0
        for s in an["sections"]:
            pct = f"{round(100 * s['expected_medium'] / tot)}%" if tot and s["expected_medium"] else "—"
            end = f"CP{s['checkpoint']}" if s["checkpoint"] else "chegada"
            L.append(
                f"| {s['id']} {s['name']} | {s['theme'] or '—'} | {s['chunks']} | {secs(s['time'])} | {secs(s['expected_medium'])} | "
                f"{pct} | {win_txt(s['min_window'])} | {s['bifurcations']} | {s['easy']} | {end} |"
            )
        L += [
            "",
            "## Curva de dificuldade (por peça, na ordem da corrida)",
            "",
            "Medida = menor janela da rota mais segura dentro da peça (1 = sem precisão, 2 ≥ 0,4 s, 3 = 0,2–0,4 s, "
            "4 = 0,1–0,2 s, 5 < 0,1 s; +1 com 3+ manobras < 0,2 s). Caminhos = faixas que passam sozinhas ou caminhos "
            "por plataformas diferentes (piso).",
            "",
            "| Peça | Trecho | Ritmo | Alvo | Medida | Curva | Rápida | Menor janela | Caminhos | Manobras (rápida) |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for q in an["pieces"]:
            if q["kind"] not in ("trecho", "respiro", "curva", "degraus"):
                continue
            bar = "█" * (q["measured"] or 0)
            kinds = ", ".join(f"{k} ×{n}" for k, n in sorted(q["kinds"].items())) or "—"
            src = q["source"] + (" ↔" if q["mirrored"] else "")
            L.append(
                f"| {q['label']} | {src} | {q['rhythm'] or '—'} | {q['target'] if q['target'] is not None else '—'} | "
                f"{q['measured'] if q['measured'] is not None else '—'} | {bar} | {secs(q['time'])} | {win_txt(q['min_window'])} | "
                f"{q['branches']} | {kinds} |"
            )
        lane_rows = [(q, ln) for q in an["pieces"] for ln in q["lanes"]]
        if lane_rows:
            L += ["", "## Bifurcações declaradas (faixas) no mapa montado", "",
                  "| Peça | Faixa | Tipo | Passa? | Tempo | Chance sem erro | Menor janela |", "|---|---|---|---|---|---|---|"]
            for q, ln in lane_rows:
                if ln["ok"]:
                    L.append(f"| {q['label']} | {ln['id']} {ln['name']} | {ln['kind']} | sim | {secs(ln['time'])} | "
                             f"{ln['p_clean']:.0%} | {win_txt(ln['min_window'])} |")
                else:
                    L.append(f"| {q['label']} | {ln['id']} {ln['name']} | {ln['kind']} | **não** | — | — | — |")
        L += ["", "## Problemas", ""]
        L += [f"- {q}" for q in an["problems"]] or ["- nenhum"]
    if chunk_reports:
        L += ["", "## Cada trecho sozinho (`--chunks`)", "",
              "| Trecho | Rota solo | Rápida | Jogador médio | Alvo / medida | Caminhos | Problemas |", "|---|---|---|---|---|---|---|"]
        for cid, r in chunk_reports.items():
            f = r.routes.get("fastest") or {}
            m = r.routes.get("medium") or {}
            L.append(f"| {cid} | {'sim' if r.ok else '**não**'} | {secs(f.get('time'))} | {secs(m.get('expected_medium'))} | "
                     f"{r.target} / {r.measured if r.measured is not None else '—'} | {r.paths} | {'; '.join(r.problems) or '—'} |")
    L += ["", "## Peças", "", "| Peça | Tipo | Origem | Seção | Células (x, y, l, a) | Entrada | Saída |", "|---|---|---|---|---|---|---|"]
    for p in asm.pieces:
        ent = f"{p.entry.id} {p.entry.side}" if p.entry else "—"
        ex = f"{p.exit.id} {p.exit.side}" if p.exit else "—"
        src = p.source + (" (espelhado)" if p.chunk.mirrored and p.kind == "trecho" else "")
        L.append(f"| {p.label} | {p.kind} | {src} | {asm.sections[p.section].id} | {p.x}, {p.y}, {p.chunk.width}, {p.chunk.height} | {ent} | {ex} |")
    if an is None and asm.problems:
        L += ["", "## Problemas da montagem", ""] + [f"- {q}" for q in asm.problems]
    L.append("")
    return "\n".join(L)


def _count(pieces: list[Piece]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in pieces:
        out[p.kind] = out.get(p.kind, 0) + 1
    return out


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "montado"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Monta um mapa a partir de trechos e o valida (ADR 0052, etapa 4).")
    ap.add_argument("plan", help="plano (race-and-escape/plan@1)")
    ap.add_argument("--out", help="pasta de saída (padrão: maps/<nome do plano>/)")
    ap.add_argument("--full", action="store_true", help="validador completo (mais manobras, mais lento)")
    ap.add_argument("--no-validate", action="store_true", help="só monta e desenha")
    ap.add_argument("--no-refine", action="store_true", help="não refina as janelas das rotas")
    ap.add_argument("--chunks", action="store_true", help="valida também cada trecho sozinho")
    ap.add_argument("--block", type=int, help="células por bloco (padrão: plano, maps/scale.json ou 2)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1), help="processos (padrão: CPUs - 1)")
    args = ap.parse_args(argv)

    from tools.mapkit import preview, report  # noqa: PLC0415
    from tools.mapkit.chunks import validate_many  # noqa: PLC0415

    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_text(encoding="utf8"))
    t0 = time.time()
    try:
        library = plan_library(plan, plan_path.resolve().parent)
        asm = assemble(plan, library, block=args.block)
    except (AssembleError, ChunkError) as exc:
        print(f"erro: {exc}")
        return 2
    out = Path(args.out) if args.out else REPO_ROOT / "maps" / slug(asm.name)
    out.mkdir(parents=True, exist_ok=True)
    tm = asm.tiles
    print(f"Montado: {tm.width} × {tm.height} células, {len(asm.pieces)} peças, bloco {asm.block} células "
          f"({time.time() - t0:.2f} s)")
    for q in asm.problems:
        print("  " + q)
    tm.save(out / "tiles.json")
    (out / "montagem.json").write_text(_dumps_assembly(assembly_dict(asm)), encoding="utf8", newline="\n")
    v = None
    an = None
    if not args.no_validate:
        settings = V.Settings() if args.full else V.Settings.quick()
        print(f"Validando com {args.jobs} processo(s){'' if args.full else ' [rápido]'}...")
        v = V.validate(tm, settings, jobs=args.jobs, progress=print, refine=not args.no_refine, stages=asm.stages())
        an = analyze(asm, v)
        md, svg = report.render(v, svg_name="validacao.svg", tiles_path=(out / "tiles.json").as_posix())
        (out / "validacao.md").write_text(md, encoding="utf8", newline="\n")
        (out / "validacao.svg").write_text(svg, encoding="utf8", newline="\n")
    chunk_reports = None
    if args.chunks:
        ids = list(dict.fromkeys(p.source for p in asm.pieces if p.kind == "trecho"))
        chunks = [library[cid] for cid in ids]
        chunk_reports = {r.id: r for r in validate_many(chunks, refine=not args.no_refine, jobs=args.jobs, progress=print)}
    ptm, ov = assembly_overlay(asm, v, an)
    (out / "mapa.svg").write_text(preview.render_svg(ptm, ov), encoding="utf8", newline="\n")
    preview.render_png(ptm, ov, out / "mapa.png")
    (out / "relatorio.md").write_text(render_report(asm, an, plan_path.as_posix(), chunk_reports, "completo" if args.full else "rápido"),
                                      encoding="utf8", newline="\n")
    if an is not None:
        print(f"Rota solo: {'sim' if an['solo_ok'] else 'NÃO'} · mais rápida {an['total_fast'] or 0:.1f} s · "
              f"jogador médio {an['total_medium'] or 0:.1f} s (alvo {an['target']:.0f} s)")
        for q in an["problems"]:
            print("  " + q)
    print(f"Gravado em {out}: tiles.json, montagem.json, relatorio.md, mapa.svg, mapa.png"
          + (", validacao.md/.svg" if v is not None else "") + f" ({time.time() - t0:.0f} s)")
    return 0 if (an is None or an["solo_ok"]) and not any(q.startswith("erro") for q in asm.problems) else 1


if __name__ == "__main__":
    from tools.mapkit.assemble import main as _main

    sys.exit(_main())
