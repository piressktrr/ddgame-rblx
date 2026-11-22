"""Tabela de medidas do movimento e regras de desenho de mapa (ADR 0052, etapa 1).

Roda o simulador (`tools/mapkit/physics.py`) em cenários limpos, com os números do
`src/shared/Config.luau`, e grava:
- `maps/metrics.json`: medidas, regras e o hash do Config usado;
- `memory-palace/04-game-design/MEDIDAS_DO_MAPA.md`: o mesmo em PT-BR, para gente.

Regenerar (a partir da raiz do repositório):
    python -I -X utf8 tools/mapkit/metrics.py
    (ou, sem o -I: python -X utf8 -m tools.mapkit.metrics)
Conferir se os arquivos estão em dia, sem gravar: acrescente `--check`.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # Rodado como script (python -I tools/mapkit/metrics.py): a raiz do repo entra no sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.mapkit.luau_config import REPO_ROOT, ConfigData, load_config  # noqa: E402
from tools.mapkit.physics import (  # noqa: E402
    AnchorWorld,
    GridWorld,
    MovementParams,
    SimResult,
    State,
    hook,
    jump,
    move,
    simulate,
    unhook,
)

JSON_PATH = REPO_ROOT / "maps" / "metrics.json"
MD_PATH = REPO_ROOT / "memory-palace" / "04-game-design" / "MEDIDAS_DO_MAPA.md"
CELL = 2.0  # studs: célula do MapBuilder (UNIT do plugin)
ASPECT = 16 / 9
LEVELS = (-24, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20)  # desníveis medidos (studs, múltiplos de 4)
COMFORT = 0.75  # fração do máximo considerada confortável
EXPERT = 0.9  # fração do máximo para trechos difíceis
FRAME = 1 / 60
SCHEMA_VERSION = 1


# --------------------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------------------


def floor_to(value: float, grid: float) -> float:
    return math.floor(value / grid + 1e-9) * grid


def ceil_to(value: float, grid: float) -> float:
    return math.ceil(value / grid - 1e-9) * grid


def r3(value: float) -> float:
    return round(float(value), 3)


def descending_crossing(result: SimResult, level: float, feet_offset: float) -> float | None:
    """X do root quando os pés descem até `level` (interpolado), ou None."""
    traj = result.trajectory
    for a, b in zip(traj, traj[1:]):
        fa, fb = a.y - feet_offset, b.y - feet_offset
        if b.vy < 0 and fa >= level > fb:
            k = (fa - level) / (fa - fb)
            return a.x + (b.x - a.x) * k
    return None


def ledge_world() -> GridWorld:
    """Chão só em x <= 0 (borda em x = 0, topo em y = 0); depois, vazio."""
    world = GridWorld(CELL)
    world.fill_rect(-400, -8, 0, 0, "block")
    return world


def edge_start(p: MovementParams) -> State:
    """Em pé na borda: a traseira da caixa encosta em x = 0 (último instante apoiado)."""
    return State.standing(p.half_width - 1e-6, 0.0, p)


# --------------------------------------------------------------------------------------------------
# Pulo
# --------------------------------------------------------------------------------------------------


def jump_basics(p: MovementParams) -> dict[str, Any]:
    flat = GridWorld(CELL)
    flat.fill_rect(-400, -8, 400, 0, "block")
    start = State.standing(0.0, 0.0, p)
    res = simulate(start, [jump(0)], flat, 3, params=p, stop_on_land=True)
    height = max(s.y for s in res.trajectory) - start.y
    analytic = p.jump_power**2 / (2 * p.gravity)
    return {
        "jump_height": r3(height),
        "jump_height_analytic": r3(analytic),
        "jump_air_time": r3(res.time),
        "jump_air_time_analytic": r3(2 * p.jump_power / p.gravity),
        "jump_time_to_apex": r3(p.jump_power / p.gravity),
    }


def double_jump_height(p: MovementParams) -> dict[str, Any]:
    flat = GridWorld(CELL)
    flat.fill_rect(-400, -8, 400, 0, "block")
    start = State.standing(0.0, 0.0, p)
    best = (-1.0, 0.0, 0.0)
    first = math.ceil(p.double_jump_min_air_time / FRAME)
    for k in range(first, 70):
        t_dj = k * FRAME
        res = simulate(start, [jump(0), jump(t_dj)], flat, 4, params=p, stop_on_land=True)
        if not res.event_times("double_jump"):
            continue
        height = max(s.y for s in res.trajectory) - start.y
        if height > best[0]:
            best = (height, t_dj, res.time)
    return {
        "double_jump_height": r3(best[0]),
        "double_jump_height_analytic": r3(
            p.jump_power**2 / (2 * p.gravity) + p.double_jump_velocity**2 / (2 * p.gravity)
        ),
        "double_jump_best_time_for_height": r3(best[1]),
        "double_jump_air_time_at_best_height": r3(best[2]),
        "double_jump_gain": r3(p.double_jump_velocity**2 / (2 * p.gravity)),
    }


def running_jump(p: MovementParams, dj_time: float | None) -> SimResult:
    events = [move(0, 1), jump(0)]
    if dj_time is not None:
        events.append(jump(dj_time))
    return simulate(edge_start(p), events, ledge_world(), 5, params=p, kill_y=-200)


def jump_reach(p: MovementParams) -> dict[str, Any]:
    """Vão máximo (borda a borda) para cada desnível, com pulo e com pulo + pulo duplo."""
    plain = running_jump(p, None)
    first = math.ceil(p.double_jump_min_air_time / FRAME)
    dj_runs = [(k * FRAME, running_jump(p, k * FRAME)) for k in range(first, 140)]
    rows = []
    for level in LEVELS:
        x = descending_crossing(plain, level, p.feet_offset)
        gap = None if x is None else x + p.half_width
        best_dj: tuple[float, float] | None = None
        for t_dj, res in dj_runs:
            if not res.event_times("double_jump"):
                continue
            xd = descending_crossing(res, level, p.feet_offset)
            if xd is None:
                continue
            # o cruzamento tem de ser depois do pulo duplo (senão é o mesmo do pulo simples)
            gap_dj = xd + p.half_width
            if best_dj is None or gap_dj > best_dj[0]:
                best_dj = (gap_dj, t_dj)
        rows.append(
            {
                "level": level,
                "jump_gap": None if gap is None else r3(gap),
                "double_jump_gap": None if best_dj is None else r3(best_dj[0]),
                "double_jump_time": None if best_dj is None else r3(best_dj[1]),
            }
        )
    return {"rows": rows}


# --------------------------------------------------------------------------------------------------
# Gancho
# --------------------------------------------------------------------------------------------------


def hook_climb(p: MovementParams, height: float, step: int = 2) -> dict[str, Any]:
    """Ponto de gancho bem acima (a `height` studs do root): altura máxima dos pés soltando na hora
    certa e dando o pulo duplo no topo, e onde o corpo fica se segurar."""
    floor = GridWorld(CELL)
    floor.fill_rect(-400, -8, 400, 0, "block")
    start = State.standing(0.0, 0.0, p)
    radius = 0.5
    anchor = (0.0, start.y + height + radius)
    world = AnchorWorld(floor, [anchor], radius)

    held = simulate(start, [hook(0, point=anchor)], world, 4, params=p)
    hang_root_below = anchor[1] - radius - held.final.y

    def search(with_dj: bool) -> tuple[float, float]:
        best = (-1.0, 0.0)
        for k in range(3, 150, step):
            t_r = k * FRAME
            st = {"dj": False}

            def ctrl(s: State, t: float, t_r: float = t_r, st=st):
                if with_dj and t >= t_r and not st["dj"] and s.vy <= 0 and not s.grounded:
                    st["dj"] = True
                    return [jump(t)]
                return None

            res = simulate(
                start,
                [hook(0, point=anchor), unhook(t_r)],
                world,
                t_r + 3,
                params=p,
                controller=ctrl,
                stop_on_land=True,
            )
            if not res.event_times("hook_attach"):
                continue
            rise = max(s.y for s in res.trajectory) - start.y
            if rise > best[0]:
                best = (rise, t_r)
        return best

    no_dj = search(False)
    best = search(True)
    return {
        "anchor_height": r3(height),
        "hang_root_below_anchor": r3(hang_root_below),
        "hang_feet_below_anchor": r3(hang_root_below + p.feet_offset),
        "max_feet_rise_no_double_jump": r3(no_dj[0]),
        "release_time_no_double_jump": r3(no_dj[1]),
        "max_feet_rise_with_double_jump": r3(best[0]),
        "release_time_with_double_jump": r3(best[1]),
    }


def hook_gap(p: MovementParams, max_up: float, grid: float, quick: bool = False) -> dict[str, Any]:
    """Vão máximo: corre, pula na borda, prende num ponto à frente (dentro do alcance e da tela),
    solta, segue no embalo segurando D e dá o pulo duplo perto do pouso. O ponto de gancho é um bloco
    (DefaultGrid x DefaultGrid) com o centro a Range - 1 do root na hora do disparo."""
    start = edge_start(p)
    dist = p.hook_range - 1.0
    angles = (0, 20, 40, 60) if quick else (0, 10, 20, 30, 40, 50, 60, 70)
    fire_times = (0.2,) if quick else (0.0, 0.2, 0.45)
    release_step = 6 if quick else 3
    best: dict[str, Any] | None = None
    for angle in angles:
        theta = math.radians(angle)
        for t_f in fire_times:
            root_x = start.x + p.walk_speed * t_f
            root_y = start.y + p.jump_power * t_f - 0.5 * p.gravity * t_f * t_f
            up = dist * math.sin(theta)
            if up > max_up:
                continue
            anchor = (root_x + dist * math.cos(theta), root_y + up)
            world = ledge_world()
            half = grid / 2
            world.fill_rect(anchor[0] - half, anchor[1] - half, anchor[0] + half, anchor[1] + half, "block")
            for k in range(4, 160, release_step):
                t_r = t_f + k * FRAME
                st = {"dj": False, "release_v": 0.0}

                def ctrl(s: State, t: float, t_r: float = t_r, st=st):
                    if abs(t - t_r) < 1e-9:
                        st["release_v"] = math.hypot(s.vx, s.vy)
                    if t > t_r and not st["dj"] and s.vy < 0 and s.y - p.feet_offset < 1.0:
                        st["dj"] = True
                        return [jump(t)]
                    return None

                res = simulate(
                    start,
                    [move(0, 1), jump(0), hook(t_f, point=anchor), unhook(t_r)],
                    world,
                    t_r + 4,
                    params=p,
                    controller=ctrl,
                    kill_y=-40,
                    stop_when=lambda s, st=st: st["dj"] and s.vy < 0 and s.y - p.feet_offset < -1,
                )
                if not res.event_times("hook_attach") or not res.event_times("double_jump"):
                    continue
                x = descending_crossing(res, 0.0, p.feet_offset)
                if x is None:
                    continue
                gap = x + p.half_width
                if best is None or gap > best["gap"]:
                    best = {
                        "gap": r3(gap),
                        "anchor_angle_deg": angle,
                        "anchor_dx_from_edge": r3(anchor[0]),
                        "anchor_dy_from_ledge": r3(anchor[1]),
                        "fire_time": r3(t_f),
                        "release_time": r3(t_r),
                        "release_speed": r3(st["release_v"]),
                        "max_speed": r3(max(math.hypot(s.vx, s.vy) for s in res.trajectory)),
                        "max_horizontal_speed": r3(max(abs(s.vx) for s in res.trajectory)),
                    }
    return best or {}


def _wall_climb_ok(p: MovementParams, d: float, height: float, t_r: float, with_dj: bool) -> bool | None:
    """Sobe numa parede de `height` (topo) prendendo na face, 1 stud abaixo do topo? None = fora do
    alcance."""
    wall_x = 100.0
    world = GridWorld(CELL)
    world.fill_rect(-100, -8, 400, 0, "block")
    world.fill_rect(wall_x, 0, wall_x + 60, height, "block")
    start = State.standing(wall_x - max(d, p.half_width) - 1e-6, 0.0, p)
    aim_point = (wall_x + 0.5, height - 1.0)
    if math.hypot(aim_point[0] - start.x, aim_point[1] - start.y) > p.hook_range:
        return None
    st = {"dj": False}

    def ctrl(s: State, t: float):
        if with_dj and t >= t_r and not st["dj"] and s.vy <= 0 and not s.grounded:
            st["dj"] = True
            return [jump(t)]
        return None

    res = simulate(
        start,
        [move(0, 1), hook(0, point=aim_point), unhook(t_r)],
        world,
        t_r + 3,
        params=p,
        controller=ctrl,
        stop_when=lambda s: s.grounded and s.x - p.half_width > wall_x and s.y - p.feet_offset >= height - 0.1,
    )
    return res.stop_reason == "stop_when"


def hook_wall_climb(p: MovementParams, max_up: float, quick: bool = False) -> dict[str, Any]:
    """Parede mais alta que se sobe com UM gancho (prende na face perto do topo, solta, passa por
    cima segurando D), para algumas distâncias do pé da parede. O ponto preso fica até `max_up`
    acima do root (tela)."""
    rows = []
    step = 6 if quick else 3
    for d in (2, 12, 20):
        best = None
        lo, hi = 0, 30  # alturas em células: 2*lo..2*hi
        while lo < hi:
            mid = (lo + hi + 1) // 2
            height = mid * CELL
            if height - 1.0 - p.feet_offset > max_up:
                hi = mid - 1
                continue
            ok = False
            for with_dj in (False, True):
                for k in range(3, 120, step):
                    result = _wall_climb_ok(p, d, height, k * FRAME, with_dj)
                    if result is None:
                        break
                    if result:
                        ok = True
                        break
                if ok:
                    break
            if ok:
                lo = mid
                best = height
            else:
                hi = mid - 1
        rows.append({"distance_from_wall": d, "max_wall_height": best})
    return {"rows": rows, "max_wall_height": max((r["max_wall_height"] or 0) for r in rows)}


# --------------------------------------------------------------------------------------------------
# Câmera e queda
# --------------------------------------------------------------------------------------------------


def camera_view(cfg: ConfigData, p: MovementParams) -> dict[str, Any]:
    cam = cfg["Camera"]
    distance = float(cam["Distance"])
    fov = math.radians(float(cam["FieldOfView"]))
    height = 2 * distance * math.tan(fov / 2)
    width = height * ASPECT
    cam_h = float(cam["Height"])
    ahead = float(cam["LookAhead"])
    front_face = distance - float(cfg["MapElements"]["BlockDepth"]) / 2
    return {
        "aspect": "16:9",
        "visible_height": r3(height),
        "visible_width": r3(width),
        "visible_up_from_root": r3(height / 2 + cam_h),
        "visible_down_from_root": r3(height / 2 - cam_h),
        "visible_side_stopped": r3(width / 2),
        "visible_ahead_running": r3(width / 2 + ahead),
        "visible_behind_running": r3(width / 2 - ahead),
        "front_face_visible_height": r3(2 * front_face * math.tan(fov / 2)),
        "smoothing": float(cam["Smoothing"]),
        "note": "FOV vertical; área no plano Z do jogo (a face da frente dos blocos fica mais perto).",
    }


def fall_table(cfg: ConfigData, p: MovementParams, camera: dict[str, Any]) -> dict[str, Any]:
    smoothing = float(cfg["Camera"]["Smoothing"])
    rows = []
    for h in (12, 24, 40, 60, 100, 160):
        v = math.sqrt(2 * p.gravity * h)
        lag = v / smoothing
        rows.append(
            {
                "height": h,
                "speed": r3(v),
                "time": r3(math.sqrt(2 * h / p.gravity)),
                "camera_lag": r3(lag),
                "visible_below_feet": r3(camera["visible_down_from_root"] - lag - p.feet_offset),
            }
        )
    return {
        "fall_damage": False,
        "note": (
            "Sem dano de queda: nenhum código do jogo tira vida por queda e o Humanoid do Roblox não "
            "tem dano de queda. Só matam a zona Kill e cair abaixo do FallenPartsDestroyHeight do place."
        ),
        "rows": rows,
    }


# --------------------------------------------------------------------------------------------------
# Tudo junto
# --------------------------------------------------------------------------------------------------


def units(studs: float | None, grid: float) -> dict[str, Any] | None:
    if studs is None:
        return None
    return {"studs": r3(studs), "blocks": r3(studs / grid), "cells": r3(studs / CELL)}


def compute_metrics(cfg: ConfigData | None = None, quick: bool = False) -> dict[str, Any]:
    cfg = cfg or load_config()
    p = MovementParams.from_config(cfg)
    grid = float(cfg["MapElements"]["DefaultGrid"])
    camera = camera_view(cfg, p)
    hook_up_limit = min(p.hook_range, camera["visible_up_from_root"])
    metrics: dict[str, Any] = {
        "jump": {**jump_basics(p), **double_jump_height(p)},
        "reach": jump_reach(p),
        "hook_climb_range": hook_climb(p, p.hook_range - 0.5, step=4 if quick else 2),
        "hook_climb_on_screen": hook_climb(
            p, floor_to(hook_up_limit - 1.0, CELL), step=4 if quick else 2
        ),
        "hook_gap": hook_gap(p, hook_up_limit - 1.0, grid, quick=quick),
        "hook_wall_climb": hook_wall_climb(p, hook_up_limit, quick=quick),
        "camera": camera,
        "fall": fall_table(cfg, p, camera),
        "speeds": {
            "walk": p.walk_speed,
            "air_control": p.air_control_speed,
            "drag_max": p.drag_speed,
            "max_swing": p.max_swing_speed,
            "hook_fire": p.fire_speed,
            "jump_up": p.jump_power,
            "double_jump_up": p.double_jump_velocity,
        },
        "body": {
            "width": p.box_width,
            "height": p.box_height,
            "feet_below_root": r3(p.feet_offset),
            "head_above_root": r3(p.head_offset),
        },
        "hook": {
            "range": p.hook_range,
            "cooldown": p.hook_cooldown,
            "drag_min_distance": p.drag_min_distance,
            "fire_time_at_range": r3(p.hook_range / p.fire_speed),
            "on_screen_up": r3(hook_up_limit),
            "on_screen_down": r3(min(p.hook_range, camera["visible_down_from_root"])),
            "on_screen_side": r3(min(p.hook_range, camera["visible_behind_running"])),
        },
    }
    metrics["rules"] = design_rules(metrics, p, grid)
    return {
        "schema": SCHEMA_VERSION,
        "generated_by": "tools/mapkit/metrics.py",
        "config": {
            "path": "src/shared/Config.luau",
            "sha256": cfg.sha256,
            "grid": grid,
            "cell": CELL,
            "hook_mode": p.hook_mode,
        },
        "metrics": metrics,
    }


def design_rules(m: dict[str, Any], p: MovementParams, grid: float) -> list[dict[str, Any]]:
    """Regras de desenho com folga, em studs e arredondadas para a grade de blocos."""
    jump_h = m["jump"]["jump_height"]
    dj_h = m["jump"]["double_jump_height"]
    level0 = next(r for r in m["reach"]["rows"] if r["level"] == 0)
    gap_j, gap_dj = level0["jump_gap"], level0["double_jump_gap"]
    cam = m["camera"]
    hk = m["hook"]
    safe_range = floor_to(EXPERT * p.hook_range, grid)
    hang = m["hook_climb_on_screen"]["hang_root_below_anchor"]
    chain = floor_to(EXPERT * math.sqrt(max(safe_range**2 - hang**2, 0)), grid)

    def rule(rule_id: str, op: str, studs: float, text: str) -> dict[str, Any]:
        return {"id": rule_id, "op": op, **(units(studs, grid) or {}), "text": text}

    return [
        rule(
            "step_jump_comfort",
            "<=",
            floor_to(COMFORT * jump_h, grid),
            "Degrau (só pulo, sem gancho): confortável.",
        ),
        rule(
            "step_jump_max",
            "<=",
            floor_to(jump_h - 0.5, CELL),
            "Degrau máximo só com pulo (na grade de células; acima disso precisa do pulo duplo).",
        ),
        rule(
            "step_double_jump_comfort",
            "<=",
            floor_to(COMFORT * dj_h, grid),
            "Degrau com pulo duplo: confortável.",
        ),
        rule(
            "step_double_jump_max",
            "<=",
            floor_to(dj_h - 0.5, CELL),
            "Degrau máximo com pulo duplo bem cronometrado (no topo do 1º pulo).",
        ),
        rule(
            "step_needs_hook",
            ">=",
            ceil_to(dj_h + 1.0, grid),
            "Degrau a partir do qual só se sobe com gancho (impossível com os dois pulos).",
        ),
        rule(
            "gap_jump_comfort",
            "<=",
            floor_to(COMFORT * gap_j, grid),
            "Vão no mesmo nível só com pulo: confortável (borda a borda).",
        ),
        rule(
            "gap_jump_max",
            "<=",
            floor_to(EXPERT * gap_j, grid),
            "Vão no mesmo nível só com pulo: difícil (pular quase na borda).",
        ),
        rule(
            "gap_double_jump_comfort",
            "<=",
            floor_to(COMFORT * gap_dj, grid),
            "Vão no mesmo nível com pulo duplo: confortável.",
        ),
        rule(
            "gap_double_jump_max",
            "<=",
            floor_to(EXPERT * gap_dj, grid),
            "Vão no mesmo nível com pulo duplo: difícil (duplo tarde, perto do pouso).",
        ),
        rule(
            "gap_needs_hook",
            ">=",
            ceil_to(gap_dj + 2.0, grid),
            "Vão a partir do qual só se passa com gancho (ou embalo de gancho).",
        ),
        rule(
            "gap_hook_comfort",
            "<=",
            floor_to(0.5 * m["hook_gap"]["gap"], grid),
            "Vão com 1 gancho + embalo + pulo duplo: confortável (metade do máximo medido).",
        ),
        rule(
            "wall_one_hook_max",
            "<=",
            floor_to(EXPERT * m["hook_wall_climb"]["max_wall_height"], grid),
            "Parede que se sobe com 1 gancho (prende na face perto do topo e passa por cima).",
        ),
        rule(
            "wall_needs_two_hooks",
            ">",
            float(m["hook_wall_climb"]["max_wall_height"]),
            "Parede mais alta que isto precisa de 2 ganchos (soltar e prender de novo no ar).",
        ),
        rule(
            "hook_target_distance",
            "<=",
            safe_range,
            "Distância do root até o ponto de gancho (alcance com folga).",
        ),
        rule(
            "hook_target_up",
            "<=",
            floor_to(hk["on_screen_up"] - 3.0, grid),
            "Ponto de gancho acima do jogador: no máximo isto, para ficar na tela com folga.",
        ),
        rule(
            "hook_target_down",
            "<=",
            floor_to(hk["on_screen_down"] - 3.0, grid),
            "Ponto de gancho abaixo do jogador: no máximo isto (a câmera mostra menos para baixo).",
        ),
        rule(
            "hook_chain_spacing",
            "<=",
            chain,
            "Espaço horizontal entre pontos de gancho seguidos na mesma altura (pendurado no anterior).",
        ),
        rule(
            "ceiling_walk_min",
            ">=",
            ceil_to(p.box_height + 0.5, grid),
            "Altura livre mínima para passar andando (corpo de 5,5).",
        ),
        rule(
            "ceiling_jump_free",
            ">=",
            ceil_to(p.box_height + jump_h, grid),
            "Altura livre para pular sem bater a cabeça (pulo inteiro).",
        ),
        rule(
            "corridor_width_min",
            ">=",
            ceil_to(p.box_width + 0.5, grid),
            "Largura mínima de poço/corredor vertical (corpo de 2; 1 bloco).",
        ),
        rule(
            "shaft_width_hook",
            ">=",
            2 * grid,
            "Largura confortável de poço para subir com gancho/pulos (balanço e erro de mira).",
        ),
        rule(
            "hang_clearance",
            ">=",
            ceil_to(hang + p.feet_offset + 1.0, grid),
            "Do ponto de gancho no teto até o chão, para ficar pendurado sem encostar os pés.",
        ),
    ]


# --------------------------------------------------------------------------------------------------
# Saída
# --------------------------------------------------------------------------------------------------


def br(value: Any, digits: int = 1) -> str:
    """Número no formato PT-BR (vírgula decimal)."""
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        text = f"{value:.{digits}f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text.replace(".", ",")
    return str(value)


def render_markdown(data: dict[str, Any]) -> str:
    m = data["metrics"]
    cfg = data["config"]
    grid = cfg["grid"]
    j = m["jump"]
    cam = m["camera"]
    hk = m["hook"]
    hc = m["hook_climb_range"]
    hs = m["hook_climb_on_screen"]
    hg = m["hook_gap"]
    sp = m["speeds"]

    def u(studs: float | None) -> str:
        if studs is None:
            return "—"
        return f"{br(studs, 2)} studs · {br(studs / grid, 2)} blocos · {br(studs / cfg['cell'], 2)} células"

    lines: list[str] = []
    add = lines.append
    add("# Medidas do mapa (gerado)")
    add("")
    add("> **Arquivo gerado** por `tools/mapkit/metrics.py`. Não edite à mão: mude o `Config.luau`")
    add("> ou o simulador e regenere. ADR 0052, etapa 1.")
    add(">")
    add(f"> Config: `{cfg['path']}` · sha256 `{cfg['sha256'][:16]}…` · gancho modo `{cfg['hook_mode']}`.")
    add(
        f"> Unidades: studs; **bloco** = `MapElements.DefaultGrid` = {br(grid)} studs; "
        f"**célula** do MapBuilder = {br(cfg['cell'])} studs."
    )
    add("")
    add("## Como regenerar")
    add("")
    add("Na raiz do repositório:")
    add("")
    add("```")
    add("python -I -X utf8 tools/mapkit/metrics.py           # grava maps/metrics.json e este arquivo")
    add("python -I -X utf8 tools/mapkit/metrics.py --check   # só confere se estão em dia")
    add("python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .")
    add("```")
    add("")
    add("Os números saem do simulador (`tools/mapkit/physics.py`), que porta o código do movimento e do")
    add("gancho (veja as simplificações no topo dele). Os máximos são **teóricos** (entrada perfeita);")
    add("as regras abaixo já têm folga.")
    add("")
    add("## Pulo")
    add("")
    add("| Medida | Valor |")
    add("|---|---|")
    add(f"| Altura do pulo (pés) | {u(j['jump_height'])} (fórmula JumpPower²/2g: {br(j['jump_height_analytic'], 2)}) |")
    add(f"| Tempo até o topo | {br(j['jump_time_to_apex'], 2)} s |")
    add(f"| Tempo no ar (mesmo nível) | {br(j['jump_air_time'], 2)} s (fórmula: {br(j['jump_air_time_analytic'], 2)} s) |")
    add(
        f"| Altura com pulo duplo no topo | {u(j['double_jump_height'])} "
        f"(duplo em t = {br(j['double_jump_best_time_for_height'], 2)} s; ganho do duplo {br(j['double_jump_gain'], 2)}) |"
    )
    add(f"| Tempo no ar com duplo no topo | {br(j['double_jump_air_time_at_best_height'], 2)} s |")
    add("")
    add("### Vão máximo por desnível (borda a borda, correndo e pulando na borda)")
    add("")
    add("Desnível = altura do lado de chegada menos a do lado de partida (positivo = subindo).")
    add("O pulo duplo do alcance máximo é tardio (perto do pouso), não no topo.")
    add("")
    add("| Desnível (studs / blocos) | Só pulo | Pulo + duplo | Duplo em t = |")
    add("|---|---|---|---|")
    for row in m["reach"]["rows"]:
        add(
            f"| {br(row['level'])} / {br(row['level'] / grid, 2)} | {br(row['jump_gap'])} "
            f"| {br(row['double_jump_gap'])} | {br(row['double_jump_time'], 2)} s |"
        )
    add("")
    add("## Gancho")
    add("")
    add("| Medida | Valor |")
    add("|---|---|")
    add(f"| Alcance (`Hook.Range`, do root) | {u(hk['range'])} |")
    add(f"| Tempo de voo até o alcance | {br(hk['fire_time_at_range'], 3)} s (FireSpeed {br(sp['hook_fire'])}) |")
    add(f"| Recarga entre prender | {br(hk['cooldown'], 2)} s |")
    add(
        f"| Pendurado (segurando) | root {br(hs['hang_root_below_anchor'], 2)} abaixo do ponto; pés "
        f"{br(hs['hang_feet_below_anchor'], 2)} abaixo |"
    )
    add(
        f"| Subida com 1 gancho a {br(hc['anchor_height'])} acima (no alcance) | pés sobem até "
        f"{br(hc['max_feet_rise_no_double_jump'])} sem duplo · {br(hc['max_feet_rise_with_double_jump'])} "
        f"com duplo no topo |"
    )
    add(
        f"| Subida com 1 gancho a {br(hs['anchor_height'])} acima (limite da tela) | pés sobem até "
        f"{br(hs['max_feet_rise_no_double_jump'])} sem duplo · {br(hs['max_feet_rise_with_double_jump'])} "
        f"com duplo no topo |"
    )
    for row in m["hook_wall_climb"]["rows"]:
        add(
            f"| Parede subida com 1 gancho, saindo a {br(row['distance_from_wall'])} do pé dela "
            f"| até {br(row['max_wall_height'])} de altura |"
        )
    if hg:
        add(
            f"| Vão máximo com gancho + soltar + embalo + duplo | {u(hg['gap'])} (ponto a "
            f"{br(hg['anchor_angle_deg'])}°, solta em t = {br(hg['release_time'], 2)} s a "
            f"{br(hg['release_speed'])} studs/s) |"
        )
    add("")
    add("As duas \"subidas com 1 gancho\" usam um ponto solto (sem bloco para o corpo bater): é o teto")
    add("otimista de altura. A parede e o vão usam blocos de verdade (o vão: um bloco de gancho a")
    add("Range - 1 do jogador no disparo). Paredes ficam limitadas pelo alcance e pela tela, não pela")
    add("força do puxão. O embalo segurando D no ar não perde velocidade (o controle do DDNet não corta")
    add("velocidade acima do limite), por isso o vão com gancho é bem maior que o do pulo.")
    add("")
    add("## Câmera (16:9) e alvo do gancho na tela")
    add("")
    add("| Medida | Valor |")
    add("|---|---|")
    add(f"| Área visível no plano | {br(cam['visible_width'])} × {br(cam['visible_height'])} studs (largura × altura) |")
    add(f"| Acima do root | {br(cam['visible_up_from_root'])} studs (`Camera.Height` sobe o centro) |")
    add(f"| Abaixo do root | {br(cam['visible_down_from_root'])} studs |")
    add(
        f"| Para os lados | {br(cam['visible_side_stopped'])} parado · {br(cam['visible_ahead_running'])} à frente "
        f"e {br(cam['visible_behind_running'])} atrás correndo (LookAhead) |"
    )
    add(f"| Altura visível na face da frente dos blocos | {br(cam['front_face_visible_height'])} studs |")
    add(
        f"| Gancho na tela | até {br(hk['on_screen_up'])} acima, {br(hk['on_screen_down'])} abaixo, "
        f"{br(hk['on_screen_side'])} para os lados (alcance {br(hk['range'])}) |"
    )
    add("")
    add("Para cima o alcance (40) passa da borda da tela: um ponto a 40 bem acima fica fora da tela.")
    add("")
    add("## Queda")
    add("")
    add(m["fall"]["note"])
    add("")
    add("| Altura da queda | Velocidade | Tempo | Atraso da câmera | Visível abaixo dos pés |")
    add("|---|---|---|---|---|")
    for row in m["fall"]["rows"]:
        add(
            f"| {br(row['height'])} | {br(row['speed'])} studs/s | {br(row['time'], 2)} s "
            f"| {br(row['camera_lag'])} | {br(row['visible_below_feet'])} |"
        )
    add("")
    add("## Velocidades (studs/s)")
    add("")
    add("| Andar | Controle no ar (gancho/embalo) | Puxão máx. (DragSpeed) | Limite do balanço | Pulo | Pulo duplo |")
    add("|---|---|---|---|---|---|")
    add(
        f"| {br(sp['walk'])} | {br(sp['air_control'])} | {br(sp['drag_max'])} | {br(sp['max_swing'])} "
        f"| {br(sp['jump_up'])} | {br(sp['double_jump_up'])} |"
    )
    if hg:
        add("")
        add(
            f"Embalo medido no melhor vão com gancho: até {br(hg['max_horizontal_speed'])} studs/s na horizontal."
        )
    add("")
    add("## Regras de desenho (com folga)")
    add("")
    add("| Regra | Valor | Blocos | Células |")
    add("|---|---|---|---|")
    for rule in m["rules"]:
        add(
            f"| {rule['text']} (`{rule['id']}`) | {rule['op']} {br(rule['studs'])} studs "
            f"| {br(rule['blocks'], 2)} | {br(rule['cells'], 2)} |"
        )
    add("")
    add(f"Folga: \"confortável\" = {br(COMFORT * 100)}% do máximo; \"difícil\" = {br(EXPERT * 100)}%; tudo")
    add("arredondado para baixo na grade de blocos (para cima nos mínimos).")
    add("")
    add("## Limites do simulador (resumo)")
    add("")
    add("- Um jogador só: sem gancho em jogador, martelo, empurrão nem modo solo.")
    add("- Humanoid fora do gancho chega à velocidade de andar na hora, no chão e no ar; sem subida")
    add("  automática de degrau baixo (o Humanoid real sobe quinas pequenas) e sem rampas.")
    add("- Corpo = caixa 2 × 5,5 sem atrito nem quique; mão única é atravessável; zonas pela grade.")
    add("- Prender de novo durante o embalo não devolve o pulo duplo (igual ao jogo hoje: a recarga vem")
    add("  da mudança do atributo `HookActive`, que já está ligado no embalo).")
    add("- Detalhes no topo de `tools/mapkit/physics.py`.")
    add("")
    return "\n".join(lines)


def build_outputs(quick: bool = False) -> tuple[str, str]:
    data = compute_metrics(quick=quick)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n", render_markdown(data)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    json_text, md_text = build_outputs()
    if "--check" in args:
        stale = [
            str(path.relative_to(REPO_ROOT))
            for path, text in ((JSON_PATH, json_text), (MD_PATH, md_text))
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        if stale:
            print("Desatualizado:", ", ".join(stale))
            return 1
        print("Medidas em dia.")
        return 0
    JSON_PATH.write_text(json_text, encoding="utf-8", newline="\n")
    MD_PATH.write_text(md_text, encoding="utf-8", newline="\n")
    print(f"Gravado: {JSON_PATH.relative_to(REPO_ROOT)} e {MD_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
