"""Números extras de um mapa montado, para o documento da proposta (ADR 0055).

    python -I -X utf8 tools/mapkit/proposals/stats_proposta.py maps/proposta-a/plano.json

Monta o plano de novo, roda o validador (rápido, como o `assemble.py`) e imprime:
- tipos de manobra por rota (mais rápida, jogador médio, mais segura), no mapa todo e só nos trechos do plano
  (sem largada, checkpoints, curvas e degraus gerados pelo montador), com a fatia que usa o gancho;
- erros esperados e manobras < 0,1 s / < 0,2 s na rota do jogador médio;
- conferência da MÃO ÚNICA: manobras das rotas que atravessam uma peça OneWay contra a seta (o validador trata
  mão única como ar; no jogo essa passagem não existe).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.mapkit import validate as V  # noqa: E402
from tools.mapkit.assemble import assemble, plan_library  # noqa: E402

ROUTES = (("fastest", "mais rápida"), ("medium", "jogador médio"), ("safest", "mais segura"))
ARROW = {"Up": (0, 1), "Down": (0, -1), "Left": (-1, 0), "Right": (1, 0)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args(argv)
    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_text(encoding="utf8"))
    asm = assemble(plan, plan_library(plan, plan_path.resolve().parent))
    v = V.validate(asm.tiles, V.Settings.quick(), jobs=args.jobs, stages=asm.stages())
    g = v.graph
    authored = {p.label for p in asm.pieces if p.kind == "trecho"}
    tm = asm.tiles
    traj = v.results.get("trajectories", {})
    for key, name in ROUTES:
        r = v.results["route_objs"].get(key)
        if r is None:
            print(f"{name}: sem rota")
            continue
        edges = [g.edges[ei] for ei in r.edge_ids()]
        for scope, sel in (("mapa todo", edges), ("só trechos", [e for e in edges if g.node_stage(e.src) in authored])):
            ms = [e for e in sel if e.maneuver]
            kinds: dict[str, int] = {}
            for e in ms:
                kinds[e.label] = kinds.get(e.label, 0) + 1
            hook = sum(n for k, n in kinds.items() if "hook" in k)
            print(f"{name} ({scope}): {len(ms)} manobras, gancho {hook} ({hook / max(1, len(ms)):.0%}) · "
                  + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])))
        if key == "medium":
            ms = [e for e in edges if e.maneuver]
            errs = sum(1 / V.p_success(e.w_eff) - 1 for e in ms)
            print(f"  jogador médio: erros esperados {errs:.1f}; janelas < 0,1 s: {sum(1 for e in ms if e.w_eff < 0.1)}; "
                  f"< 0,2 s: {sum(1 for e in ms if e.w_eff < 0.2)}; tempo esperado {sum(V.cost_medium(e) for e in edges):.1f} s")
        bad = 0
        crossed = 0
        for ei in r.edge_ids():
            pts = traj.get(ei, ())
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cell = tm.cell_at(x1, y1)
                if tm.get(*cell) != "OneWay":
                    continue
                crossed += 1
                ax, ay = ARROW.get(tm.directions.get(cell, "Up"), (0, 1))
                if (x1 - x0) * ax + (y1 - y0) * ay < -1e-6:
                    bad += 1
        print(f"  mão única: {crossed} pontos da trajetória dentro de OneWay, {bad} contra a seta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
