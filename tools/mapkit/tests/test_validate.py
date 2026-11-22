"""Testes do validador de mapa (tools/mapkit/validate.py) com mapas pequenos montados à mão.

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

from __future__ import annotations

import unittest

from tools.mapkit import report
from tools.mapkit.tiles import TileMap, from_rows
from tools.mapkit.validate import (
    INF,
    Edge,
    Graph,
    Node,
    Settings,
    Validation,
    build_geometry,
    disjoint_between,
    validate,
)

QUICK = Settings.quick()
W = 80  # colunas (160 studs)


def blank(height: int) -> list[list[str]]:
    return [["."] * W for _ in range(height)]


def put(grid: list[list[str]], i0: int, i1: int, j0: int, j1: int, ch: str) -> None:
    """Pinta colunas i0..i1 e linhas j0..j1 (j de baixo para cima, inclusive)."""
    h = len(grid)
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            grid[h - 1 - j][i] = ch


def make(grid: list[list[str]], spawn: tuple[int, int]) -> TileMap:
    tm = from_rows(["".join(r) for r in grid], name="teste")
    tm.spawn = spawn
    return tm


_CACHE: dict[str, Validation] = {}


def run(name: str, tm: TileMap) -> Validation:
    if name not in _CACHE:
        _CACHE[name] = validate(tm, QUICK, jobs=1, refine=False)
    return _CACHE[name]


def simple_map() -> TileMap:
    g = blank(14)
    put(g, 0, W - 1, 0, 1, "#")
    put(g, W - 4, W - 2, 2, 2, "F")
    return make(g, (2, 2))


def island_map() -> TileMap:
    g = blank(50)
    put(g, 0, W - 1, 0, 1, "#")
    put(g, W - 4, W - 2, 2, 2, "F")
    put(g, 30, 40, 42, 42, "x")  # laje proibida a ~80 studs do chão: nada a alcança
    return make(g, (2, 2))


def gap_map(with_anchor: bool) -> TileMap:
    g = blank(24)
    put(g, 0, 14, 0, 1, "#")
    put(g, 65, W - 1, 0, 1, "#")  # vão de 100 studs: maior que o pulo duplo (~69)
    put(g, W - 4, W - 2, 2, 2, "F")
    if with_anchor:
        put(g, 28, 29, 15, 16, "#")  # bloco de gancho acima do começo do vão
    return make(g, (2, 2))


def wall_map() -> TileMap:
    g = blank(26)
    put(g, 0, W - 1, 0, 1, "#")
    put(g, 40, W - 1, 2, 16, "#")  # degrau de 30 studs: acima do pulo duplo (~22), abaixo de 1 gancho (~38)
    put(g, W - 4, W - 2, 17, 17, "F")
    return make(g, (2, 2))


def step_map() -> TileMap:
    g = blank(16)
    put(g, 0, W - 1, 0, 1, "#")
    put(g, 40, W - 1, 2, 4, "#")  # degrau de 6 studs: pulo simples
    put(g, W - 4, W - 2, 5, 5, "F")
    return make(g, (2, 2))


class GeometryTests(unittest.TestCase):
    def test_platforms_and_finish_zone(self):
        geo = build_geometry(simple_map())
        self.assertEqual(geo.spawn_pid, 0)
        self.assertEqual(len(geo.platforms), 1)
        plat = geo.platforms[0]
        self.assertEqual((plat.i0, plat.i1, plat.floor_y), (0, W - 1, 4.0))
        self.assertIn("fin", plat.zone_x)
        self.assertEqual([z.zid for z in geo.zones], ["fin"])


class ValidatorTests(unittest.TestCase):
    def test_simple_route_reaches_finish(self):
        v = run("simple", simple_map())
        self.assertEqual(v.results["stage_reach"], [True])
        fast = v.results["routes"]["fastest"]
        self.assertIsNotNone(fast)
        # andar ~150 studs a 38 studs/s (algum pulo/gancho pode encurtar um pouco)
        self.assertLess(fast["time"], 160 / v.geo.params.walk_speed + 0.5)
        self.assertEqual(v.results["islands"], [])
        self.assertEqual(v.results["traps"], [])

    def test_unreachable_platform_is_island(self):
        v = run("island", island_map())
        self.assertEqual(v.results["stage_reach"], [True])
        islands = v.results["islands"]
        self.assertEqual(len(islands), 1)
        self.assertGreater(islands[0].floor_y, 70)

    def test_gap_only_passes_with_hook(self):
        v = run("gap", gap_map(True))
        self.assertEqual(v.results["stage_reach"], [True])
        self.assertIsNone(v.results["filters"]["sem gancho"])
        fast = v.results["routes"]["fastest"]
        self.assertTrue(any("hook" in k for k in fast["by_kind"]))
        # o ponto de gancho é usado
        self.assertTrue(any(a.status == "usado" for a in v.results["anchors"]))
        without = run("gap-sem-ponto", gap_map(False))
        self.assertEqual(without.results["stage_reach"], [False])
        self.assertIsNone(without.results["routes"]["fastest"])

    def test_detects_hook_only_route(self):
        v = run("wall", wall_map())
        self.assertEqual(v.results["stage_reach"], [True])
        self.assertIsNone(v.results["filters"]["sem gancho"])  # 30 studs: pulo duplo não sobe
        only_hook = v.results["filters"]["só gancho (sem pulo nenhum)"]
        self.assertIsNotNone(only_hook)
        self.assertTrue(all("hook" in k or k == "walk" for k in only_hook["by_kind"]))
        # e o degrau é classificado como "só gancho"
        self.assertIn("só gancho", {s["class"] for s in v.results["steps"]})

    def test_small_step_needs_no_hook(self):
        v = run("step", step_map())
        self.assertIsNotNone(v.results["filters"]["sem gancho"])
        self.assertIn("pulo", {s["class"] for s in v.results["steps"]})

    def test_report_renders(self):
        v = run("gap", gap_map(True))
        md, svg = report.render(v, "teste.svg", "teste.json")
        self.assertIn("## Resumo", md)
        self.assertIn("## Bifurcações", md)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))


class BifurcationTests(unittest.TestCase):
    """Grafo montado à mão: só a contagem de caminhos por plataformas diferentes."""

    @staticmethod
    def graph(edges: list[tuple[int, int, float]], n: int) -> Graph:
        nodes = [Node(k, "stand", float(10 * k), 0.0, pid=k) for k in range(n)]
        es = [Edge(a, b, t, 0.5, "jump") for a, b, t in edges]
        out: dict[int, list[int]] = {}
        for idx, e in enumerate(es):
            out.setdefault(e.src, []).append(idx)
        return Graph(None, nodes, es, out, {k: [k] for k in range(n)}, set(range(n)), {})  # type: ignore[arg-type]

    def test_two_disjoint_paths(self):
        # 0 -> 1 -> 3 e 0 -> 2 -> 3 (plataformas 1 e 2 diferentes)
        g = self.graph([(0, 1, 1.0), (1, 3, 1.0), (0, 2, 2.0), (2, 3, 2.0)], 4)
        routes = disjoint_between(g, 0, 3)
        self.assertEqual(len(routes), 2)
        self.assertEqual([round(r["time"], 3) for r in routes], [2.0, 4.0])
        self.assertGreater(routes[1]["spread"], 0)

    def test_shared_platform_is_one_path(self):
        # 0 -> 1 -> 2 -> 4 e 0 -> 1 -> 3 -> 4: todo caminho passa pela plataforma 1
        g = self.graph([(0, 1, 1.0), (1, 2, 1.0), (2, 4, 1.0), (1, 3, 1.0), (3, 4, 1.0)], 5)
        self.assertEqual(len(disjoint_between(g, 0, 4)), 1)

    def test_no_path(self):
        g = self.graph([(0, 1, 1.0)], 3)
        self.assertEqual(disjoint_between(g, 0, 2), [])
        self.assertEqual(INF, float("inf"))


if __name__ == "__main__":
    unittest.main()
