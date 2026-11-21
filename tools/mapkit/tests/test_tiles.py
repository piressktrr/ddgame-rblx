"""Testes do formato de grade (tools/mapkit/tiles.py) e da conversão do layout.

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

import json
import unittest
from pathlib import Path

from tools.mapkit import convert_layout
from tools.mapkit.tiles import FORMAT, TileMap, from_rows

ROOT = Path(__file__).resolve().parents[3]

SAMPLE = [
    "....g",
    "#.o.x",
    "#hkf#",
]


class TestFormat(unittest.TestCase):
    def setUp(self):
        self.tm = from_rows(SAMPLE, cell=2, origin=(10, 20), name="amostra")

    def test_rows_start_at_top(self):
        self.assertEqual(self.tm.get(0, 0), "Block")  # canto inferior esquerdo
        self.assertEqual(self.tm.get(4, 2), "HookOnce")  # canto superior direito
        self.assertEqual(self.tm.get(1, 0), "HookThrough")
        self.assertIsNone(self.tm.get(1, 1))
        self.assertEqual(self.tm.direction(2, 1), "Up")  # mão única sem direção vira "Up"

    def test_cell_studs(self):
        self.assertEqual(self.tm.cell_min(0, 0), (10, 20))
        self.assertEqual(self.tm.cell_center(1, 2), (13, 25))
        self.assertEqual(self.tm.cell_at(11.9, 21.9), (0, 0))
        self.assertEqual(self.tm.cell_at(12.0, 22.0), (1, 1))
        self.assertEqual(self.tm.cell_at(9.9, 20), (-1, 0))
        self.assertEqual(self.tm.bounds(), (10, 20, 20, 26))

    def test_round_trip_is_stable(self):
        self.tm.set(2, 1, "OneWay", "Left")
        self.tm.attributes[(3, 0)] = {"Order": 1}
        self.tm.spawn = (1, 1)
        text = self.tm.dumps()
        again = TileMap.from_dict(json.loads(text))
        self.assertEqual(again.dumps(), text)
        self.assertEqual(again.direction(2, 1), "Left")
        self.assertEqual(again.attributes[(3, 0)], {"Order": 1})
        self.assertEqual(again.spawn, (1, 1))
        data = json.loads(text)
        self.assertEqual(data["format"], FORMAT)
        self.assertEqual(data["rows"], ["....g", "#.o.x", "#hkf#"])
        self.assertEqual(data["directions"], {"2,1": "Left"})

    def test_matches_mapbuilder_export_text(self):
        # Texto como o botão Exportar do plugin (e o export_editor.luau) escreve: o Python tem de
        # ler e regravar igual, byte a byte.
        legend = "\n".join(
            f'  "{c}": {"null" if e is None else chr(34) + e + chr(34)}{"," if n < 14 else ""}'
            for n, (c, e) in enumerate(
                [(".", None), ("#", "Block"), ("x", "Unhookable"), ("h", "HookThrough"), ("f", "Freeze"),
                 ("u", "Unfreeze"), ("o", "OneWay"), ("k", "Kill"), ("g", "HookOnce"), ("S", "StartLine"),
                 ("F", "FinishLine"), ("s", "SoloStart"), ("e", "SoloEnd"), ("c", "Checkpoint"), ("R", "RaceStart")]
            )
        )
        text = (
            '{\n "format": "race-and-escape/tiles@1",\n "name": "Editor",\n'
            ' "source": "MapBuilder (Workspace.Maps.Editor)",\n "cell": 2,\n "origin": [-4, 6],\n'
            ' "width": 3,\n "height": 2,\n "legend": {\n' + legend + "\n },\n"
            ' "spawn": [0, 1],\n "directions": {\n  "2,0": "Left"\n },\n "attributes": {},\n'
            ' "rows": [\n  "..f",\n  "##o"\n ]\n}\n'
        )
        tm = TileMap.from_dict(json.loads(text))
        self.assertEqual(tm.dumps(), text)
        self.assertEqual(tm.get(2, 0), "OneWay")
        self.assertEqual(tm.direction(2, 0), "Left")
        self.assertEqual(tm.cell_min(*tm.spawn), (-4, 8))

    def test_custom_legend_and_errors(self):
        data = json.loads(self.tm.dumps())
        data["legend"] = {" ": None, "B": "Block"}
        data["rows"] = ["  B", "BBB"]
        data["width"], data["height"] = 3, 2
        tm = TileMap.from_dict(data)
        self.assertEqual(tm.counts(), {"Block": 4})
        data["rows"] = ["  Z", "BBB"]
        with self.assertRaises(ValueError):
            TileMap.from_dict(data)
        data["format"] = "outro@1"
        with self.assertRaises(ValueError):
            TileMap.from_dict(data)

    def test_rects_like_grid_merge(self):
        tm = from_rows(["##..", "##.#", "oo.#"])
        tm.set(1, 0, "OneWay", "Down")
        rects = {(r.i, r.j, r.w, r.h, r.element, r.direction) for r in tm.rects()}
        self.assertEqual(
            rects,
            {
                (0, 0, 1, 1, "OneWay", "Up"),
                (1, 0, 1, 1, "OneWay", "Down"),
                (3, 0, 1, 2, "Block", None),
                (0, 1, 2, 2, "Block", None),
            },
        )
        covered = sum(r.w * r.h for r in tm.rects())
        self.assertEqual(covered, len(tm.cells))


class TestWorld(unittest.TestCase):
    def setUp(self):
        # x0 = 0, y0 = 0, cell 2: colunas em x 0..2, 2..4, ...; j = 0 é a linha de baixo.
        self.tm = from_rows(
            [
                "..........",
                "#.h.k.x.g#",
                "##########",
            ]
        )
        self.world = self.tm.to_world()

    def test_is_solid(self):
        w = self.world
        self.assertTrue(w.is_solid(1, 1))  # chão
        self.assertTrue(w.is_solid(5, 3))  # hookthrough
        self.assertFalse(w.is_solid(9, 3))  # morte (MapBuilder: atravessável)
        self.assertTrue(w.is_solid(13, 3))  # unhookable
        self.assertTrue(w.is_solid(17, 3))  # gancho único
        self.assertFalse(w.is_solid(3, 3))
        self.assertFalse(w.is_solid(-5, 3))  # fora da grade
        self.assertTrue(self.tm.to_world(outside_solid=True).is_solid(-5, 3))

    def test_one_way(self):
        tm = from_rows(["o"])
        tm.set(0, 0, "OneWay", "Up")
        w = tm.to_world()
        self.assertFalse(w.is_solid(1, 1))  # parado
        self.assertFalse(w.is_solid(1, 1, 0, 5))  # subindo passa
        self.assertTrue(w.is_solid(1, 1, 0, -5))  # descendo é chão
        self.assertFalse(w.is_solid(1, 1, 5, 0))  # de lado passa
        self.assertEqual(w.one_way_at(1, 1), "Up")
        self.assertEqual(w.hook_surface_at(1, 1), "through")

    def test_zones_and_surfaces(self):
        w = self.world
        self.assertEqual(w.zone_at(9, 3), "kill")
        self.assertIsNone(w.zone_at(3, 3))
        self.assertEqual(w.hook_surface_at(1, 1), "hook")
        self.assertEqual(w.hook_surface_at(5, 3), "through")
        self.assertIsNone(w.hook_surface_at(9, 3))
        self.assertEqual(w.hook_surface_at(13, 3), "nohook")
        self.assertEqual(w.hook_surface_at(17, 3), "once")

    def test_collide_override(self):
        self.tm.collide["Kill"] = True
        w = self.tm.to_world()
        self.assertTrue(w.is_solid(9, 3))
        self.assertEqual(w.zone_at(9, 3), "kill")
        self.assertEqual(w.hook_surface_at(9, 3), "hook")  # zona sólida sem tag: gancho prende

    def test_raycast(self):
        w = self.world
        hit = w.raycast_hook((3, 3), (0, -1), 50)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.surface, "hook")
        self.assertEqual(hit.cell, (1, 0))
        self.assertAlmostEqual(hit.point[1], 2.0)
        self.assertAlmostEqual(hit.distance, 1.0)
        # Para a direita, de x = 3: atravessa hookthrough (x 4..6) e morte (8..10), barra no unhookable.
        hit = w.raycast_hook((3, 3), (1, 0), 50)
        self.assertEqual((hit.surface, hit.cell), ("nohook", (6, 1)))
        self.assertAlmostEqual(hit.point[0], 12.0)
        # Curto demais.
        self.assertIsNone(w.raycast_hook((3, 3), (1, 0), 8.5))
        # Para cima: nada (sai da grade).
        self.assertIsNone(w.raycast_hook((3, 3), (0, 1), 500))
        # Diagonal para baixo e para a esquerda acerta o chão ou a parede.
        hit = w.raycast_hook((3, 3), (-1, -1), 50)
        self.assertEqual(hit.surface, "hook")
        self.assertIn(hit.cell, {(0, 1), (1, 0), (0, 0)})
        # Começando dentro do bloco: a própria célula não conta.
        hit = w.raycast_hook((1, 3), (1, 0), 50)
        self.assertEqual(hit.surface, "nohook")
        self.assertIsNone(w.raycast_hook((0, 0), (0, 0), 50))

    def test_raycast_from_outside(self):
        hit = self.world.raycast_hook((-10, 1), (1, 0), 50)
        self.assertEqual((hit.surface, hit.cell), ("hook", (0, 0)))
        self.assertAlmostEqual(hit.distance, 10.0)


class TestConvert(unittest.TestCase):
    def layout(self, parts):
        return {"name": "T", "bounds": {"x1": -4, "y1": 0, "x2": 12, "y2": 8}, "parts": parts}

    def test_kinds_and_priority(self):
        parts = [
            {"kind": "Rock", "class": "Part", "center": [4, 1, 0], "size": [16, 2, 12]},
            {"kind": "Kill", "class": "Part", "center": [0, 1, 0], "size": [4, 2, 12]},  # sobre a rocha
            {"kind": "Spawn", "class": "SpawnLocation", "center": [-2, 3, 0], "size": [4, 2, 1]},
            {"kind": "Checkpoint", "class": "Part", "center": [9, 3, 0], "size": [2, 2, 12],
             "attributes": {"Order": 1}},
            {"kind": "Sign", "class": "Part", "center": [4, 4, -9], "size": [8, 4, 1]},
            {"kind": "Ice", "class": "Part", "center": [5, 5, 0], "size": [2, 2, 12]},
        ]
        tm, report = convert_layout.convert(self.layout(parts))
        self.assertEqual((tm.width, tm.height, tm.origin), (8, 4, (-4, 0)))
        self.assertEqual(tm.get(0, 0), "Block")
        self.assertEqual(tm.get(1, 0), "Kill")  # x -2..0
        self.assertEqual(tm.get(2, 0), "Kill")
        self.assertEqual(tm.get(3, 0), "Block")
        self.assertEqual(tm.get(1, 1), "RaceStart")
        self.assertEqual(tm.get(6, 1), "Checkpoint")
        self.assertEqual(tm.attributes[(6, 1)], {"Order": 1})
        self.assertEqual(tm.get(4, 2), "Freeze")
        self.assertEqual(report["overlaps"], 2)
        self.assertEqual(report["ignored"], {"Sign": 1})
        self.assertIn(tm.spawn, {(0, 2), (1, 2)})
        self.assertTrue(tm.collide["Kill"])

    def test_wedge_and_rotated(self):
        parts = [
            # sobe para a esquerda: canto reto embaixo à esquerda
            {"kind": "SlopeR", "class": "WedgePart", "center": [0, 4, 0], "size": [8, 8, 12], "slopeFaces": "+X"},
            {"kind": "SlopeL", "class": "WedgePart", "center": [8, 4, 0], "size": [8, 8, 12], "slopeFaces": "-X"},
        ]
        tm, _ = convert_layout.convert(self.layout(parts))
        self.assertEqual(tm.get(0, 0), "Block")
        self.assertEqual(tm.get(0, 3), None)  # centro (-3, 7): fora do triângulo (v=0.875, u=0.125)
        self.assertEqual(tm.get(0, 2), "Block")  # (-3, 5): v=0.625 < 0.875
        self.assertEqual(tm.get(2, 0), "Block")  # (1, 1): v=0.125 < 1 - 0.625
        self.assertIsNone(tm.get(3, 0))  # (3, 1): na borda inclinada, fica de fora
        self.assertIsNone(tm.get(3, 3))
        self.assertEqual(tm.get(7, 2), "Block")  # SlopeL: canto reto à direita
        self.assertIsNone(tm.get(4, 3))
        rotated = [{"kind": "Kill", "class": "Part", "center": [5, 4, 0], "size": [12, 2, 12], "rotZ": 90}]
        tm, _ = convert_layout.convert(self.layout(rotated))
        self.assertEqual(sorted(tm.cells), [(4, j) for j in range(4)])

    def test_map01_file_matches_layout(self):
        layout_path = ROOT / "maps" / "map01" / "layout.json"
        tiles_path = ROOT / "maps" / "map01" / "tiles.json"
        if not layout_path.exists() or not tiles_path.exists():
            self.skipTest("map01 ausente")
        layout = json.loads(layout_path.read_text(encoding="utf8"))
        saved = TileMap.load(tiles_path)
        tm, report = convert_layout.convert(layout, saved.source)
        self.assertEqual(tm.dumps(), saved.dumps(), "tiles.json desatualizado: rode convert_layout.py")
        self.assertEqual(report["overlaps"], 0)
        self.assertEqual(report["empty_parts"], [])
        orders = sorted({a["Order"] for a in saved.attributes.values() if "Order" in a})
        self.assertEqual(orders, [1, 2, 3])
        world = saved.to_world()
        x, y = saved.cell_min(*saved.spawn)
        self.assertFalse(world.is_solid(x + 1, y + 1))  # nasce no ar
        self.assertTrue(world.is_solid(x + 1, y - 1))  # em cima da faixa de início (sólida no map01)


if __name__ == "__main__":
    unittest.main()
