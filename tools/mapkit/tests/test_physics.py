"""Testes do leitor do Config e do simulador (tools/mapkit/luau_config.py e physics.py).

Rodar da raiz: python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
"""

from __future__ import annotations

import math
import unittest

from tools.mapkit.luau_config import load_config, parse_config_source, strip_comments
from tools.mapkit.physics import (
    GridWorld,
    MovementParams,
    State,
    default_params,
    hook,
    hook_drag,
    jump,
    move,
    saturated_add,
    simulate,
    unhook,
)

P = default_params()


def flat_world(top: float = 0.0) -> GridWorld:
    world = GridWorld(2.0)
    world.fill_rect(-200, top - 8, 200, top, "block")
    return world


class PointOnlyWorld:
    """Mundo genérico (só `is_solid` e `raycast_hook`), para testar o caminho sem atalhos da grade."""

    def __init__(self, grid: GridWorld):
        self.grid = grid

    def is_solid(self, x: float, y: float) -> bool:
        return self.grid.is_solid(x, y)

    def raycast_hook(self, origin, direction, max_dist):
        hit = self.grid.raycast_hook(origin, direction, max_dist)
        return None if hit is None else (hit[0], hit[1])


class ConfigParserTests(unittest.TestCase):
    def test_reads_current_config(self):
        cfg = load_config()
        self.assertEqual(cfg.get("Movement.Gravity"), 112.5)
        self.assertEqual(cfg.get("Movement.WalkSpeed"), 38)
        self.assertEqual(cfg.get("Movement.JumpPower"), 51)
        self.assertEqual(cfg.get("Movement.DoubleJumpVelocity"), 48)
        self.assertEqual(cfg.get("Hook.Range"), 40)
        self.assertEqual(cfg.get("Hook.Mode"), "DDNet")
        self.assertEqual(cfg.get("Camera.Distance"), 64)
        self.assertEqual(cfg.get("Camera.FieldOfView"), 50)
        self.assertEqual(cfg.get("MapElements.DefaultGrid"), 4)
        self.assertEqual(cfg.get("Zones.CharacterBoxSize"), (2.0, 5.5, 1.0))
        self.assertIs(cfg.get("Hook.IgnoreNonCollidable"), True)
        self.assertEqual(cfg.get("Freeze.ReleaseDelay"), 1)
        self.assertEqual(len(cfg.sha256), 64)
        # Color3 e Enum ficam de fora
        self.assertIsNone(cfg.get("Hook.RopeColor"))
        self.assertIn("Hook.RopeColor", cfg.skipped)
        self.assertIsNone(cfg.get("RaceUi.Font"))

    def test_parser_handles_syntax(self):
        source = """
        --!strict
        --[[ bloco
            Config = { Fake = 1 }
        ]]
        local Other = 3
        local Config = {
            A = 1, -- comentário com = e { }
            B = -2.5e1,
            C = "texto -- não é comentário",
            D = { X = 1 / 4, Y = (2 + 3) * 2, Z = 2 ^ 3 },
            E = Vector3.new(1, -2, 3.5),
            F = Color3.fromRGB(1, 2, 3),
            G = Enum.Font.GothamBold,
            H = false,
            I = { "a", "b" },
            J = 0x10,
            --[==[ outro ]==] K = 'aspas',
            L = Other,
        }
        return table.freeze(Config)
        """
        values, skipped = parse_config_source(source)
        self.assertEqual(values["A"], 1)
        self.assertEqual(values["B"], -25.0)
        self.assertEqual(values["C"], "texto -- não é comentário")
        self.assertEqual(values["D"], {"X": 0.25, "Y": 10, "Z": 8.0})
        self.assertEqual(values["E"], (1.0, -2.0, 3.5))
        self.assertNotIn("F", values)
        self.assertNotIn("G", values)
        self.assertIs(values["H"], False)
        self.assertEqual(values["I"], ["a", "b"])
        self.assertEqual(values["J"], 16)
        self.assertEqual(values["K"], "aspas")
        self.assertNotIn("L", values)
        self.assertIn("F", skipped)
        self.assertNotIn("Fake", values)

    def test_strip_comments_keeps_strings(self):
        self.assertEqual(strip_comments('a = "x--y" -- fim').strip(), 'a = "x--y"')


class JumpTests(unittest.TestCase):
    def test_jump_height_matches_formula(self):
        start = State.standing(0, 0)
        res = simulate(start, [jump(0)], flat_world(), 3, stop_on_land=True)
        height = res.max_y - start.y
        expected = P.jump_power**2 / (2 * P.gravity)
        self.assertAlmostEqual(expected, 11.56, places=2)
        self.assertAlmostEqual(height, expected, delta=0.05)
        self.assertEqual(res.stop_reason, "landed")
        self.assertAlmostEqual(res.time, 2 * P.jump_power / P.gravity, delta=2 / 60)
        self.assertAlmostEqual(res.final.y, start.y, delta=1e-3)

    def test_running_jump_distance(self):
        start = State.standing(0, 0)
        res = simulate(start, [move(0, 1), jump(0)], flat_world(), 3, stop_on_land=True)
        self.assertAlmostEqual(res.final.x, P.walk_speed * res.time, delta=0.01)

    def test_double_jump_at_apex(self):
        start = State.standing(0, 0)
        apex = P.jump_power / P.gravity
        res = simulate(start, [jump(0), jump(apex)], flat_world(), 4, stop_on_land=True)
        self.assertEqual(len(res.event_times("double_jump")), 1)
        expected = (P.jump_power**2 + P.double_jump_velocity**2) / (2 * P.gravity)
        self.assertAlmostEqual(res.max_y - start.y, expected, delta=0.1)

    def test_double_jump_rules(self):
        start = State.standing(0, 0)
        # cedo demais (antes de DoubleJumpMinAirTime): não vale
        res = simulate(start, [jump(0), jump(0.05)], flat_world(), 3, stop_on_land=True)
        self.assertEqual(res.event_times("double_jump"), [])
        # uma carga só
        res = simulate(start, [jump(0), jump(0.3), jump(0.6)], flat_world(), 3, stop_on_land=True)
        self.assertEqual(len(res.event_times("double_jump")), 1)
        # apertos colados contam como um
        res = simulate(start, [jump(0), jump(0.2), jump(0.25)], flat_world(), 3)
        self.assertEqual(len(res.event_times("double_jump")), 1)
        # tocar o chão recarrega
        res = simulate(start, [jump(0), jump(0.3), jump(2.5), jump(2.8)], flat_world(), 5)
        self.assertEqual(len(res.event_times("double_jump")), 2)

    def test_double_jump_keeps_horizontal_speed_and_zeroes_fall(self):
        start = State.standing(0, 0)
        res = simulate(start, [move(0, 1), jump(0), jump(0.7)], flat_world(), 0.75)
        self.assertEqual(len(res.event_times("double_jump")), 1)
        sample = next(s for s in res.trajectory if s.t >= 0.7 - 1e-9 + 1 / 60)
        self.assertAlmostEqual(sample.vx, P.walk_speed)
        self.assertGreater(sample.vy, P.double_jump_velocity - P.gravity / 60 - 1e-6)


class CollisionTests(unittest.TestCase):
    def test_floor_holds_body(self):
        start = State.standing(0, 0)
        res = simulate(start, [], flat_world(), 1)
        self.assertTrue(res.landed)
        self.assertAlmostEqual(res.final.feet(), 0.0, delta=1e-3)

    def test_fall_lands_on_floor(self):
        start = State(x=0, y=40)
        res = simulate(start, [], flat_world(), 4, stop_on_land=True)
        self.assertEqual(res.stop_reason, "landed")
        self.assertAlmostEqual(res.final.feet(), 0.0, delta=1e-6)

    def test_wall_stops_walk(self):
        world = flat_world()
        world.fill_rect(20, 0, 24, 40, "block")
        res = simulate(State.standing(0, 0), [move(0, 1)], world, 2)
        self.assertAlmostEqual(res.final.x, 20 - P.half_width, delta=1e-6)
        self.assertEqual(res.final.vx, 0.0)

    def test_wall_from_the_right(self):
        world = flat_world()
        world.fill_rect(-24, 0, -20, 40, "block")
        res = simulate(State.standing(0, 0), [move(0, -1)], world, 2)
        self.assertAlmostEqual(res.final.x, -20 + P.half_width, delta=1e-6)

    def test_ceiling_cuts_jump(self):
        world = flat_world()
        world.fill_rect(-20, 10, 20, 12, "block")  # teto em y = 10
        start = State.standing(0, 0)
        res = simulate(start, [jump(0)], world, 2, stop_on_land=True)
        head = max(s.y for s in res.trajectory) + P.head_offset
        self.assertAlmostEqual(head, 10.0, delta=1e-6)
        self.assertEqual(res.stop_reason, "landed")
        self.assertLess(res.time, 0.8)

    def test_hookthrough_is_solid_for_body(self):
        world = flat_world()
        world.fill_rect(10, 0, 12, 20, "hookthrough")
        res = simulate(State.standing(0, 0), [move(0, 1)], world, 1)
        self.assertAlmostEqual(res.final.x, 10 - P.half_width, delta=1e-6)

    def test_generic_world_matches_grid(self):
        world = flat_world()
        world.fill_rect(30, 0, 34, 8, "block")
        world.fill_rect(-10, 30, 10, 32, "block")
        inputs = [move(0, 1), jump(0.2), jump(0.6), move(1.2, -1), hook(1.5, direction=(0.3, 1)), unhook(2.2)]
        a = simulate(State.standing(0, 0), inputs, world, 3)
        b = simulate(State.standing(0, 0), inputs, PointOnlyWorld(world), 3)
        self.assertAlmostEqual(a.final.x, b.final.x, delta=0.05)
        self.assertAlmostEqual(a.final.y, b.final.y, delta=0.05)


class ZoneTests(unittest.TestCase):
    def test_kill_zone(self):
        world = flat_world()
        world.fill_rect(10, 0, 12, 2, "kill")
        res = simulate(State.standing(0, 0), [move(0, 1)], world, 2)
        self.assertTrue(res.dead)
        self.assertEqual(res.stop_reason, "kill")

    def test_freeze_zone(self):
        world = flat_world()
        world.fill_rect(10, 0, 12, 2, "freeze")
        res = simulate(State.standing(0, 0), [move(0, 1)], world, 2)
        self.assertTrue(res.frozen)
        self.assertIn("freeze", res.zones)

    def test_named_zone_and_stop_when(self):
        world = flat_world()
        world.fill_rect(20, 0, 22, 8, "finish")
        res = simulate(
            State.standing(0, 0), [move(0, 1)], world, 3, stop_when=lambda s: "finish" in s.zones
        )
        self.assertEqual(res.stop_reason, "stop_when")

    def test_kill_y(self):
        res = simulate(State(x=0, y=10), [], GridWorld(), 3, kill_y=-20)
        self.assertTrue(res.dead)
        self.assertEqual(res.stop_reason, "fell")


class HookTests(unittest.TestCase):
    def test_attaches_and_pulls_up(self):
        world = flat_world()
        world.fill_rect(-4, 30, 4, 34, "block")  # bloco acima: face de baixo em y = 30
        start = State.standing(0, 0)
        res = simulate(start, [hook(0, direction=(0, 1))], world, 2)
        self.assertEqual(len(res.event_times("hook_attach")), 1)
        attach_t = res.event_times("hook_attach")[0]
        self.assertAlmostEqual(attach_t, (30 - start.y) / P.fire_speed, delta=2 / 60)
        anchor = res.final.hook.anchor
        self.assertIsNotNone(anchor)
        self.assertAlmostEqual(anchor[1], 30.0, delta=1e-6)
        # sobe e fica pendurado perto de DragMinDistance abaixo do ponto
        self.assertGreater(res.final.y, 20)
        self.assertLess(30 - res.final.y, P.drag_min_distance + P.hang_damping_margin)
        self.assertLessEqual(res.max_y + P.head_offset, 30 + 1e-6)  # não atravessa o bloco
        self.assertLessEqual(max(abs(s.vy) for s in res.trajectory), P.drag_speed + 5)

    def test_nohook_refuses(self):
        world = flat_world()
        world.fill_rect(-4, 30, 4, 34, "nohook")
        res = simulate(State.standing(0, 0), [hook(0, direction=(0, 1))], world, 1)
        self.assertEqual(res.event_times("hook_attach"), [])
        self.assertEqual(len(res.event_times("hook_refused")), 1)
        self.assertLess(res.max_y, 4)

    def test_out_of_range_misses(self):
        world = flat_world()
        world.fill_rect(-4, 3 + P.hook_range + 2, 4, 60, "block")
        res = simulate(State.standing(0, 0), [hook(0, direction=(0, 1))], world, 1)
        self.assertEqual(res.event_times("hook_attach"), [])
        self.assertEqual(len(res.event_times("hook_miss")), 1)

    def test_hookthrough_is_crossed_by_hook(self):
        world = flat_world()
        world.fill_rect(-4, 14, 4, 16, "hookthrough")
        world.fill_rect(-4, 30, 4, 34, "block")
        res = simulate(State.standing(0, 0), [hook(0, direction=(0, 1))], world, 0.3)
        self.assertEqual(len(res.event_times("hook_attach")), 1)
        self.assertAlmostEqual(res.final.hook.anchor[1], 30.0, delta=1e-6)

    def test_hook_once_only_once(self):
        world = flat_world()
        world.fill_rect(-4, 30, 4, 34, "once")
        res = simulate(
            State.standing(0, 0),
            [hook(0, direction=(0, 1)), unhook(0.3), hook(2.0, direction=(0, 1))],
            world,
            3,
        )
        self.assertEqual(len(res.event_times("hook_attach")), 1)
        self.assertEqual(len(res.event_times("hook_refused")), 1)

    def test_aim_point(self):
        world = flat_world()
        world.fill_rect(20, 20, 24, 24, "block")
        res = simulate(State.standing(0, 0), [hook(0, point=(22, 22))], world, 0.2)
        self.assertEqual(len(res.event_times("hook_attach")), 1)
        ax, ay = res.final.hook.anchor
        self.assertTrue(abs(ax - 20) < 1e-6 or abs(ay - 20) < 1e-6)

    def test_release_keeps_momentum_and_double_jump_allowed(self):
        world = flat_world()
        world.fill_rect(28, 28, 32, 32, "block")
        events = [move(0, 1), jump(0), hook(0.1, point=(30, 30)), unhook(0.4), jump(0.5)]
        res = simulate(State.standing(0, 0), events, world, 3, stop_on_land=True)
        self.assertEqual(len(res.event_times("double_jump")), 1)  # embalo: duplo vale
        released = next(s for s in res.trajectory if s.t > 0.4)
        self.assertTrue(released.momentum)
        self.assertGreater(released.vx, P.air_control_speed)  # embalo acima do controle normal

    def test_no_double_jump_while_attached(self):
        world = flat_world()
        world.fill_rect(-4, 30, 4, 34, "block")
        res = simulate(State.standing(0, 0), [hook(0, direction=(0, 1)), jump(0.5)], world, 1)
        self.assertEqual(res.event_times("double_jump"), [])

    def test_cooldown_and_reattach_recharge_quirk(self):
        world = flat_world()
        world.fill_rect(-30, 40, 30, 44, "block")
        start = State.standing(0, 0)
        events = [
            jump(0),
            jump(0.3),  # gasta o duplo
            hook(0.45, direction=(0, 1)),  # prende: atributo liga → recarga
            unhook(0.8),
            jump(0.95),  # duplo no embalo
            hook(1.05, direction=(0, 1)),  # prende de novo NO embalo: no jogo não recarrega
            unhook(1.3),
            jump(1.45),
        ]
        res = simulate(start, events, world, 1.6)
        self.assertEqual(len(res.event_times("double_jump")), 2)
        res2 = simulate(start, events, world, 1.6, recharge_on_reattach=True)
        self.assertEqual(len(res2.event_times("double_jump")), 3)

    def test_input_state_is_not_mutated(self):
        start = State.standing(0, 0)
        simulate(start, [move(0, 1), jump(0)], flat_world(), 1)
        self.assertEqual(start.x, 0)
        self.assertTrue(start.grounded)


class PureRuleTests(unittest.TestCase):
    def test_saturated_add(self):
        self.assertEqual(saturated_add(-22, 22, 10, 30), 22)
        self.assertEqual(saturated_add(-22, 22, 50, 5), 50)  # não corta embalo
        self.assertEqual(saturated_add(-22, 22, -50, -5), -50)
        self.assertEqual(saturated_add(-22, 22, 50, -5), 45)

    def test_hook_drag(self):
        ticks = 1.0
        accel = P.drag_accel / P.tick_rate
        vx, vy = hook_drag(0, 0, 0, 20, 0, P, ticks)
        self.assertAlmostEqual(vy, accel)
        self.assertAlmostEqual(vx, 0)
        vx, vy = hook_drag(0, 0, 0, -20, 0, P, ticks)
        self.assertAlmostEqual(vy, -accel * P.drag_down_factor)
        vx, vy = hook_drag(0, 0, 20, 0, 1, P, ticks)
        self.assertAlmostEqual(vx, accel * P.drag_assist_factor)
        vx, vy = hook_drag(0, 0, 20, 0, 0, P, ticks)
        self.assertAlmostEqual(vx, accel * P.drag_resist_factor)
        # perto demais: não puxa
        self.assertEqual(hook_drag(3, 4, 0, P.drag_min_distance - 0.1, 0, P, ticks), (3, 4))
        # acima do limite e acelerando: descartado
        self.assertEqual(hook_drag(0, 80, 0, 20, 0, P, ticks), (0, 80))
        # vindo de baixo: para no limite
        vx, vy = hook_drag(0, P.drag_speed - 1, 0, 20, 0, P, ticks)
        self.assertAlmostEqual(math.hypot(vx, vy), P.drag_speed)

    def test_params_from_config(self):
        params = MovementParams.from_config(load_config())
        self.assertAlmostEqual(params.feet_offset, 3.0)
        self.assertAlmostEqual(params.head_offset, 2.5)
        self.assertEqual(params.hook_mode, "DDNet")


if __name__ == "__main__":
    unittest.main()
