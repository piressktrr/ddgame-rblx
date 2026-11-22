"""Ferramentas de desenho dos trechos de proposta (grade em blocos + metadados do chunk@1)."""

from __future__ import annotations

from typing import Any, Callable

from tools.mapkit.chunks import CHUNK_FORMAT

LEGEND = {
    ".": None,
    "#": "Block",
    "x": "Unhookable",
    "h": "HookThrough",
    "f": "Freeze",
    "u": "Unfreeze",
    "o": "OneWay",
    "k": "Kill",
    "g": "HookOnce",
    "s": "SoloStart",
    "e": "SoloEnd",
}
SOLID = set("#xhgk")
DOOR = 5  # blocos de abertura das portas laterais (20 studs = ceiling_jump_free)


class G:
    """Grade de um trecho em blocos. (i, j): i = coluna da esquerda, j = linha de baixo para cima."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.c = [["." for _ in range(w)] for _ in range(h)]
        self.dirs: dict[tuple[int, int], str] = {}
        self.doors: list[dict[str, Any]] = []

    def box(self, i0: int, j0: int, i1: int, j1: int, ch: str) -> "G":
        for j in range(min(j0, j1), max(j0, j1) + 1):
            for i in range(min(i0, i1), max(i0, i1) + 1):
                if 0 <= i < self.w and 0 <= j < self.h:
                    self.c[j][i] = ch
        return self

    def set(self, i: int, j: int, ch: str) -> "G":
        return self.box(i, j, i, j, ch)

    def get(self, i: int, j: int) -> str:
        return self.c[j][i]

    def oneway(self, i0: int, j0: int, i1: int, j1: int, direction: str) -> "G":
        self.box(i0, j0, i1, j1, "o")
        for j in range(min(j0, j1), max(j0, j1) + 1):
            for i in range(min(i0, i1), max(i0, i1) + 1):
                self.dirs[(i, j)] = direction
        return self

    def shell(self) -> "G":
        self.box(0, 0, self.w - 1, 0, "x")
        self.box(0, self.h - 1, self.w - 1, self.h - 1, "x")
        self.box(0, 0, 0, self.h - 1, "x")
        self.box(self.w - 1, 0, self.w - 1, self.h - 1, "x")
        return self

    def ground(self, i0: int, i1: int, feet: int, ch: str = "x") -> "G":
        """Terreno sólido de j = 0 até feet - 1 (os pés ficam na linha `feet`)."""
        return self.box(i0, 0, i1, feet - 1, ch)

    def door(self, side: str, feet: int, role: str, did: str, width: int = DOOR) -> "G":
        col = 0 if side == "L" else self.w - 1
        self.box(col, feet, col, feet + width - 1, ".")
        if self.get(col, feet - 1) not in SOLID:
            self.set(col, feet - 1, "x")
        self.doors.append({"id": did, "role": role, "side": side, "pos": feet, "width": width})
        return self

    def rows(self) -> list[str]:
        return ["".join(self.c[j]) for j in range(self.h - 1, -1, -1)]

    def ascii(self) -> str:
        out = []
        for j in range(self.h - 1, -1, -1):
            out.append(f"{j:3d} " + "".join(self.c[j]))
        ruler = "".join(str(i % 10) for i in range(self.w))
        out.append("    " + ruler)
        return "\n".join(out)


CHUNKS: dict[str, Callable[[], dict[str, Any]]] = {}
ASCII: dict[str, str] = {}


def chunk(fn: Callable[[], dict[str, Any]]) -> Callable[[], dict[str, Any]]:
    CHUNKS[fn.__name__.replace("_", "-")] = fn
    return fn


def meta(
    cid: str,
    g: G,
    *,
    name: str,
    theme: str,
    pattern: str,
    rhythm: str,
    difficulty: int,
    required: list[str],
    optional: list[str],
    lanes: list[dict[str, Any]] | None = None,
    notes: str,
    checkpoint_end: bool = False,
) -> dict[str, Any]:
    tiles: dict[str, Any] = {
        "cell": 4,
        "origin": [0, 0],
        "width": g.w,
        "height": g.h,
        "legend": dict(LEGEND),
        "rows": g.rows(),
    }
    if g.dirs:
        tiles["directions"] = {f"{i},{j}": d for (i, j), d in sorted(g.dirs.items(), key=lambda kv: (kv[0][1], kv[0][0]))}
    ASCII[cid] = g.ascii()
    return {
        "format": CHUNK_FORMAT,
        "id": cid,
        "name": name,
        "theme": theme,
        "pattern": pattern,
        "rhythm": rhythm,
        "difficulty": difficulty,
        "solo": True,
        "checkpoint_end": checkpoint_end,
        "mechanics": {"required": required, "optional": optional},
        "doors": g.doors,
        "lanes": lanes or [],
        "notes": notes,
        "tiles": tiles,
    }


def lane(lid: str, name: str, kind: str, area: tuple[int, int, int, int]) -> dict[str, Any]:
    return {"id": lid, "name": name, "kind": kind, "area": list(area)}
