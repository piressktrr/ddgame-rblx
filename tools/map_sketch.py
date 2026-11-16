"""Rascunho do mapa 2.5D em vista lateral (SVG), para discutir com o dono antes do greybox.

Não é o mapa final: é um desenho em studs (X para a direita, Y para cima) com as áreas de ar
(onde se joga), a rocha (cinza) e as zonas por cor. O layout fica em `tools/map_layout.py`
(o mesmo que `tools/map2d.py` usa para montar o greybox no Studio).

v0 (faixa reta) e v1 (fileiras) ficaram guardados como imagem. v2: salas soltas em várias alturas
ligadas por poços e túneis de respiro; gelo como armadilha no caminho; cair quase sempre = checkpoint;
tutorial do gancho separado, antes do mapa.

Uso: python tools/map_sketch.py  ->  memory-palace/04-game-design/estudos/mapa-2-5d/rascunho-v2.svg
"""

from pathlib import Path

from map_layout import COL, VERSION, labels, route, shapes

OUT = Path(__file__).resolve().parent.parent / "memory-palace" / "04-game-design" / "estudos" / "mapa-2-5d"
S = 3  # px por stud
X0, X1, Y0, Y1 = -160, 880, 10, 425
PAD_TOP = 70


def X(x):
    return (x - X0) * S


def Y(y):
    return (Y1 - y) * S + PAD_TOP


def render_svg() -> str:
    w, h = (X1 - X0) * S, (Y1 - Y0) * S + PAD_TOP + 60
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="Segoe UI, sans-serif">',
        f'<rect width="{w}" height="{h}" fill="{COL["rock"]}"/>',
        f'<text x="20" y="44" fill="#fff" font-size="30" font-weight="600">Race and Escape · rascunho {VERSION} do mapa '
        "(vista lateral, studs; pulo ~9, gancho 40)</text>",
    ]
    order = ["air", "tutorial", "solid", "ice", "unfreeze", "kill", "nohook", "hookonce", "checkpoint", "start", "finish"]
    for kind in order:
        for k, pts, _ in shapes:
            if k == kind:
                d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
                out.append(f'<polygon points="{d}" fill="{COL[k]}"/>')
    d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in route)
    out.append(f'<polyline points="{d}" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="10 8" stroke-opacity="0.8"/>')
    for x, y, t, fs in labels:
        out.append(f'<text x="{X(x):.0f}" y="{Y(y):.0f}" fill="#fff" font-size="{fs * 2}">{t}</text>')
    legend = [("ice", "gelo"), ("unfreeze", "descongelar"), ("kill", "mortal (volta ao checkpoint)"), ("nohook", "não gruda"),
              ("hookonce", "gruda 1 vez"), ("checkpoint", "checkpoint"), ("finish", "fim"), ("tutorial", "tutorial")]
    lx = 20
    for k, t in legend:
        out.append(f'<rect x="{lx}" y="{h - 45}" width="26" height="26" fill="{COL[k]}"/>')
        out.append(f'<text x="{lx + 34}" y="{h - 24}" fill="#fff" font-size="22">{t}</text>')
        lx += 70 + len(t) * 11
    out.append(f'<text x="{lx + 20}" y="{h - 24}" fill="#fff" font-size="22">- - - rota principal</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"rascunho-{VERSION}.svg").write_text(render_svg(), encoding="utf8", newline="\n")
    print("ok", OUT / f"rascunho-{VERSION}.svg")


if __name__ == "__main__":
    main()
