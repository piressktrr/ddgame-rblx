"""Testes do montador (tools/mapkit/assemble.py) com os trechos mínimos de maps/trechos.

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.mapkit import preview
from tools.mapkit.assemble import (
    AssembleError,
    Assembly,
    analyze,
    assemble,
    assembly_overlay,
    plan_sections,
    render_report,
)
from tools.mapkit.chunks import CHUNK_FORMAT, Chunk, load_library
from tools.mapkit.tiles import TileMap
from tools.mapkit.validate import Settings, validate

QUICK = Settings.quick()


def plan(sections: list[list], **extra) -> dict:
    p = {
        "format": "race-and-escape/plan@1",
        "name": "teste",
        "sections": [{"id": f"s{k + 1}", "name": f"Seção {k + 1}", "theme": "exemplo", "chunks": items} for k, items in enumerate(sections)],
    }
    p.update(extra)
    return p


THREE = plan([["ex-corredor", "ex-bifurcacao"], ["ex-vao-gancho"]], max_width=2000)

_CACHE: dict[str, object] = {}


def lib() -> dict[str, Chunk]:
    if "lib" not in _CACHE:
        _CACHE["lib"] = load_library()
    return _CACHE["lib"]  # type: ignore[return-value]


def three() -> Assembly:
    if "three" not in _CACHE:
        _CACHE["three"] = assemble(THREE, lib())
    return _CACHE["three"]  # type: ignore[return-value]


def validated():
    if "v" not in _CACHE:
        asm = three()
        v = validate(asm.tiles, QUICK, jobs=1, refine=False, stages=asm.stages())
        _CACHE["v"] = (v, analyze(asm, v))
    return _CACHE["v"]


class AssembleTests(unittest.TestCase):
    def test_three_chunks_with_start_checkpoint_and_finish(self):
        asm = three()
        kinds = [p.kind for p in asm.pieces]
        self.assertEqual(kinds, ["largada", "trecho", "trecho", "checkpoint", "trecho", "chegada"])
        self.assertEqual([p.source for p in asm.pieces if p.kind == "trecho"], ["ex-corredor", "ex-bifurcacao", "ex-vao-gancho"])
        self.assertEqual([q for q in asm.problems if q.startswith("erro")], [])
        tm = asm.tiles
        counts = tm.counts()
        for el in ("StartLine", "Checkpoint", "FinishLine"):
            self.assertGreater(counts.get(el, 0), 0, el)
        attrs = {tuple(sorted(a.items())) for (i, j), a in tm.attributes.items() if tm.get(i, j) == "Checkpoint"}
        self.assertEqual(attrs, {(("Name", "Seção 1"), ("Order", 1), ("Section", "s1"), ("Split", True))})
        self.assertIsNotNone(tm.spawn)
        # sem sobreposição e cada saída colada na entrada seguinte
        boxes = [p.bbox for p in asm.pieces]
        for a in range(len(boxes)):
            for b in range(a + 1, len(boxes)):
                A, B = boxes[a], boxes[b]
                self.assertFalse(A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3], (a, b))
        for prev, nxt in zip(asm.pieces, asm.pieces[1:]):
            self.assertEqual(prev.bbox[2], nxt.bbox[0])
            self.assertEqual(prev.y + prev.exit.pos, nxt.y + nxt.entry.pos)  # chão alinhado

    def test_tiles_round_trip(self):
        tm = three().tiles
        again = TileMap.from_dict(tm.to_dict())
        self.assertEqual(again.cells, tm.cells)
        self.assertEqual(again.attributes, tm.attributes)

    def test_serpentine_turns_and_mirrors(self):
        asm = assemble(plan([["ex-corredor", "ex-bifurcacao", "ex-vao-gancho", "ex-corredor"]], max_width=300), lib())
        kinds = [p.kind for p in asm.pieces]
        self.assertIn("curva", kinds)
        after = asm.pieces[kinds.index("curva") + 1]
        self.assertEqual(after.kind, "trecho")
        self.assertTrue(after.chunk.mirrored)  # a fileira de cima corre para a esquerda
        self.assertGreater(after.y, asm.pieces[1].y)  # e fica em cima
        self.assertEqual([q for q in asm.problems if q.startswith("erro")], [])

    def test_vertical_exit_needs_matching_entry(self):
        rows = ["xxxx..xxxx"] + ["..........", ".........."] * 3 + ["##########"]
        up = Chunk.from_dict({
            "format": CHUNK_FORMAT, "id": "sobe", "name": "sobe", "tiles": {"cell": 4, "rows": rows},
            "doors": [{"id": "in", "role": "entry", "side": "L", "pos": 1, "width": 4},
                      {"id": "top", "role": "exit", "side": "T", "pos": 4, "width": 2}],
        })
        library = dict(lib())
        library["sobe"] = up
        with self.assertRaises(AssembleError):
            assemble(plan([["sobe", "ex-corredor"]]), library)

    def test_unknown_chunk_and_flat_list_sections(self):
        with self.assertRaises(AssembleError):
            plan_sections(plan([["nao-existe"]]), lib())
        secs = plan_sections({"chunks": ["ex-corredor", "ex-vao-gancho", "ex-bifurcacao"]}, lib())
        # ex-vao-gancho tem checkpoint_end: a lista corta depois dele
        self.assertEqual([len(s.items) for s in secs], [2, 1])

    def test_validated_map_is_solo_and_counts_bifurcation(self):
        v, an = validated()
        self.assertTrue(an["solo_ok"], an["problems"])
        self.assertEqual(len(an["sections"]), 2)
        s1, s2 = an["sections"]
        self.assertEqual(s1["checkpoint"], 1)
        self.assertIsNone(s2["checkpoint"])
        self.assertGreaterEqual(s1["bifurcations"], 1)  # ex-bifurcacao
        self.assertTrue(any("sem bifurcação" in q and "s2" in q for q in an["problems"]))
        self.assertGreater(an["total_medium"], an["total_fast"] * 0.99)
        self.assertTrue(any("alvo" in q for q in an["problems"]))  # mapa de teste: bem menos que 8 min
        by = {q["label"]: q for q in an["pieces"]}
        self.assertEqual(by["S1.1"]["measured"], 1)
        self.assertGreaterEqual(by["S1.2"]["branches"], 2)

    def test_report_and_previews(self):
        v, an = validated()
        asm = three()
        md = render_report(asm, an, "plano.json")
        self.assertIn("## Seções", md)
        self.assertIn("ex-bifurcacao", md)
        tm, ov = assembly_overlay(asm, v, an)
        svg = preview.render_svg(tm, ov)
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("rota mais rápida", svg)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "m.png"
            w, h = preview.render_png(tm, ov, out)
            data = out.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertGreater(w, tm.width)


if __name__ == "__main__":
    unittest.main()
