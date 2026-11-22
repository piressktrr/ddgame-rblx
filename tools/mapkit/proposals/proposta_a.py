"""Gerador dos trechos da PROPOSTA A do mapa novo (ADR 0052 etapa 4, ADR 0055: o Claude propõe, o dono aprova).

Cada trecho é uma função que desenha a grade (em blocos de 4 studs, `maps/scale.json`) com a classe `G` e
devolve os metadados do `chunk@1`. Rodar da raiz:

    python -I -X utf8 tools/mapkit/proposals/proposta_a.py            # grava maps/trechos/p-*.json
    python -I -X utf8 tools/mapkit/proposals/proposta_a.py --ascii    # também imprime as grades
    python -I -X utf8 tools/mapkit/proposals/proposta_a.py p-s1-escadaria   # só os ids dados

Depois: `python -I -X utf8 tools/mapkit/chunks.py maps/trechos --out maps/trechos/previa` (valida) e
`python -I -X utf8 tools/mapkit/assemble.py maps/proposta-a/plano.json --out maps/proposta-a/` (monta).

Convenções do desenho (valem para todos os trechos `p-`):
- coordenadas (i, j) em blocos, j de baixo para cima (como o `tiles@1`); `box` é inclusivo;
- casca: chão, teto e paredes de **Unhookable** (`x`); o gancho só prende onde o trecho põe `#` (Block),
  `g` (HookOnce) ou `k` (Kill, que segura o gancho). Assim o gancho é dosado de propósito (o validador mostrou
  que com o chão todo prendível a rota mais rápida usa gancho até em corredor);
- `h` (HookThrough) = chão/parede sólido que o gancho atravessa (pisa, mas não prende);
- **gelo nunca é chão** (rede de segurança, ADR 0053): `f` só fica no ar (cortina, "chão falso", pele de
  teto). Embaixo de todo gelo onde se pode cair há chão com `u` (Unfreeze) e um caminho de volta;
- portas laterais com 5 blocos de abertura (pulo inteiro sem bater a cabeça) e chão sólido na borda.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.mapkit.chunks import LIBRARY_DIR, Chunk  # noqa: E402
from tools.mapkit.proposals import trechos_a  # noqa: E402,F401  (registra os trechos)
from tools.mapkit.proposals.kit import ASCII, CHUNKS  # noqa: E402



def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera os trechos p-* da proposta A.")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--ascii", action="store_true")
    ap.add_argument("--out", default=str(LIBRARY_DIR))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for cid, fn in CHUNKS.items():
        if args.ids and cid not in args.ids:
            continue
        data = fn()
        assert data["id"] == cid, (cid, data["id"])
        c = Chunk.from_dict(data)
        c.save(out / f"{cid}.json")
        if args.ascii:
            print(f"== {cid} ({data['tiles']['width']} x {data['tiles']['height']})")
            print(ASCII.get(cid, ""))
        print(f"gravado {cid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
