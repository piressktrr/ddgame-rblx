"""Testes da tabela de medidas (tools/mapkit/metrics.py).

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

from __future__ import annotations

import json
import math
import unittest

from tools.mapkit import metrics
from tools.mapkit.luau_config import load_config
from tools.mapkit.physics import GridWorld, State, default_params, jump, move, simulate

P = default_params()


def gap_world(gap: float, level: float = 0.0) -> GridWorld:
    """Borda de partida em x = 0 (topo y = 0) e de chegada em x = gap (topo y = level)."""
    world = GridWorld(metrics.CELL)
    world.fill_rect(-200, -40, 0, 0, "block")
    world.fill_rect(gap, -40, gap + 200, level, "block")
    return world


def crosses(gap: float, level: float, dj_time: float | None) -> bool:
    events = [move(0, 1), jump(0)]
    if dj_time is not None:
        events.append(jump(dj_time))
    res = simulate(metrics.edge_start(P), events, gap_world(gap, level), 4, kill_y=-30)
    return res.final.grounded and res.final.x > gap and abs(res.final.feet() - level) < 1e-3


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = metrics.compute_metrics(quick=True)
        cls.m = cls.data["metrics"]

    def test_jump_numbers(self):
        jump_m = self.m["jump"]
        self.assertAlmostEqual(jump_m["jump_height"], 11.56, delta=0.05)
        self.assertAlmostEqual(jump_m["double_jump_height"], 21.8, delta=0.1)
        self.assertAlmostEqual(
            jump_m["double_jump_best_time_for_height"], P.jump_power / P.gravity, delta=2 / 60
        )

    def test_reach_table_is_reproducible_in_grid(self):
        row = next(r for r in self.m["reach"]["rows"] if r["level"] == 0)
        gap = row["jump_gap"]
        self.assertAlmostEqual(gap, P.walk_speed * 2 * P.jump_power / P.gravity + P.box_width, delta=1.0)
        cell = metrics.CELL
        self.assertTrue(crosses(metrics.floor_to(gap - 0.7, cell), 0, None))
        self.assertFalse(crosses(metrics.ceil_to(gap + 0.7, cell), 0, None))
        dj_gap, dj_t = row["double_jump_gap"], row["double_jump_time"]
        self.assertGreater(dj_gap, gap)
        self.assertTrue(crosses(metrics.floor_to(dj_gap - 0.7, cell), 0, dj_t))
        self.assertFalse(crosses(metrics.ceil_to(dj_gap + 0.7, cell), 0, dj_t))

    def test_reach_up_needs_double_jump(self):
        rows = {r["level"]: r for r in self.m["reach"]["rows"]}
        self.assertIsNone(rows[12]["jump_gap"])  # 12 > altura do pulo
        self.assertIsNotNone(rows[12]["double_jump_gap"])
        self.assertGreater(rows[-8]["jump_gap"], rows[0]["jump_gap"])

    def test_camera(self):
        cam = self.m["camera"]
        height = 2 * 64 * math.tan(math.radians(25))
        self.assertAlmostEqual(cam["visible_height"], height, places=2)
        self.assertAlmostEqual(cam["visible_width"], height * 16 / 9, places=2)
        self.assertAlmostEqual(cam["visible_up_from_root"], height / 2 + 6, places=2)
        self.assertLess(self.m["hook"]["on_screen_up"], P.hook_range)

    def test_hook_measures(self):
        hc = self.m["hook_climb_on_screen"]
        self.assertGreater(hc["max_feet_rise_no_double_jump"], hc["anchor_height"])
        self.assertGreater(hc["max_feet_rise_with_double_jump"], hc["max_feet_rise_no_double_jump"])
        self.assertLess(hc["hang_root_below_anchor"], P.drag_min_distance + P.hang_damping_margin)
        gap = self.m["hook_gap"]["gap"]
        dj_gap = next(r for r in self.m["reach"]["rows"] if r["level"] == 0)["double_jump_gap"]
        self.assertGreater(gap, dj_gap)
        self.assertGreater(self.m["hook_wall_climb"]["max_wall_height"], 24)

    def test_rules_are_consistent(self):
        rules = {r["id"]: r for r in self.m["rules"]}
        for rule in rules.values():
            self.assertAlmostEqual(rule["blocks"] * 4, rule["studs"], places=6)
            self.assertAlmostEqual(rule["cells"] * 2, rule["studs"], places=6)
        self.assertLessEqual(rules["step_jump_comfort"]["studs"], rules["step_jump_max"]["studs"])
        self.assertLess(rules["step_jump_max"]["studs"], self.m["jump"]["jump_height"])
        self.assertLess(rules["step_double_jump_max"]["studs"], rules["step_needs_hook"]["studs"])
        self.assertGreater(rules["step_needs_hook"]["studs"], self.m["jump"]["double_jump_height"])
        self.assertLess(rules["gap_double_jump_max"]["studs"], rules["gap_needs_hook"]["studs"])
        self.assertLessEqual(rules["hook_target_up"]["studs"], self.m["camera"]["visible_up_from_root"])
        self.assertLessEqual(rules["hook_target_distance"]["studs"], P.hook_range)
        self.assertGreaterEqual(rules["ceiling_walk_min"]["studs"], P.box_height)
        self.assertGreaterEqual(rules["corridor_width_min"]["studs"], P.box_width)

    def test_markdown_renders(self):
        text = metrics.render_markdown(self.data)
        self.assertIn("Arquivo gerado", text)
        self.assertIn("Regras de desenho", text)
        self.assertIn(self.data["config"]["sha256"][:16], text)

    def test_generated_json_matches_config(self):
        """maps/metrics.json foi gerado com o Config atual (senão: regenerar)."""
        self.assertTrue(metrics.JSON_PATH.exists(), "rode tools/mapkit/metrics.py")
        saved = json.loads(metrics.JSON_PATH.read_text(encoding="utf-8"))
        self.assertEqual(saved["config"]["sha256"], load_config().sha256)
        self.assertEqual(saved["schema"], metrics.SCHEMA_VERSION)


class HelperTests(unittest.TestCase):
    def test_grid_rounding(self):
        self.assertEqual(metrics.floor_to(11.56, 4), 8)
        self.assertEqual(metrics.ceil_to(21.8, 4), 24)
        self.assertEqual(metrics.floor_to(8.0, 4), 8)
        self.assertEqual(metrics.ceil_to(8.0, 4), 8)

    def test_br_format(self):
        self.assertEqual(metrics.br(11.56, 2), "11,56")
        self.assertEqual(metrics.br(8.0), "8")
        self.assertEqual(metrics.br(None), "—")

    def test_standing_state(self):
        s = State.standing(0, 10)
        self.assertAlmostEqual(s.feet(), 10, places=4)


if __name__ == "__main__":
    unittest.main()
