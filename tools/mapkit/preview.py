"""Prévias (SVG e PNG) de trechos e do mapa montado (ADR 0052, etapa 4). Só biblioteca padrão.

Cores dos elementos lidas de `src/shared/MapElements.luau` (as mesmas do MapBuilder); se o arquivo não
for achado, usa a cópia abaixo. O PNG é desenhado à mão (zlib + struct): sem texto, só as cores, as
caixas dos trechos, as portas e a rota mais rápida. O SVG tem os rótulos.

    from tools.mapkit import preview
    svg = preview.chunk_svg(chunk, report)        # report = ChunkReport (opcional: desenha a rota)
    preview.chunk_png(chunk, report, "x.png")
    svg = preview.render_svg(tm, overlay)         # qualquer TileMap + Overlay
"""

from __future__ import annotations

import html
import re
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.mapkit.luau_config import REPO_ROOT
from tools.mapkit.tiles import TileMap

ELEMENTS_PATH = REPO_ROOT / "src" / "shared" / "MapElements.luau"
BACKGROUND = "#1c1f26"

# cópia de MapElements.luau (cor, quadriculado, transparência) para quando o arquivo não existir
FALLBACK: dict[str, tuple[str, str | None, float]] = {
    "Block": ("#96976c", None, 0.0),
    "Unhookable": ("#67809a", "#53687c", 0.0),
    "HookThrough": ("#2d2d34", None, 0.2),
    "Freeze": ("#464b5a", None, 0.3),
    "Unfreeze": ("#ffd746", None, 0.3),
    "OneWay": ("#aec2d3", None, 0.3),
    "Kill": ("#b74a54", None, 0.0),
    "HookOnce": ("#71a377", None, 0.0),
    "StartLine": ("#f0f0f5", "#3c6ec8", 0.0),
    "FinishLine": ("#f0f0f5", "#19191e", 0.0),
    "SoloStart": ("#969ba8", None, 0.3),
    "SoloEnd": ("#cdd0d8", None, 0.3),
}
# não são elementos do MapBuilder (mapas antigos / montador)
EXTRA: dict[str, tuple[str, str | None, float]] = {
    "Checkpoint": ("#e3b341", "#a87d16", 0.0),
    "RaceStart": ("#4a90e2", None, 0.0),
}

_COLORS: dict[str, tuple[str, str | None, float]] | None = None


def _hex(r: str, g: str, b: str) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(float(r)), int(float(g)), int(float(b)))


def element_colors() -> dict[str, tuple[str, str | None, float]]:
    """id -> (cor, cor do quadriculado ou None, transparência), lido do MapElements.luau."""
    global _COLORS
    if _COLORS is not None:
        return _COLORS
    out = dict(FALLBACK)
    if ELEMENTS_PATH.exists():
        text = ELEMENTS_PATH.read_text(encoding="utf8")
        rgb = r"Color3\.fromRGB\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"
        blocks = re.split(r'\n\s*id\s*=\s*"', text)
        for blk in blocks[1:]:
            name = blk.split('"', 1)[0]
            body = blk.split("\n\t},", 1)[0]
            m = re.search(r"\bcolor\s*=\s*" + rgb, body)
            if not m:
                continue
            chk = re.search(r"\bchecker\s*=\s*" + rgb, body)
            tr = re.search(r"\btransparency\s*=\s*([\d.]+)", body)
            out[name] = (_hex(*m.groups()), _hex(*chk.groups()) if chk else None, float(tr.group(1)) if tr else 0.0)
    out.update(EXTRA)
    _COLORS = out
    return out


@dataclass
class Box:
    label: str
    i0: int
    j0: int
    i1: int  # exclusivo
    j1: int  # exclusivo
    color: str = "#9fb3c8"
    sublabel: str = ""
    dashed: bool = False


@dataclass
class DoorMark:
    cells: list[tuple[int, int]]
    role: str  # entry | exit
    label: str = ""


@dataclass
class RouteLine:
    points: list[tuple[float, float]]  # studs (root)
    color: str = "#4fc3ff"
    width: float = 2.0
    dash: str = ""
    label: str = ""


@dataclass
class Mark:
    x: float  # studs
    y: float
    text: str
    color: str = "#ffd84a"


@dataclass
class Overlay:
    title: str = ""
    boxes: list[Box] = field(default_factory=list)
    doors: list[DoorMark] = field(default_factory=list)
    routes: list[RouteLine] = field(default_factory=list)
    marks: list[Mark] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # linhas de texto embaixo


def _px_svg(tm: TileMap, target: float = 1400.0) -> float:
    return max(1.5, min(12.0, target / max(1, tm.width)))


# --------------------------------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------------------------------


def render_svg(tm: TileMap, ov: Overlay | None = None, px: float | None = None) -> str:
    ov = ov or Overlay()
    px = px or _px_svg(tm)
    colors = element_colors()
    cell = float(tm.cell)
    x0, y0 = tm.origin
    W = tm.width * px
    top = 30 if ov.title else 6
    H = tm.height * px
    legend = 34 + 18 * len(ov.notes)
    total_h = top + H + legend

    def X(x: float) -> float:
        return round((x - x0) / cell * px, 1)

    def Y(y: float) -> float:
        return round(top + H - (y - y0) / cell * px, 1)

    def CX(i: float) -> float:
        return round(i * px, 1)

    def CY(j: float) -> float:
        return round(top + H - j * px, 1)

    esc = html.escape
    o: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(W)}" height="{round(total_h)}" '
        f'viewBox="0 0 {round(W)} {round(total_h)}" font-family="sans-serif">',
        "<defs>",
    ]
    for el, (c, chk, _tr) in colors.items():
        if chk:
            s = max(px, 2)
            o.append(
                f'<pattern id="chk-{el}" width="{2 * s}" height="{2 * s}" patternUnits="userSpaceOnUse">'
                f'<rect width="{2 * s}" height="{2 * s}" fill="{c}"/><rect width="{s}" height="{s}" fill="{chk}"/>'
                f'<rect x="{s}" y="{s}" width="{s}" height="{s}" fill="{chk}"/></pattern>'
            )
    o.append("</defs>")
    o.append(f'<rect width="{round(W)}" height="{round(total_h)}" fill="{BACKGROUND}"/>')
    if ov.title:
        o.append(f'<text x="8" y="20" fill="#f0f0f0" font-size="15" font-weight="bold">{esc(ov.title)}</text>')
    for rc in tm.rects():
        c, chk, tr = colors.get(rc.element, ("#888888", None, 0.0))
        fill = f"url(#chk-{rc.element})" if chk else c
        o.append(
            f'<rect x="{CX(rc.i)}" y="{CY(rc.j + rc.h)}" width="{round(rc.w * px, 1)}" height="{round(rc.h * px, 1)}" '
            f'fill="{fill}" opacity="{round(1 - tr * 0.6, 2)}"/>'
        )
        if rc.element == "OneWay" and rc.direction:
            cx, cy = CX(rc.i + rc.w / 2), CY(rc.j + rc.h / 2)
            arrow = {"Up": "▲", "Down": "▼", "Left": "◀", "Right": "▶"}[rc.direction]
            o.append(f'<text x="{cx}" y="{cy + 4}" fill="#203040" font-size="{max(8, round(px * 2))}" text-anchor="middle">{arrow}</text>')
    for b in ov.boxes:
        dash = ' stroke-dasharray="6,4"' if b.dashed else ""
        o.append(
            f'<rect x="{CX(b.i0)}" y="{CY(b.j1)}" width="{round((b.i1 - b.i0) * px, 1)}" height="{round((b.j1 - b.j0) * px, 1)}" '
            f'fill="none" stroke="{b.color}" stroke-width="1.5"{dash}/>'
        )
        if b.label:
            o.append(f'<text x="{CX(b.i0) + 4}" y="{CY(b.j1) + 14}" fill="{b.color}" font-size="12" font-weight="bold">{esc(b.label)}</text>')
        if b.sublabel:
            o.append(f'<text x="{CX(b.i0) + 4}" y="{CY(b.j1) + 28}" fill="#dfe6ee" font-size="11">{esc(b.sublabel)}</text>')
    for r in ov.routes:
        if len(r.points) < 2:
            continue
        dash = f' stroke-dasharray="{r.dash}"' if r.dash else ""
        pts = " ".join(f"{X(x)},{Y(y - 3)}" for x, y in r.points)
        o.append(f'<polyline fill="none" stroke="{r.color}" stroke-width="{r.width}" opacity="0.95"{dash} points="{pts}"/>')
    for d in ov.doors:
        col = "#3ddc84" if d.role == "entry" else "#ff8c42"
        for i, j in d.cells:
            o.append(f'<rect x="{CX(i)}" y="{CY(j + 1)}" width="{round(px, 1)}" height="{round(px, 1)}" fill="{col}" opacity="0.75"/>')
        if d.label and d.cells:
            i, j = d.cells[len(d.cells) // 2]
            o.append(f'<text x="{CX(i) + px + 2}" y="{CY(j)}" fill="{col}" font-size="11" font-weight="bold">{esc(d.label)}</text>')
    for m in ov.marks:
        o.append(f'<circle cx="{X(m.x)}" cy="{Y(m.y)}" r="5" fill="{m.color}" stroke="#ffffff" stroke-width="1"/>')
        o.append(f'<text x="{X(m.x) + 7}" y="{Y(m.y) - 6}" fill="{m.color}" font-size="12" font-weight="bold">{esc(m.text)}</text>')
    # legenda
    ly = top + H + 18
    items = [("#3ddc84", "entrada"), ("#ff8c42", "saída")] + [(r.color, r.label) for r in ov.routes if r.label]
    x = 8.0
    for col, text in items:
        o.append(f'<rect x="{x}" y="{ly - 8}" width="14" height="8" fill="{col}"/>')
        o.append(f'<text x="{x + 18}" y="{ly}" fill="#e8e8e8" font-size="12">{esc(text)}</text>')
        x += 26 + 7 * len(text)
    for n, line in enumerate(ov.notes):
        o.append(f'<text x="8" y="{ly + 18 * (n + 1)}" fill="#cfd6de" font-size="12">{esc(line)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# --------------------------------------------------------------------------------------------------
# PNG (sem dependências)
# --------------------------------------------------------------------------------------------------


def _rgb(hexcol: str) -> tuple[int, int, int]:
    h = hexcol.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[k] * (1 - t) + b[k] * t) for k in range(3))  # type: ignore[return-value]


def write_png(path: str | Path, width: int, height: int, pixels: bytearray) -> None:
    """Grava RGB 8 bits (linhas de cima para baixo)."""
    stride = width * 3
    raw = b"".join(b"\x00" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def render_png(tm: TileMap, ov: Overlay | None, path: str | Path, px: int | None = None) -> tuple[int, int]:
    ov = ov or Overlay()
    px = px or max(1, min(10, 3000 // max(1, tm.width)))
    colors = element_colors()
    W, H = tm.width * px, tm.height * px
    bg = _rgb(BACKGROUND)
    buf = bytearray(bytes(bg) * (W * H))
    cell = float(tm.cell)
    x0, y0 = tm.origin

    def put(x: int, y: int, c: tuple[int, int, int]) -> None:
        if 0 <= x < W and 0 <= y < H:
            k = (y * W + x) * 3
            buf[k:k + 3] = bytes(c)

    def fill_cell(i: int, j: int, c: tuple[int, int, int]) -> None:
        y_top = (tm.height - 1 - j) * px
        row = bytes(c) * px
        for dy in range(px):
            k = ((y_top + dy) * W + i * px) * 3
            buf[k:k + 3 * px] = row

    cache: dict[tuple[str, int], tuple[int, int, int]] = {}
    for (i, j), el in tm.cells.items():
        c, chk, tr = colors.get(el, ("#888888", None, 0.0))
        alt = 1 if (chk and (i + j) % 2) else 0
        key = (el, alt)
        if key not in cache:
            base = _rgb(chk if alt else c)
            cache[key] = _blend(base, bg, tr * 0.6)
        fill_cell(i, j, cache[key])

    def line(xa: float, ya: float, xb: float, yb: float, c: tuple[int, int, int], thick: int = 1) -> None:
        n = int(max(abs(xb - xa), abs(yb - ya))) + 1
        for s in range(n + 1):
            t = s / n
            x, y = round(xa + (xb - xa) * t), round(ya + (yb - ya) * t)
            for dx in range(thick):
                for dy in range(thick):
                    put(x + dx, y + dy, c)

    def SX(x: float) -> float:
        return (x - x0) / cell * px

    def SY(y: float) -> float:
        return H - (y - y0) / cell * px

    for b in ov.boxes:
        c = _rgb(b.color)
        xa, xb = b.i0 * px, b.i1 * px - 1
        ya, yb = H - b.j1 * px, H - b.j0 * px - 1
        step = 3 if b.dashed else 1
        for x in range(xa, xb + 1, step):
            put(x, ya, c)
            put(x, yb, c)
        for y in range(ya, yb + 1, step):
            put(xa, y, c)
            put(xb, y, c)
    for r in ov.routes:
        c = _rgb(r.color)
        for (xa, ya), (xb, yb) in zip(r.points, r.points[1:]):
            line(SX(xa), SY(ya - 3), SX(xb), SY(yb - 3), c, 2 if px >= 2 else 1)
    for d in ov.doors:
        c = _rgb("#3ddc84" if d.role == "entry" else "#ff8c42")
        for i, j in d.cells:
            if 0 <= i < tm.width and 0 <= j < tm.height:
                fill_cell(i, j, c)
    for m in ov.marks:
        c = _rgb(m.color)
        cx, cy = round(SX(m.x)), round(SY(m.y))
        rad = max(2, px * 2)
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if dx * dx + dy * dy <= rad * rad:
                    put(cx + dx, cy + dy, c)
    write_png(path, W, H, buf)
    return W, H


# --------------------------------------------------------------------------------------------------
# Trecho
# --------------------------------------------------------------------------------------------------


def _chunk_tiles(c: Any) -> tuple[Any, TileMap]:
    from tools.mapkit.chunks import BASE_CELL  # noqa: PLC0415

    sc = c.scaled(BASE_CELL)
    t = sc.tiles
    tm = TileMap(name=t.name, cell=t.cell, origin=(0, 0), width=t.width, height=t.height, collide=dict(t.collide))
    tm.cells = dict(t.cells)
    tm.directions = dict(t.directions)
    tm.attributes = dict(t.attributes)
    return sc, tm


def chunk_overlay(c: Any, report: Any = None) -> tuple[TileMap, Overlay]:
    from tools.mapkit.chunks import SIDE_PT, door_cells  # noqa: PLC0415

    sc, tm = _chunk_tiles(c)
    title = f"{c.id} — {c.name}"
    ov = Overlay(title=title)
    for d in sc.doors:
        word = "entrada" if d.role == "entry" else "saída"
        ov.doors.append(DoorMark(door_cells(sc, d), d.role, f"{word} {d.id} ({SIDE_PT[d.side]})"))
    lane_col = {"rapida": "#ff6b6b", "segura": "#7bd88f", "outra": "#c8a2ff"}
    lane_info = {ln["id"]: ln for ln in (report.lanes if report else [])}
    for ln in sc.lanes:
        i0, j0, i1, j1 = ln.area
        info = lane_info.get(ln.id)
        sub = ""
        if info is not None:
            sub = f"{info['time']:.2f} s · chance sem erro {info['p_clean']:.0%}" if info["ok"] else "sem rota solo"
        ov.boxes.append(Box(f"faixa {ln.id}: {ln.name or ln.kind}", i0, j0, i1 + 1, j1 + 1, lane_col.get(ln.kind, "#c8a2ff"), sub, True))
    notes = [
        f"tema {c.theme or '—'} · padrão {c.pattern or '—'} · ritmo {c.rhythm or '—'} · {c.width} × {c.height} blocos de {c.cell:g} studs"
        f" · exige {', '.join(c.required) or '—'}"
    ]
    if report is not None:
        if report.ok:
            f = report.routes.get("fastest") or {}
            m = report.routes.get("medium") or {}
            ov.routes.append(RouteLine(list(report.route), "#4fc3ff", 2.0, label="rota mais rápida"))
            notes.append(
                f"rota solo ok · rápida {f.get('time', 0):.1f} s · jogador médio {m.get('expected_medium', 0):.1f} s · "
                f"dificuldade alvo {report.target} / medida {report.measured} · {report.paths} caminho(s)"
            )
        else:
            notes.append("SEM ROTA SOLO da entrada até a saída")
        notes.extend(report.problems[:4])
    else:
        notes.append(f"dificuldade alvo {c.difficulty} (não validado)")
    ov.notes = notes
    return tm, ov


def chunk_svg(c: Any, report: Any = None) -> str:
    tm, ov = chunk_overlay(c, report)
    return render_svg(tm, ov, px=max(4.0, min(14.0, 900 / max(1, tm.width))))


def chunk_png(c: Any, report: Any, path: str | Path) -> tuple[int, int]:
    tm, ov = chunk_overlay(c, report)
    return render_png(tm, ov, path, px=max(2, min(10, 900 // max(1, tm.width))))


__all__ = [
    "Box",
    "DoorMark",
    "Mark",
    "Overlay",
    "RouteLine",
    "chunk_png",
    "chunk_svg",
    "element_colors",
    "render_png",
    "render_svg",
    "write_png",
]
