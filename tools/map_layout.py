"""Layout do mapa 2.5D (rascunho v2), num lugar só.

Usado por `tools/map_sketch.py` (desenho SVG para discutir com o dono) e por `tools/map2d.py`
(greybox no Studio). Coordenadas em studs: X para a direita, Y para cima, tudo no plano Z = 0.

"air" é onde se joga; o resto é rocha. As outras peças ficam dentro do ar. Cada forma guarda o
grupo (estágio) em que foi desenhada; o grupo "Tutorial" é sala separada e não entra no greybox.
"""

VERSION = "v2"

COL = {
    "rock": "#6f717b",
    "air": "#86a6c8",
    "tutorial": "#9db7a6",
    "solid": "#6f717b",
    "ice": "#c8ecff",
    "unfreeze": "#FF8A1F",
    "kill": "#d9434b",
    "nohook": "#8e5bd6",
    "hookonce": "#5fbf6a",
    "checkpoint": "#ffd23f",
    "start": "#5aa06e",
    "finish": "#ffffff",
}

Point = tuple[float, float]

shapes: list[tuple[str, list[Point], str]] = []  # (tipo, pontos, grupo)
labels: list[tuple[float, float, str, int]] = []
route: list[Point] = []

_group = ""


def group(name):
    global _group
    _group = name


def rect(kind, x1, y1, x2, y2):
    shapes.append((kind, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], _group))


def poly(kind, pts):
    shapes.append((kind, pts, _group))


def title(x, y, text):
    labels.append((x, y, text, 15))


def note(x, y, text):
    labels.append((x, y, text, 10))


# ---------- Tutorial (fora do mapa, sala separada) ----------
group("Tutorial")
rect("tutorial", -150, 300, -75, 372)
rect("start", -140, 300, -120, 302)
title(-150, 392, "Tutorial")
note(-148, 362, "gancho: mirar,")
note(-148, 352, "segurar, balançar,")
note(-148, 342, "W/S, roxo, verde")
note(-148, 290, "portal → E1")

# ---------- E1 Salão dos pilares (→) ----------
group("E1")
rect("air", 0, 290, 230, 360)
rect("air", 80, 360, 160, 376)  # teto mais alto no meio
rect("solid", 0, 290, 24, 318)
rect("start", 4, 318, 20, 320)
for px in (54, 100, 146, 192):
    rect("solid", px, 290, px + 12, 340)
rect("ice", 146, 340, 158, 342)  # armadilha: topo do 3º pilar
rect("unfreeze", 192, 340, 204, 342)
rect("kill", 24, 290, 210, 292)
title(0, 380, "E1 · Salão dos pilares")
note(28, 352, "vãos de 30+: gancho no teto · cair = morte")
note(28, 344, "gelo no 3º pilar, laranja no 4º")

# ---------- respiro A ----------
group("RespiroA")
rect("air", 210, 240, 230, 290)
note(234, 282, "respiro")

# ---------- E2 Corredor dos dentes (→) ----------
group("E2")
rect("air", 210, 190, 520, 240)
rect("kill", 230, 190, 500, 192)
for i, tx in enumerate(range(250, 500, 40)):
    rect("nohook" if i == 3 else "solid", tx, 228, tx + 8, 240)
# teto roxo de ~40 studs entre os dentes 3 e 5: obriga um balanço longo ou um pulo (dono, 2A)
rect("nohook", 330, 238, 378, 240)  # 2 studs abaixo do teto: o raio bate no roxo antes da rocha
rect("solid", 350, 190, 372, 204)  # plataforma no meio
rect("ice", 350, 204, 362, 206)
rect("unfreeze", 362, 204, 372, 206)
title(250, 252, "E2 · Corredor dos dentes")
note(240, 182, "chão mortal · plataforma do meio: metade gelo, metade laranja")

# ---------- respiro B ----------
group("RespiroB")
rect("air", 500, 130, 520, 190)

# ---------- E3 Vale em V (←) ----------
group("E3")
poly("air", [(260, 90), (300, 90), (340, 40), (380, 40), (420, 90), (520, 90), (520, 130), (260, 130)])
rect("air", 236, 72, 260, 130)  # fosso
rect("kill", 236, 72, 260, 74)
poly("kill", [(322, 62), (340, 40), (343, 43), (325, 65)])
poly("kill", [(380, 40), (398, 62), (395, 65), (377, 43)])
rect("ice", 440, 90, 460, 92)
title(300, 150, "E3 · Vale em V  ←")
note(300, 30, "gelo no caminho antes da descida")

# ---------- Farol 1 ----------
group("Farol1")
rect("air", 196, 90, 236, 140)
rect("checkpoint", 200, 90, 232, 92)
labels.append((192, 146, "✦ Farol 1", 12))

# ---------- E4 Serpentina (↑, coluna da esquerda, embaixo do E1) ----------
group("E4")
rect("air", -60, 40, 196, 272)
rect("air", 196, 90, 200, 130)
floors = [75, 110, 145, 180, 215, 245]
for i, fy in enumerate(floors):
    if i % 2 == 0:
        rect("solid", -30, fy, 196, fy + 4)
        rect("nohook", -30, fy, -18, fy + 4)
    else:
        rect("solid", -60, fy, 166, fy + 4)
        rect("nohook", 154, fy, 166, fy + 4)
    if i in (1, 3):
        rect("kill", 40, fy + 4, 100, fy + 6)
rect("ice", 60, 149, 84, 151)
rect("unfreeze", -50, 184, -38, 186)
rect("kill", -60, 40, 196, 42)
title(-55, 278, "E4 · Serpentina ↑")
note(-56, 30, "sobe em zigue-zague · pontas roxas · faixas mortais · um andar com gelo")

# ---------- respiro C: poço e túnel por cima do E1 ----------
group("RespiroC")
rect("air", -60, 272, -40, 405)
rect("air", -60, 386, 600, 405)
note(250, 395, "respiro")

# ---------- E5 Campo flutuante x Labirinto ----------
group("E5")
rect("air", 560, 300, 820, 396)
rect("solid", 580, 346, 820, 350)
rect("kill", 600, 350, 800, 352)
for row, by in enumerate((360, 372, 384)):
    for bx in range(604 + (row % 2) * 12, 800, 24):
        rect("solid", bx, by, bx + 4, by + 2)
for wx in range(600, 810, 20):
    rect("solid", wx, 300, wx + 3, 334)
for wx in range(610, 810, 20):
    rect("solid", wx, 312, wx + 3, 346)
rect("ice", 683, 300, 693, 302)
rect("unfreeze", 723, 300, 733, 302)
title(610, 414, "E5 · Campo flutuante (em cima) ou Labirinto (embaixo)")
note(590, 290, "labirinto: lento e seguro, com 1 gelo")

# ---------- E6 Poço ↓, fundo e subida ↑ ----------
group("E6")
rect("air", 820, 40, 862, 396)
for i, wy in enumerate(range(352, 70, -36)):
    if i % 2 == 0:
        rect("solid", 820, wy, 846, wy + 4)
        rect("kill", 820, wy + 4, 846, wy + 6)
    else:
        rect("solid", 836, wy, 862, wy + 4)
        rect("kill", 836, wy + 4, 862, wy + 6)
rect("air", 600, 30, 862, 70)
rect("kill", 650, 30, 810, 32)
for ix, kind in ((680, "ice"), (700, "unfreeze"), (760, "ice"), (780, "unfreeze")):
    rect(kind, ix, 32, ix + 14, 34)
rect("air", 600, 70, 650, 230)
for i, wy in enumerate(range(92, 220, 26)):
    if i % 2 == 0:
        rect("solid", 600, wy, 628, wy + 4)
    else:
        rect("solid", 622, wy, 650, wy + 4)
rect("hookonce", 646, 110, 650, 140)
rect("hookonce", 600, 160, 604, 190)
group("Farol2")
rect("air", 650, 180, 760, 240)
rect("finish", 680, 180, 740, 182)
labels.append((668, 226, "✦ Farol 2 (fim)", 12))
title(670, 160, "E6 · Poço ↓ e subida ↑")
note(670, 150, "lâminas mortais no poço,")
note(670, 140, "gelo no fundo, S com verde")

route.extend([
    (12, 324), (80, 350), (160, 350), (215, 320), (220, 262), (220, 215),
    (300, 220), (360, 210), (500, 215), (510, 150), (470, 105), (360, 60), (290, 105), (220, 100),
    (180, 95), (-20, 90), (180, 125), (-20, 160), (180, 195), (-20, 230), (180, 260), (-50, 262),
    (-50, 396), (590, 396), (600, 370), (810, 370), (840, 380), (828, 320), (850, 260), (828, 200), (850, 140),
    (840, 50), (640, 50), (614, 80), (636, 120), (614, 170), (636, 205), (700, 190),
])
