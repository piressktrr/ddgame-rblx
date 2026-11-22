"""Mostra, manobra por manobra, as rotas do validador num trecho (para desenhar trechos de proposta).

    python -I -X utf8 tools/mapkit/proposals/inspect_chunk.py maps/trechos/p-s1-escadaria.json [--route safest]

Imprime, para cada rota (mais rápida, jogador médio, mais segura), cada manobra com rótulo, tempo, janela
refinada e de onde para onde (em blocos do trecho: x/4, pés/4). Ajuda a achar a manobra que define a
dificuldade medida (a menor janela da rota mais segura) e a ver se a rota passa por mão única no sentido certo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.mapkit.chunks import Chunk, validate_chunk  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--route", action="append", help="fastest/medium/safest (padrão: as três)")
    args = ap.parse_args(argv)
    c = Chunk.load(args.path)
    rep = validate_chunk(c)
    v = rep.validation
    print(rep.summary())
    for p in rep.problems:
        print("  ", p)
    for ln in rep.lanes:
        print(f"  faixa {ln['id']}: ok={ln['ok']} t={ln.get('time', 0):.2f} p_clean={ln.get('p_clean', 0):.2f} minwin={ln.get('min_window', 0):.2f}")
    if v is None:
        return 1
    g = v.graph
    fo = g.geo.params.feet_offset
    for key in args.route or ("fastest", "medium", "safest"):
        r = v.results["route_objs"].get(key)
        if r is None:
            print(f"[{key}] sem rota")
            continue
        print(f"[{key}]")
        for ei in r.edge_ids():
            e = g.edges[ei]
            a, b = g.nodes[e.src], g.nodes[e.dst]
            if not e.maneuver and e.label == "walk" and abs(a.y - b.y) < 0.1:
                continue
            anc = " ".join(f"({x / 4:.1f},{y / 4:.1f})" for x, y in e.anchors)
            print(
                f"  {e.label:14s} t={e.time:5.2f} w={e.w_eff:5.2f} fam={e.window:5.2f}  "
                f"({a.x / 4:5.1f},{(a.y - fo) / 4:4.1f}) -> ({b.x / 4:5.1f},{(b.y - fo) / 4:4.1f}) {anc}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
