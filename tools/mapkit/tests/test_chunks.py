"""Testes da biblioteca de trechos (tools/mapkit/chunks.py) com os exemplos mínimos de maps/trechos.

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.mapkit.chunks import (
    CHUNK_FORMAT,
    LIBRARY_DIR,
    Chunk,
    ChunkError,
    check_chunk,
    default_block_cells,
    difficulty_level,
    fit,
    isolated_map,
    load_library,
    validate_chunk,
)
from tools.mapkit.validate import Settings

QUICK = Settings.quick()


def make_chunk(rows: list[str], doors: list[dict], cid: str = "t", cell: int = 4, **meta) -> Chunk:
    data = {
        "format": CHUNK_FORMAT,
        "id": cid,
        "name": cid,
        "difficulty": meta.pop("difficulty", 1),
        "doors": doors,
        "tiles": {"cell": cell, "rows": rows},
    }
    data.update(meta)
    return Chunk.from_dict(data)


def door(did: str, role: str, side: str, pos: int, width: int) -> dict:
    return {"id": did, "role": role, "side": side, "pos": pos, "width": width}


FLAT = [
    "xxxxxxxxxx",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "##########",
]
FLAT_DOORS = [door("in", "entry", "L", 1, 4), door("out", "exit", "R", 1, 4)]

_CACHE: dict[str, object] = {}


def report(name: str):
    if name not in _CACHE:
        lib = load_library()
        _CACHE[name] = validate_chunk(lib[name], settings=QUICK, refine=False)
    return _CACHE[name]


class FormatTests(unittest.TestCase):
    def test_examples_load_and_pass_static_check(self):
        lib = load_library()
        for cid in ("ex-corredor", "ex-vao-gancho", "ex-bifurcacao"):
            self.assertIn(cid, lib)
            self.assertEqual(check_chunk(lib[cid]), [], cid)
            self.assertTrue(lib[cid].solo)

    def test_round_trip_is_stable(self):
        for path in sorted(LIBRARY_DIR.glob("ex-*.json")):
            text = path.read_text(encoding="utf8")
            self.assertEqual(Chunk.load(path).dumps(), text, path.name)

    def test_scaled_doubles_cells_doors_and_lanes(self):
        c = load_library()["ex-bifurcacao"]
        s = c.scaled(2)
        self.assertEqual((s.width, s.height, s.cell), (c.width * 2, c.height * 2, 2.0))
        self.assertEqual((s.door("in").pos, s.door("in").width), (c.door("in").pos * 2, c.door("in").width * 2))
        self.assertEqual(s.tiles.get(0, 0), c.tiles.get(0, 0))
        self.assertEqual(s.lanes[0].area[2], c.lanes[0].area[2] * 2 + 1)

    def test_mirror_swaps_sides_and_one_way(self):
        c = make_chunk(["x....", "..o..", "#####"], FLAT_DOORS[:1] + [door("up", "exit", "T", 1, 2)], directions={})
        c.tiles.directions[(2, 1)] = "Left"
        m = c.mirrored_copy()
        self.assertEqual(m.door("in").side, "R")
        self.assertEqual(m.door("up").pos, c.width - 1 - 2)
        self.assertEqual(m.tiles.direction(2, 1), "Right")
        self.assertEqual(m.tiles.get(c.width - 1, 2), "Unhookable")
        self.assertTrue(m.mirrored)

    def test_bad_format_raises(self):
        with self.assertRaises(ChunkError):
            Chunk.from_dict({"format": "outro", "id": "x"})
        with self.assertRaises(ChunkError):
            make_chunk(FLAT, [door("in", "entry", "Z", 1, 4)])

    def test_default_block_reads_scale_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "scale.json"
            self.assertEqual(default_block_cells(p), 2)  # sem arquivo
            p.write_text(json.dumps({"recommended": {"block_studs": 6}}), encoding="utf8")
            self.assertEqual(default_block_cells(p), 3)
            p.write_text(json.dumps({"block_cells": 4}), encoding="utf8")
            self.assertEqual(default_block_cells(p), 4)


class StaticCheckTests(unittest.TestCase):
    def test_door_without_floor_and_blocked_door(self):
        c = make_chunk(FLAT, [door("in", "entry", "L", 0, 4), door("out", "exit", "R", 0, 7)])
        probs = check_chunk(c)
        self.assertTrue(any("sem chão" in p for p in probs))
        self.assertTrue(any("sólida" in p for p in probs))  # a saída pega o chão e o teto

    def test_solo_false_and_missing_exit(self):
        c = make_chunk(FLAT, FLAT_DOORS[:1], solo=False)
        probs = check_chunk(c)
        self.assertTrue(any("solo" in p and p.startswith("erro") for p in probs))
        self.assertTrue(any("sem porta de saída" in p for p in probs))

    def test_fit(self):
        a = make_chunk(FLAT, FLAT_DOORS, "a")
        b = make_chunk(FLAT, FLAT_DOORS, "b")
        self.assertTrue(fit(a, "out", b, "in")[0])
        self.assertFalse(fit(a, "out", b.mirrored_copy(), "in")[0])  # saída R × entrada R
        low = make_chunk(FLAT, [door("in", "entry", "L", 1, 1), door("out", "exit", "R", 1, 1)], "low")
        ok, why = fit(a, "out", low, "in")
        self.assertFalse(ok)
        self.assertIn("corpo", why)

    def test_isolated_map_has_spawn_and_finish(self):
        c = make_chunk(FLAT, FLAT_DOORS)
        tm = isolated_map(c)
        self.assertIsNotNone(tm.spawn)
        self.assertGreater(tm.counts().get("FinishLine", 0), 0)
        # a célula (0, 0) do trecho fica em (0, 0) studs
        self.assertEqual(tm.cell_min(*tm.cell_at(1, 1)), (0.0, 0.0))
        self.assertEqual(tm.get(*tm.cell_at(1, 1)), "Block")

    def test_difficulty_levels(self):
        self.assertEqual(difficulty_level(float("inf")), 1)
        self.assertEqual(difficulty_level(0.5), 2)
        self.assertEqual(difficulty_level(0.3), 3)
        self.assertEqual(difficulty_level(0.15), 4)
        self.assertEqual(difficulty_level(0.05), 5)
        self.assertEqual(difficulty_level(0.3, hard=3), 4)


class SoloRouteTests(unittest.TestCase):
    def test_corridor_has_solo_route_and_is_easy(self):
        r = report("ex-corredor")
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.measured, 1)
        self.assertIn("walk", r.mechanics_used)
        self.assertGreater(len(r.route), 2)
        # ~96 studs de trecho + corredores de teste, a 38 studs/s
        self.assertLess(r.routes["fastest"]["time"], 5.0)

    def test_hook_gap_needs_hook(self):
        r = report("ex-vao-gancho")
        self.assertTrue(r.ok, r.problems)
        self.assertIn("hook", r.mechanics_used)
        self.assertGreaterEqual(r.measured, 2)

    def test_bifurcation_counts_two_lanes(self):
        r = report("ex-bifurcacao")
        self.assertTrue(r.ok, r.problems)
        self.assertEqual([ln["ok"] for ln in r.lanes], [True, True])
        self.assertGreaterEqual(r.paths, 2)
        fast, safe = r.lanes
        self.assertLess(fast["time"], safe["time"])

    def test_wall_without_hook_has_no_solo_route(self):
        rows = [
            "xxxxxxxxxxxxxxxxxxxx",
        ] + ["..........x........."] * 22 + [
            "####################",
        ]
        c = make_chunk(rows, [door("in", "entry", "L", 1, 4), door("out", "exit", "R", 1, 4)], "parede")
        r = validate_chunk(c, settings=QUICK, refine=False)
        self.assertFalse(r.ok)
        self.assertTrue(r.problems[0].startswith("erro"))


if __name__ == "__main__":
    unittest.main()
