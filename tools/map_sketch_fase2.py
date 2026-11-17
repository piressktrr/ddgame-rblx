"""Rascunho do mapa da Fase 2 (vista lateral) + conferência de alcance e estimativa de tempo.

Rascunho de papel, não greybox. Coordenadas em studs (X direita, Y cima, plano Z = 0).
Uso (na raiz): python -X utf8 tools/map_sketch_fase2.py memory-palace/04-game-design/estudos/mapa-2-5d/rascunho-fase2.svg
Sem argumento, só imprime a conferência de alcance e os tempos. Estudo: memory-palace/04-game-design/estudos/mapa-fase2.md
"""

import math
import sys

# ---------------- números do Config (src/shared/Config.luau) ----------------
G = 196.2  # gravidade padrão do Roblox
WALK = 24
JUMP_V = math.sqrt(2 * G * 7.2)
DJ_V = 50
HOOK_RANGE = 40
LIMIT = {"segura": 35, "media": 36, "rapida": 38}
UP_VISIBLE = 34  # alvo acima do root que ainda aparece na tela (câmera ~36 acima do root)
T_HOOK = {"segura": 2.4, "media": 1.9, "rapida": 1.4}

COL = {
    "rock": "#6f717b", "air": "#86a6c8", "respiro": "#a9c3dc", "solid": "#5b5d66",
    "ice": "#c8ecff", "unfreeze": "#FF8A1F", "kill": "#d9434b", "nohook": "#8e5bd6",
    "hookonce": "#5fbf6a", "checkpoint": "#ffd23f", "start": "#5aa06e", "finish": "#ffffff",
}
ROUTE_COL = {"rapida": "#ff4fa3", "media": "#00e5ff", "segura": "#ffffff"}

shapes = []  # (kind, x1, y1, x2, y2)
labels = []  # (x, y, text, size, color)
reserved = []  # (x, y, letra, nome)
routes = []  # (stage, name, class, [(x, y, t)])


def rect(kind, x1, y1, x2, y2):
    shapes.append((kind, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))


def anchor(x, y, kind="solid", w=4, h=4):
    rect(kind, x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def title(x, y, t):
    labels.append((x, y, t, 22, "#ffffff"))


def note(x, y, t):
    labels.append((x, y, t, 14, "#ffffff"))


def reserve(x, y, letter, name):
    reserved.append((x, y, letter, name))


def route(stage, name, cls, pts):
    routes.append((stage, name, cls, pts))


def S(x, y):
    return (x, y, "s")


def H(x, y):
    return (x, y, "h")


def W(x, y):
    return (x, y, "w")


def F(x, y):
    return (x, y, "f")


def M(x, y):
    return (x, y, "m")


def platform_hops(plats):
    """Plataformas [(x1, x2, topo)]: chega na borda de perto (gancho) e anda até a de longe."""
    pts = []
    for x1, x2, top in plats:
        pts += [H(x1 + 1, top + 3), W(x2 - 1, top + 3)]
    return pts


def platform_hops_left(plats):
    pts = []
    for x1, x2, top in plats:
        pts += [H(x2 - 1, top + 3), W(x1 + 1, top + 3)]
    return pts


def under(pts):
    """Âncoras no teto/embaixo de algo: o corpo fica ~3 abaixo do ponto."""
    return [H(x, y - 3) for x, y in pts]


# =====================================================================================
# REGIÃO A (E1-E3): Bosque Antigo, faixa de baixo, para a direita →
# =====================================================================================
# ---------- E1 Clareira dos Troncos (X 0-420, Y 0-140) ----------
rect("air", 0, 0, 420, 140)
rect("nohook", 40, 136, 420, 140)  # teto roxo: só os nós cinza prendem
rect("kill", 40, 0, 406, 2)
rect("solid", 0, 0, 40, 70)
rect("start", 6, 70, 34, 72)
tops = [72, 80, 88, 78, 70, 82, 90, 80]
e1_plats = []
for i, t in enumerate(tops):
    x1 = 70 + 42 * i
    rect("solid", x1, 0, x1 + 12, t)
    e1_plats.append((x1, x1 + 12, t))
rect("solid", 406, 0, 420, 70)
knots = [60 + 36 * k for k in range(7)] + [330, 366, 396]
for kx in knots:
    rect("solid", kx - 2, 130, kx + 2, 136)
anchor(40, 100)  # galho de entrada da rota alta
anchor(300, 104)  # galho embaixo da estalactite
rect("ice", 301, 112, 307, 136)  # estalactite de gelo
rect("unfreeze", 294, 0, 318, 14)  # ilha laranja embaixo dela
for ry in (44, 76):
    anchor(322, ry)  # saída da ilha: lateral do tronco 7
title(4, 172, "E1 · Clareira dos Troncos →")
note(4, 154, "troncos, vão 30 · teto roxo, só nós cinza · chão mortal")
note(196, 112, "estalactite de gelo")
note(250, 20, "ilha laranja")
reserve(356, 30, "V", "cristal de degelo (Vulcano)")
route("E1", "troncos", "segura", [S(20, 73), W(38, 73)] + platform_hops(e1_plats) + [H(407, 73), W(420, 73)])
route("E1", "nós do teto", "rapida", [S(20, 73), H(40, 100)] + under([(k, 130) for k in knots[:7]])
      + [H(300, 107)] + under([(330, 130), (366, 130), (396, 130)]) + [F(412, 73), W(420, 73)])

# respiro 1
rect("respiro", 420, 70, 460, 100)
rect("solid", 420, 60, 460, 70)

# ---------- E2 Copa e Raízes (X 460-880, Y 0-280) ----------
rect("air", 460, 0, 880, 280)
rect("solid", 460, 0, 500, 70)  # átrio
rect("solid", 500, 0, 880, 20)  # chão do túnel
rect("solid", 500, 60, 880, 170)  # faixa entre túnel e copa
rect("air", 620, 60, 644, 170)  # poço 1 (troca de andar)
rect("air", 760, 60, 784, 170)  # poço 2 (verde)
rect("kill", 500, 170, 880, 172)  # topo da faixa: mortal (quem cai da copa)
rect("nohook", 460, 276, 880, 280)
for px1, px2 in ((556, 590), (696, 730)):
    rect("air", px1, 10, px2, 20)
    rect("kill", px1, 10, px2, 12)
teeth = list(range(516, 880, 28))
low_route = []
for i, tx in enumerate(teeth):
    kind = "nohook" if i in (4, 9) else "solid"
    rect(kind, tx - 2, 54, tx + 2, 60)
    if kind == "solid":
        low_route.append(H(tx, 51))
    else:
        low_route.append(W(tx + 10, 23))  # roxo: desce, anda e engancha o próximo de baixo
atrium = [(462, 104), (462, 136), (466, 168), (484, 196)]
for ax, ay in atrium:
    anchor(ax, ay)
leaves = [(512 + 35 * k, 206 + (6 if k % 2 else 0)) for k in range(11)] + [(878, 220)]
for lx, ly in leaves:
    rect("solid", lx - 5, ly - 3, lx + 5, ly)
for vx in (602, 674, 746, 818):
    rect("kill", vx - 1, 236, vx + 1, 276)  # cipós mortais
shaft1 = [(642, 56), (622, 82), (642, 108), (622, 134), (640, 160), (630, 190)]
for sx, sy in shaft1:
    anchor(sx, sy)
for sx, sy in ((782, 86), (762, 114), (782, 142)):
    anchor(sx, sy)
anchor(772, 168, "hookonce")
title(464, 312, "E2 · Copa e Raízes →")
note(500, 262, "copa: folhas a 36, cipós mortais, cair = morte")
note(504, 40, "raízes: túnel baixo, dentes a 28 (2 roxos), 2 poços mortais")
note(648, 150, "poço 1 → copa")
note(788, 150, "poço 2 (verde)")
route("E2", "copa", "rapida", [S(480, 73)] + [H(x + 3, y) for x, y in atrium] + [H(x, y + 3) for x, y in leaves]
      + [W(896, 233)])
route("E2", "raízes", "segura", [S(480, 73), W(500, 23)] + low_route + [W(880, 23)])
route("E2", "raízes → poço 1 → copa", "media", [S(480, 73), W(500, 23)] + low_route[:4] + [W(636, 23)]
      + [H(x, y) for x, y in shaft1] + [H(x, y + 3) for x, y in leaves[4:]] + [W(896, 233)])

# respiro 2 (dois andares)
rect("respiro", 880, 230, 920, 260)
rect("solid", 880, 220, 920, 230)
rect("respiro", 880, 20, 920, 60)

# ---------- E3 Garganta Gelada (X 920-1320, Y 0-320) ----------
rect("air", 920, 0, 1320, 320)
rect("solid", 920, 0, 960, 20)
rect("solid", 960, 0, 1200, 20)
rect("kill", 960, 20, 1200, 22)
rect("nohook", 920, 316, 1320, 320)
rect("solid", 960, 64, 1196, 72)  # laje entre o salão e a cascata
rect("nohook", 960, 64, 1196, 66)  # barriga roxa: só as estalactites prendem
rect("kill", 960, 72, 1196, 74)  # topo da laje mortal ...
for ux1 in (985, 1091):
    rect("unfreeze", ux1, 72, ux1 + 24, 76)  # ... menos embaixo das lascas de gelo
stal = [(962, 54), (992, 50), (1022, 56), (1052, 50), (1082, 56), (1112, 50), (1142, 56), (1172, 50)]
for sx, sy in stal:
    rect("solid", sx - 2, sy, sx + 2, 64)
upper = [(946, 244), (980, 236), (1014, 246), (1048, 238), (1082, 248), (1116, 240), (1150, 250), (1184, 256),
         (1216, 266)]
for ux, uy in upper:
    rect("solid", ux - 3, uy - 2, ux + 3, uy + 2)
for ix in (997, 1103):  # lascas de gelo logo acima da linha da cascata
    rect("ice", ix - 2, 250, ix + 2, 262)
for cx in (1003, 1109):  # escadinha de volta do laranja para a cascata
    for cy in (104, 134, 164, 194, 224):
        anchor(cx, cy)
rect("air", 1200, 20, 1228, 270)  # chaminé
rect("solid", 1228, 20, 1240, 266)
rect("nohook", 1196, 20, 1200, 72)
rungs = [(1204 if i % 2 == 0 else 1224, 46 + 26 * i) for i in range(9)]
for rx, ry in rungs:
    anchor(rx, ry)
anchor(1222, 284)
rect("solid", 1240, 266, 1320, 270)
rect("checkpoint", 1250, 270, 1310, 272)
title(924, 352, "E3 · Garganta Gelada →")
note(930, 302, "cascata: blocos a 34, lascas de gelo; congelou = cai no laranja da laje")
note(964, 34, "salão: barriga roxa, estalactites a 30, chão mortal")
note(1244, 280, "✦ Farol 1")
route("E3", "cascata", "rapida", [S(900, 233), W(918, 233)] + [H(x, y + 4) for x, y in upper]
      + [H(1252, 273), W(1280, 273)])
route("E3", "salão + chaminé", "segura", [S(900, 23), W(950, 23)] + under(stal)
      + [H(x, y) for x, y in rungs] + [H(1222, 281), H(1241, 273), W(1280, 273)])

# =====================================================================================
# REGIÃO B (E4-E6): Ruínas Flutuantes, coluna da direita, sobe ↑ e volta ←
# =====================================================================================
rect("respiro", 1320, 270, 1360, 300)
rect("solid", 1320, 266, 1360, 270)
# ---------- E4 Escombros Flutuantes (X 1360-1900, Y 240-470) ----------
rect("air", 1360, 240, 1900, 466)
rect("kill", 1360, 240, 1900, 242)
safe4 = [(1398, 284), (1430, 296), (1462, 310), (1494, 322), (1526, 336), (1558, 348), (1590, 362), (1622, 374),
         (1654, 388), (1686, 400), (1718, 412), (1750, 424), (1782, 436), (1814, 446), (1846, 456)]
for bx, by in safe4:
    rect("solid", bx - 4, by - 3, bx + 4, by)
for bx, by in ((1446, 336), (1574, 330), (1702, 380), (1606, 418), (1830, 420)):
    rect("nohook", bx - 4, by - 3, bx + 4, by)
fast4 = [("h", 1400, 300, ""), ("h", 1434, 312, ""), ("h", 1468, 326, "g"), ("m", 1514, 344, "g"),
         ("h", 1548, 358, "g"), ("m", 1594, 376, ""), ("h", 1628, 390, ""), ("m", 1674, 408, ""),
         ("h", 1708, 422, ""), ("m", 1754, 440, ""), ("h", 1788, 452, "")]
for t, fx, fy, g in fast4:
    anchor(fx, fy + 3, "hookonce" if g else "solid")
title(1364, 500, "E4 · Escombros Flutuantes →")
note(1376, 256, "abismo mortal · blocos a 32 · roxos de isca · arco alto com 3 verdes e embalo")
route("E4", "blocos", "segura", [S(1340, 273), W(1366, 273)] + [H(x, y + 3) for x, y in safe4]
      + [H(1850, 473), W(1870, 473)])
route("E4", "arco verde", "rapida", [S(1340, 273), W(1376, 273)]
      + [(H if t == "h" else M)(fx, fy) for t, fx, fy, g in fast4] + [H(1810, 473), W(1870, 473)])

# ---------- E5 Torre Partida (X 1680-1900, Y 470-820) ----------
rect("air", 1680, 470, 1900, 820)
rect("solid", 1680, 466, 1900, 470)
rect("unfreeze", 1856, 470, 1880, 474)
rect("nohook", 1850, 474, 1856, 816)
rect("nohook", 1880, 474, 1886, 816)
rect("air", 1850, 580, 1856, 612)  # janela do verde no poço
shaft = []
for i in range(13):
    rx = 1858 if i % 2 == 0 else 1878
    ry = 496 + 26 * i
    kind = "hookonce" if i in (5, 9) else "solid"
    anchor(rx, ry, kind)
    shaft.append(H(rx, ry))
for iy in (560, 716):
    rect("ice", 1874, iy, 1880, iy + 10)
slabs = [526, 582, 638, 694, 750, 816]
L1, L2, R1, R2 = 1690, 1714, 1826, 1850
serp = [S(1840, 473)]
for i, top in enumerate(slabs):
    base = 470 if i == 0 else slabs[i - 1] + 4
    gap_left = i % 2 == 0
    if top < 816:
        x1, x2 = (L2, R2) if gap_left else (L1, R1)
        x1, x2 = (L2, R2) if gap_left else (1680, R1)
        rect("solid", x1, top, x2, top + 4)
        if gap_left:
            rect("nohook", R2 - 8, top, R2, top + 4)  # ponta roxa do lado oposto à abertura
        else:
            rect("nohook", 1680, top, 1688, top + 4)
    else:
        rect("solid", 1820, 816, 1900, 820)
    if i in (2, 4):  # faixa mortal no andar, atravessada por um bloco
        rect("kill", 1736, base, 1804, base + 2)
        rect("solid", 1766, base, 1774, base + 10)
        if gap_left:
            serp += [W(1805, base + 3), H(1773, base + 13), W(1767, base + 13), H(1735, base + 3)]
        else:
            serp += [W(1735, base + 3), H(1767, base + 13), W(1773, base + 13), H(1805, base + 3)]
    if gap_left:
        rect("solid", 1680, base + 30, 1692, base + 34)  # consola na parede
        serp += [W(1700, base + 3), H(1690, base + 32), H(L2 + 1, top - 3), W(L2 + 8, top + 7)]
    else:
        anchor(1848, base + 32)
        serp += [W(1838, base + 3), H(1846, base + 32), H(R1 - 1, top - 3), W(R1 - 8, top + 7)]
    if i == 3:
        rect("ice", 1748, top - 14, 1752, top)
        rect("unfreeze", 1740, base, 1760, base + 2)
serp += [W(1880, 823)]
anchor(1853, 592, "hookonce")
title(1540, 800, "E5 · Torre Partida ↑")
note(1560, 760, "serpentina: 5 andares,")
note(1560, 744, "pontas roxas, 2 faixas")
note(1560, 728, "mortais, 1 lasca de gelo")
note(1900, 640, "")
note(1560, 560, "poço (direita): degraus a 26,")
note(1560, 544, "paredes roxas, 2 verdes, gelo;")
note(1560, 528, "cair = laranja do fundo")
reserve(1868, 520, "J", "pedra-âncora (Júpiter)")
route("E5", "poço", "rapida", [S(1868, 473)] + shaft + [H(1866, 823), W(1880, 823)])
route("E5", "serpentina", "segura", serp)
k = next(i for i, p in enumerate(serp) if p[2] == "h" and p[0] > 1840 and p[1] >= 560)
route("E5", "serpentina → verde → poço", "media", serp[: k + 1] + [H(1853, 592)]
      + shaft[4:] + [H(1866, 823), W(1880, 823)])

# ---------- E6 Pontes Quebradas (X 1300-1900, Y 820-910) ← ----------
rect("air", 1300, 820, 1900, 910)
rect("kill", 1340, 820, 1820, 822)
rect("nohook", 1300, 906, 1900, 910)
anchor(1890, 856)
beams = list(range(1868, 1340, -36))
for bx in beams:
    rect("solid", bx - 3, 890, bx + 3, 906)
for bx in beams[1::3]:
    rect("nohook", bx - 18 - 2, 892, bx - 18 + 2, 906)  # vigas roxas de isca no meio
for ix in (1704, 1488):
    rect("ice", ix - 2, 884, ix + 2, 906)  # pingentes de gelo
bridges = []
for k2, bx in enumerate(range(1790, 1360, -46)):
    top = 836 if k2 == 0 else (844 if k2 == 1 else 852)
    rect("solid", bx - 8, top - 6, bx + 8, top)
    bridges.append((bx - 8, bx + 8, top))
rect("ice", 1600, 870, 1604, 890)  # pingente sobre a ponte
rect("unfreeze", 1590, 822, 1614, 830)
rect("solid", 1300, 856, 1340, 860)
rect("checkpoint", 1302, 860, 1338, 862)
title(1304, 942, "E6 · Pontes Quebradas ←")
note(1520, 914, "vigas do teto a 36 · iscas roxas · 2 pingentes de gelo")
note(1420, 830, "pontes, vão 30, chão mortal")
note(1290, 878, "✦ Farol 2")
reserve(1872, 836, "B", "Bouncer: pega aqui")
reserve(1620, 870, "B", "trecho do Bouncer")
route("E6", "vigas do teto", "rapida", [S(1880, 823), H(1888, 856)] + [H(bx, 887) for bx in beams]
      + [F(1330, 863), W(1320, 863)])
route("E6", "pontes", "segura", [S(1880, 823), W(1821, 823)] + platform_hops_left(bridges)
      + [H(1339, 863), W(1320, 863)])

# =====================================================================================
# REGIÃO C (E7-E9): Caverna de Cristal ← e Torre do Mago ↑
# =====================================================================================
rect("respiro", 1260, 860, 1300, 890)
rect("solid", 1260, 856, 1300, 860)
# ---------- E7 Galeria dos Cristais (X 800-1260, Y 830-960) ----------
rect("air", 800, 830, 1260, 960)
rect("kill", 800, 830, 1260, 832)
rect("nohook", 800, 956, 1260, 960)
crys = []
for k2, cx in enumerate(range(1232, 820, -30)):
    cy = 856 + (8 if k2 % 2 else 0)
    rect("solid", cx - 3, cy - 4, cx + 3, cy)
    crys.append((cx, cy))
for ix in (1112, 962):
    rect("ice", ix - 2, 876, ix + 2, 896)
    rect("unfreeze", ix - 10, 832, ix + 10, 842)
up7 = [("h", 1256, 888), ("h", 1226, 908), ("h", 1194, 926), ("h", 1160, 940), ("m", 1112, 946),
       ("h", 1076, 946), ("m", 1028, 946), ("h", 992, 946), ("m", 944, 946), ("h", 908, 940),
       ("h", 876, 926), ("h", 846, 906)]
for t, ux, uy in up7:
    if uy >= 930:
        rect("solid", ux - 3, uy + 3, ux + 3, 956)
    else:
        anchor(ux, uy + 3)
rect("solid", 760, 856, 812, 860)
title(804, 992, "E7 · Galeria dos Cristais ←")
note(840, 968, "teto: 3 vãos de ~48 só com embalo + pulo duplo")
note(820, 845, "cristais a 30 · 2 lascas de gelo com laranja embaixo")
reserve(1052, 920, "M", "orbe de impulso (Mercúrio)")
route("E7", "embalo no teto", "rapida", [S(1280, 863)] + [(H if t == "h" else M)(ux, uy) for t, ux, uy in up7]
      + [F(800, 863), W(780, 863)])
route("E7", "cristais", "segura", [S(1280, 863), W(1262, 863)] + [H(x, y + 3) for x, y in crys]
      + [H(811, 863), W(780, 863)])

# ---------- E8 Coração da Montanha (X 200-800, Y 440-830) ← três andares ----------
rect("air", 200, 440, 800, 830)
rect("solid", 200, 440, 760, 460)  # chão do túnel
rect("solid", 200, 500, 760, 560)  # laje túnel/gruta
rect("solid", 200, 680, 760, 700)  # laje gruta/fio
rect("solid", 200, 820, 800, 830)  # teto do fio (roxo embaixo)
rect("nohook", 200, 816, 760, 820)
rect("air", 760, 440, 800, 856)  # salão de descida
for py in (740, 630):
    rect("solid", 760, py - 4, 800, py)  # patamares
rect("solid", 760, 440, 800, 460)
rect("kill", 200, 700, 760, 702)  # embaixo do fio: mortal
rect("kill", 200, 560, 760, 562)  # chão da gruta: mortal...
for px in (640, 480, 320):
    rect("air", px, 448, px + 30, 460)
    rect("kill", px, 448, px + 30, 450)
high = [(748 - 37 * k, 760 + (6 if k % 2 else 0)) for k in range(15)]
for hx, hy in high:
    anchor(hx, hy)
for dx in (694, 546, 398):
    anchor(dx, 790, "nohook")
mid = []
for k2, mx in enumerate(range(762, 210, -30)):
    my = 664 + (6 if k2 % 2 else 0)
    rect("solid", mx - 3, my, mx + 3, 680)
    mid.append((mx, my))
for ix in (687, 537, 387):
    rect("ice", ix - 2, 644, ix + 2, 662)
    rect("unfreeze", ix - 10, 560, ix + 10, 566)  # ... menos o laranja embaixo do gelo
low = []
for k2, lx in enumerate(range(766, 210, -27)):
    ly = 492 - (6 if k2 % 3 == 1 else 0)
    rect("solid", lx - 2, ly, lx + 2, 500)
    low.append((lx, ly))
# trocas de andar com verde
rect("air", 612, 500, 640, 560)
for gx, gy, gk in ((614, 520, "solid"), (638, 546, "solid"), (626, 572, "hookonce")):
    anchor(gx, gy, gk)
rect("air", 442, 680, 470, 700)
for gx, gy, gk in ((456, 712, "hookonce"), (456, 740, "hookonce")):
    anchor(gx, gy, gk)
title(204, 862, "E8 · Coração da Montanha ←")
note(220, 804, "fio de prata: âncoras a 37, iscas roxas, embaixo mortal")
note(220, 668, "gruta: teto a 30, 3 lascas de gelo, chão mortal com laranja")
note(220, 474, "túnel: teto a 27, chão com 3 poços mortais")
note(476, 588, "troca (verde)")
note(476, 724, "troca (verdes)")
reserve(580, 600, "L", "lâmina: resgate no gelo")
reserve(540, 640, "V", "cristal de degelo")
reserve(700, 480, "B", "trecho do Bouncer")
route("E8", "fio de prata", "rapida", [S(780, 863), F(780, 743)] + [H(x, y) for x, y in high] + [W(200, 763)])
route("E8", "gruta gelada", "media", [S(780, 863), F(780, 633)] + under(mid) + [W(200, 563)])
route("E8", "túnel das raízes", "segura", [S(780, 863), F(780, 463)] + under(low) + [W(200, 463)])

# ---------- E9 Torre do Mago (X 0-200, Y 440-1160) ↑ ----------
rect("air", 0, 440, 200, 1160)
rect("solid", 50, 500, 70, 1056)  # casca da torre
rect("nohook", 50, 500, 54, 1056)
rect("kill", 0, 440, 50, 442)
rect("nohook", 0, 1156, 200, 1160)
rect("solid", 50, 440, 200, 460)
outer = [H(4, 470)]
for k2, oy in enumerate(range(500, 1090, 30)):
    rect("solid", 0, oy - 3, 8, oy)
    if k2 in (6, 13):
        rect("ice", 0, oy, 8, oy + 3)  # borda com tampa de gelo: passar do ponto = congela e cai no fosso
    outer.append(H(6, oy - 6))
rect("solid", 40, 1056, 200, 1060)
rect("finish", 90, 1060, 190, 1062)
floors9 = [560, 660, 760, 860, 960]
inner = [S(190, 463)]
lvl9 = [460] + floors9 + [1056]
for i in range(len(lvl9) - 1):
    base, top = lvl9[i], lvl9[i + 1]
    col_left = i % 2 == 0
    cx = 82 if col_left else 188
    if top < 1056:
        x1, x2 = (94, 200) if col_left else (70, 176)
        rect("solid", x1, top - 4, x2, top)
    rungs9 = [(cx - 10 if j % 2 == 0 else cx + 10, base + 26 * (j + 1)) for j in range(3)]
    for rx, ry in rungs9:
        anchor(rx, ry)
    edge = 94 if col_left else 176
    inner += [W(cx, base + 3)] + [H(rx, ry) for rx, ry in rungs9] + [H(edge + (1 if col_left else -1), top - 7),
                                                                      W(edge + (8 if col_left else -8), top + 3)]
    if i in (1, 3):
        rect("ice", cx + 6, base + 40, cx + 10, base + 56)
        rect("unfreeze", cx - 2, base, cx + 18, base + 2)
greens9 = [(120, 790 + 30 * j) for j in range(9)]
for hy in (860, 960, 1060):
    rect("air", 112, hy - 4, 128, hy)  # alçapões da escada verde
for gx, gy in greens9:
    anchor(gx, gy, "hookonce")
title(4, 1192, "E9 · Torre do Mago ↑")
note(96, 1072, "★ fim")
note(74, 520, "dentro: 6 lances de")
note(74, 506, "degraus a 26 + patamar")
note(4, 452, "fora: bordas a 30, fosso mortal")
reserve(110, 600, "S", "totem de peso + botão (Saturno)")
route("E9", "por fora", "rapida", [S(190, 463), W(30, 463)] + outer + [H(41, 1063), W(100, 1063)])
route("E9", "por dentro", "segura", inner + [W(140, 1063)])
k9 = next(i for i, p in enumerate(inner) if p[2] == "w" and p[1] >= 763)
route("E9", "dentro + escada verde", "media", inner[: k9 + 1] + [H(gx, gy) for gx, gy in greens9] + [H(129, 1063), W(150, 1063)])

# =====================================================================================
# conferência e tempo
# =====================================================================================

def seg_time(cls, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    t = b[2]
    if t == "h":
        return T_HOOK[cls]
    if t == "w":
        return abs(dx) / WALK + 0.3
    if t == "f":
        return math.sqrt(2 * max(-dy, 1) / G) + 0.4
    if t == "m":
        return 1.6
    return 0


def check():
    problems = []
    report = {}
    for stage, name, cls, pts in routes:
        tt, hooks, maxd = 0.0, 0, 0.0
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy)
            if b[2] == "h":
                hooks += 1
                maxd = max(maxd, d)
                if d > LIMIT[cls]:
                    problems.append(f"{stage} {name}: gancho {d:.1f} > {LIMIT[cls]} em {a[:2]}→{b[:2]}")
                if dy > UP_VISIBLE:
                    problems.append(f"{stage} {name}: alvo {dy:.0f} acima (fora da tela) em {b[:2]}")
            if b[2] == "m":
                hooks += 1
                if d > 50:
                    problems.append(f"{stage} {name}: embalo {d:.1f} > 50 em {a[:2]}→{b[:2]}")
            if b[2] == "w" and dy > 13:
                problems.append(f"{stage} {name}: andar/pular sobe {dy:.0f} > 13 em {a[:2]}->{b[:2]}")
            if b[2] == "f" and dy > 0:
                problems.append(f"{stage} {name}: queda que sobe em {a[:2]}->{b[:2]}")
            tt += seg_time(cls, a, b)
        report.setdefault(stage, []).append((name, cls, hooks, maxd, tt))
    return problems, report


def render(path):
    s = 1.5
    X0, X1, Y0, Y1 = -20, 1920, -20, 1220
    top, bottom = 70, 150
    w = (X1 - X0) * s
    h = (Y1 - Y0) * s + top + bottom

    def X(x):
        return (x - X0) * s

    def Y(y):
        return (Y1 - y) * s + top

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="Segoe UI, sans-serif">',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="{COL["rock"]}"/>',
         '<text x="20" y="44" fill="#fff" font-size="30" font-weight="600">Race and Escape · rascunho do mapa da Fase 2 '
         '(vista lateral, studs · 9 estágios · gancho 40 · pulo duplo ~13 de altura)</text>']
    order = ["air", "respiro", "solid", "kill", "ice", "unfreeze", "nohook", "hookonce", "checkpoint", "start", "finish"]
    for kind in order:
        for k, x1, y1, x2, y2 in shapes:
            if k == kind:
                o.append(f'<rect x="{X(x1):.1f}" y="{Y(y2):.1f}" width="{(x2 - x1) * s:.1f}" height="{(y2 - y1) * s:.1f}" '
                         f'fill="{COL[k]}"/>')
    dash = {"rapida": "10 6", "media": "3 6", "segura": ""}
    for stage, name, cls, pts in routes:
        d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y, _ in pts)
        da = f' stroke-dasharray="{dash[cls]}"' if dash[cls] else ""
        o.append(f'<polyline points="{d}" fill="none" stroke="{ROUTE_COL[cls]}" stroke-width="2.5" stroke-opacity="0.9"{da}/>')
    for x, y, letter, name in reserved:
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="11" fill="#1b1d22" stroke="#ffd23f" stroke-width="2"/>')
        o.append(f'<text x="{X(x):.1f}" y="{Y(y) + 5:.1f}" fill="#ffd23f" font-size="14" font-weight="700" '
                 f'text-anchor="middle">{letter}</text>')
    for x, y, t, fs, c in labels:
        o.append(f'<text x="{X(x):.0f}" y="{Y(y):.0f}" fill="{c}" font-size="{fs}" stroke="#1b1d22" stroke-width="3" '
                 f'paint-order="stroke">{t}</text>')
    # setas de região
    reg = [(20, -12, "Região A · E1–E3 · Bosque Antigo (nome provisório) → Farol 1"),
           (1340, 220, "Região B · E4–E6 · Ruínas Flutuantes ↑ ← Farol 2"),
           (320, 420, "Região C · E7–E9 · Caverna de Cristal ← e Torre do Mago ↑ Fim")]
    for x, y, t in reg:
        o.append(f'<text x="{X(x):.0f}" y="{Y(y):.0f}" fill="#ffd23f" font-size="20" font-weight="600" stroke="#1b1d22" '
                 f'stroke-width="3" paint-order="stroke">{t}</text>')
    ly = h - bottom + 40
    legend = [("ice", "gelo (15 s)"), ("unfreeze", "descongelar"), ("kill", "mortal"), ("nohook", "roxo: não prende"),
              ("hookonce", "verde: 1 vez"), ("checkpoint", "checkpoint"), ("start", "início"), ("finish", "fim"),
              ("respiro", "respiro")]
    lx = 20
    for k, t in legend:
        o.append(f'<rect x="{lx}" y="{ly}" width="24" height="24" fill="{COL[k]}" stroke="#1b1d22"/>')
        o.append(f'<text x="{lx + 32}" y="{ly + 19}" fill="#fff" font-size="20">{t}</text>')
        lx += 60 + len(t) * 10
    ly2 = ly + 50
    lx = 20
    for cls, t in (("rapida", "rota rápida/arriscada"), ("media", "rota média / troca"), ("segura", "rota lenta/segura")):
        da = f' stroke-dasharray="{dash[cls]}"' if dash[cls] else ""
        o.append(f'<line x1="{lx}" y1="{ly2}" x2="{lx + 50}" y2="{ly2}" stroke="{ROUTE_COL[cls]}" stroke-width="4"{da}/>')
        o.append(f'<text x="{lx + 60}" y="{ly2 + 7}" fill="#fff" font-size="20">{t}</text>')
        lx += 120 + len(t) * 10
    o.append(f'<circle cx="{lx + 10}" cy="{ly2}" r="11" fill="#1b1d22" stroke="#ffd23f" stroke-width="2"/>')
    o.append(f'<text x="{lx + 10}" y="{ly2 + 5}" fill="#ffd23f" font-size="14" font-weight="700" text-anchor="middle">B</text>')
    o.append(f'<text x="{lx + 30}" y="{ly2 + 7}" fill="#fff" font-size="20">ponto reservado (fase futura): '
             'B Bouncer · L lâmina · J Júpiter · M Mercúrio · V Vulcano · S Saturno</text>')
    o.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))


if __name__ == "__main__":
    probs, rep = check()
    for p in probs:
        print("PROBLEMA:", p)
    print(f"pulo: v0 {JUMP_V:.1f} studs/s, ar {2 * JUMP_V / G:.2f} s, distância {2 * JUMP_V / G * WALK:.1f}")
    total_safe = total_fast = 0.0
    for stage in sorted(rep):
        rows = rep[stage]
        for name, cls, hooks, maxd, tt in rows:
            print(f"{stage} {cls:7s} {name:28s} ganchos {hooks:3d}  maior {maxd:5.1f}  tempo {tt:6.1f} s")
        total_safe += max(r[4] for r in rows if r[1] in ("segura",))
        total_fast += min(r[4] for r in rows)
    print(f"limpo seguro {total_safe:.0f} s  limpo rápido {total_fast:.0f} s")
    if len(sys.argv) > 1:
        render(sys.argv[1])
