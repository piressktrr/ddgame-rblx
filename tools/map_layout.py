"""Layout do mapa 2.5D v3 (Fase 2, ADR 0047 e 0050), num lugar só.

Usado por `tools/map2d.py` (greybox no Studio). Coordenadas em studs: X para a direita, Y para cima,
tudo no plano Z = 0.

Os números vêm do rascunho aprovado, `tools/map_sketch_fase2.py` (9 estágios, 22 rotas; estudo em
memory-palace/04-game-design/estudos/mapa-fase2.md): este arquivo importa as peças de lá e só soma os
AJUSTES DO GREYBOX (seção no fim), que o desenho de papel não resolvia: portas entre estágios,
respiros com placa, vazios fechados, a rota que exige nível de gancho e os pontos reservados.

Ordem importa: as formas são pintadas na ordem em que aparecem. "air" abre (é onde se joga),
"solid" fecha (rocha), zonas só ocupam o que não é rocha, roxo e verde cobrem tudo. Cada forma
guarda o grupo (estágio ou respiro) do lugar onde fica; `attrs[i]` dá atributos da forma i.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import map_sketch_fase2 as S  # noqa: E402  (rascunho aprovado: fonte dos números)

VERSION = "v3"

COL = {
    "rock": "#6f717b",
    "air": "#86a6c8",
    "solid": "#6f717b",
    "ice": "#c8ecff",
    "unfreeze": "#FF8A1F",
    "kill": "#d9434b",
    "nohook": "#8e5bd6",
    "hookonce": "#5fbf6a",
    "checkpoint": "#ffd23f",
    "start": "#5aa06e",
    "finish": "#ffffff",
    "sign": "#33363f",
    "reserved": "#ffd23f",
}

Point = tuple[float, float]

shapes: list[tuple[str, list[Point], str]] = []  # (tipo, pontos, grupo)
attrs: dict[int, dict] = {}  # índice em shapes -> atributos da peça
labels: list[tuple[float, float, str, int]] = []  # (x, y, texto, tamanho) só para o SVG
route: list[Point] = []  # sem uso no v3 (as rotas ficam em `routes`)
routes = S.routes  # (estágio, nome, classe, [(x, y, tipo)]) do rascunho
signs: list[tuple[str, float, float, float, float, str]] = []  # (nome, x, y, w, h, texto)
reserved: list[tuple[str, float, float, str, str]] = []  # (grupo, x, y, Reserved, nota)

# Caixas dos estágios e respiros, só para dar nome (grupo) às peças: a primeira que contém o centro.
GROUPS = [
    ("R1", 420, 60, 460, 100),
    ("R2", 880, 20, 920, 260),
    ("R3", 1320, 266, 1360, 300),
    ("R4", 1800, 436, 1840, 470),
    ("R5", 1820, 816, 1900, 860),
    ("R6", 1260, 856, 1300, 890),
    ("R7", 800, 830, 840, 890),
    ("R8", 200, 440, 240, 830),
    ("E1", 0, 0, 420, 140),
    ("E2", 460, 0, 880, 280),
    ("E3", 920, 0, 1320, 320),
    ("E4", 1360, 240, 1900, 466),
    ("E5", 1680, 466, 1900, 820),
    ("E6", 1300, 816, 1900, 910),
    ("E7", 800, 830, 1260, 960),
    ("E8", 200, 440, 800, 890),
    ("E9", 0, 440, 200, 1160),
]


def group_of(x, y):
    for name, x1, y1, x2, y2 in GROUPS:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return name
    return "Map"


def rect(kind, x1, y1, x2, y2, **attributes):
    x1, x2, y1, y2 = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
    if attributes:
        attrs[len(shapes)] = attributes
    shapes.append((kind, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], group_of((x1 + x2) / 2, (y1 + y2) / 2)))


def sign(name, x, y, w, h, text):
    signs.append((name, x, y, w, h, text))


# ---------------------------------------------------------------- peças do rascunho
# Removidas (trocadas mais abaixo, nos ajustes): o piso que tampava o salão de descida do E8 e os
# patamares do salão, que iam de parede a parede (ninguém passava do primeiro).
DROP = {
    ("solid", 760, 856, 812, 860),
    ("solid", 760, 736, 800, 740),
    ("solid", 760, 626, 800, 630),
    # Gelo que o rascunho punha encostado num degrau da rota (congelar seria obrigatório) ou embaixo
    # de uma viga roxa: vai para o lado (ver "ajustes", mais abaixo).
    ("ice", 1874, 560, 1880, 570),
    ("ice", 1874, 716, 1880, 726),
    ("ice", 194, 600, 198, 616),
    ("ice", 194, 800, 198, 816),
    ("ice", 1702, 884, 1706, 906),
    ("ice", 1486, 884, 1490, 906),
    ("ice", 685, 644, 689, 662),
    ("ice", 535, 644, 539, 662),
    ("ice", 385, 644, 389, 662),
    ("ice", 1600, 870, 1604, 890),
    # O fim cobria as duas bocas por onde se chega ao topo da torre (alçapão verde e lance de dentro).
    ("finish", 90, 1060, 190, 1062),
}
SKETCH_KIND = {"respiro": "air"}

checkpoint_order = 0
for kind, x1, y1, x2, y2 in S.shapes:
    if (kind, x1, y1, x2, y2) in DROP:
        continue
    kind = SKETCH_KIND.get(kind, kind)
    extra = {}
    if kind == "checkpoint":
        checkpoint_order += 1
        extra["Order"] = checkpoint_order  # 1 = fim do E3 (Farol 1), 2 = fim do E6 (Farol 2)
    elif kind == "finish":
        extra["Order"] = 3  # topo do E9: RaceFinish e último checkpoint
    rect(kind, x1, y1, x2, y2, **extra)
assert checkpoint_order == 2, "o rascunho deveria ter 2 checkpoints antes do fim"

for x, y, text, size, _color in S.labels:
    if text:
        labels.append((x, y, text, size))

# ---------------------------------------------------------------- ajustes do greybox
# Gelo trocado de lugar (tirado em DROP). Continua "só onde se encosta voando", com o laranja do
# rascunho embaixo, mas fora do ponto onde a rota para:
# E5, poço: as 2 lascas ficam ACIMA dos degraus da direita (Y 574 e 730), não embaixo: quem passa do
# ponto ao chegar no degrau congela e cai no laranja do fundo.
rect("ice", 1876, 580, 1880, 590)
rect("ice", 1876, 736, 1880, 746)
# E9, por dentro: as 2 lascas ficam acima do degrau da direita do lance (não em volta dele).
rect("ice", 194, 624, 198, 636)
rect("ice", 194, 824, 198, 836)
# E6, vigas: os 2 pingentes saem de baixo das vigas roxas de isca (4 para a esquerda) e encurtam
# (ponta em 894, acima da linha de quem vai de viga em viga, pendurado ~3 abaixo de Y 890).
rect("ice", 1696, 894, 1700, 906)
rect("ice", 1480, 894, 1484, 906)
# E8, gruta: as 3 lascas cortavam a linha dos ganchos (corpo pendurado em ~661-667); descem 8 e
# ficam logo abaixo da linha, com o laranja do rascunho embaixo.
for ix in (687, 537, 387):
    rect("ice", ix - 2, 636, ix + 2, 650)
# E6, pontes: o pingente sobre a ponte cortava a linha das vigas (Y ~887); vai de 870 a 880.
rect("ice", 1600, 870, 1604, 880)
# E1: fresta de 2 entre o tronco 6 e a ilha laranja.
rect("solid", 292, 0, 294, 14)

# E2: os poços 1 e 2 sobem até a copa; a faixa mortal do topo da laje não pode tampar a boca deles
# (a zona mortal agora é sólida, ADR 0049).
rect("air", 620, 170, 644, 172)
rect("air", 760, 170, 784, 172)

# E3: o rascunho deixava um vazio sem chão embaixo do Farol 1 e da chaminé. Vira rocha.
rect("solid", 1200, 0, 1320, 20)
rect("solid", 1240, 20, 1320, 266)
# E3: a parede roxa no fim da laje fechava o salão; abre embaixo (Y 20..48) para a chaminé.
rect("air", 1196, 20, 1200, 48)

# Respiro 4 (E4 -> E5): o chão do E5 tampava o E4 inteiro. Boca de 40 no chão do E5 (X 1800..1840)
# e, embaixo dela, no topo do E4, um patamar de 40 (topo 446) onde as duas rotas do E4 terminam.
# Do patamar, um gancho na borda da boca: à esquerda vai para a serpentina, à direita para o poço.
rect("air", 1800, 466, 1840, 470)
rect("solid", 1800, 436, 1840, 446)
# E5: a parede roxa esquerda do poço abre embaixo (470..500: anda-se do chão para o poço) e em cima
# (754..816: o último andar da serpentina entra no poço e sai com ele).
rect("air", 1850, 474, 1856, 500)
rect("air", 1850, 754, 1856, 816)
# Respiro 5 (E5 -> E6): tampa de rocha sobre o último andar da serpentina (embaixo da faixa mortal do
# E6) e a boca do poço (X 1856..1880) aberta para o E6. O chão em volta da boca (X 1820..1900) é o
# respiro; o E6 começa à direita dela.
rect("solid", 1680, 816, 1820, 820)
rect("air", 1856, 816, 1880, 820)

# E6: vazio fechado embaixo do Farol 2.
rect("solid", 1300, 820, 1340, 856)

# Respiro 7 (E7 -> E8): patamar de 40 no fim do E7 (X 800..840, topo 860) e, à esquerda dele, o salão
# de descida aberto até Y 890 (antes um piso o tampava). Patamares do salão só na metade de dentro
# (X 760..780): quem cai pela metade de fora (780..800) desce até o túnel; com A/D escolhe o andar.
rect("air", 760, 856, 800, 890)
rect("solid", 800, 830, 840, 860)
rect("solid", 760, 736, 780, 740)
rect("solid", 760, 626, 780, 630)
# E7: salto de embalo de verdade. No código de hoje o A/D no ar dá ~50 studs/s² durante o embalo,
# então um vão de ~48 na mesma altura passa sem pulo duplo (achado do tutorial, lição 7). Como no
# tutorial, o alvo depois de cada vão fica ~12 mais alto que a âncora de saída: as 3 âncoras de saída
# (X 1160, 1076, 992) descem para Y 934 (a haste do teto fica mais comprida). No E4 os 4 vãos do
# arco verde já sobem ~18 e ficam como no rascunho.
for ux in (1160, 1076, 992):
    rect("solid", ux - 3, 937, ux + 3, 950)

# E8: as trocas de andar (poço com verde e verdes da gruta) furam a faixa mortal de cima.
rect("air", 612, 560, 640, 562)
rect("air", 442, 700, 470, 702)

# Respiro 8 (E8 -> E9): os últimos 40 de cada andar (X 200..240) têm chão que não mata.
rect("solid", 200, 560, 240, 562)
rect("solid", 200, 700, 240, 702)

# E9, por fora: a parede do mapa ao lado do canal é roxa (senão a rocha inteira servia de alvo e as
# bordas com tampa de gelo não valiam nada).
rect("nohook", -10, 442, 0, 1156)
# E9, topo: a laje do fim abre à direita (X 176..200), por onde sobe o lance de dentro (os outros
# patamares já tinham o buraco alternado). O fim (RaceFinish, Order 3) fica entre as duas bocas.
rect("air", 176, 1056, 200, 1060)
rect("finish", 130, 1060, 176, 1062, Order=3)

# Rota que EXIGE nível de gancho (ADR 0050, Q49): "corrente alta" do E3, opcional, por cima da
# cascata até o Farol 1. 8 âncoras com vãos de ~45-46 (o alcance de hoje é 40, ADR 0042). Nunca é a
# única rota (cascata e chaminé ficam). Pela física de hoje (embalo + A/D no ar) dá para chegar a 40
# da âncora seguinte voando; para barrar de verdade, o gancho terá de ler `RequiresHookLevel` quando
# a evolução do gancho (Q23) entrar.
HOOK_LV2 = [(942, 262), (987, 270), (1032, 278), (1077, 284), (1122, 288), (1167, 290), (1212, 290), (1257, 292)]
for hx, hy in HOOK_LV2:
    rect("solid", hx - 2, hy - 2, hx + 2, hy + 2, RequiresHookLevel=2)
labels.append((960, 300, "corrente alta: exige gancho nível 2 (vãos ~45)", 14))

# Placas com o número e o nome de trabalho do estágio (ADR 0050, Q46 e Q54), no fundo.
sign("E1_Sign", 20, 92, 36, 10, "E1 · Clareira dos Troncos")
sign("R1_Sign", 440, 86, 36, 10, "E2 · Copa e Raízes")
sign("R2_SignHigh", 900, 247, 36, 10, "E3 · Garganta Gelada")
sign("R2_SignLow", 900, 44, 36, 10, "E3 · Garganta Gelada")
sign("E3_SignFarol", 1280, 290, 36, 8, "Farol 1 (checkpoint)")
sign("R3_Sign", 1340, 287, 36, 10, "E4 · Escombros Flutuantes")
sign("R4_Sign", 1820, 457, 36, 8, "E5 · Torre Partida")
sign("R5_Sign", 1838, 840, 32, 8, "E6 · Pontes Quebradas")
sign("E6_SignFarol", 1320, 878, 36, 8, "Farol 2 (checkpoint)")
sign("R6_Sign", 1280, 878, 36, 8, "E7 · Galeria dos Cristais")
sign("R7_Sign", 820, 878, 36, 8, "E8 · Coração da Montanha")
sign("R8_SignLow", 220, 476, 36, 8, "E9 · Torre do Mago")
sign("R8_SignMid", 220, 580, 36, 8, "E9 · Torre do Mago")
sign("R8_SignHigh", 220, 730, 36, 8, "E9 · Torre do Mago")
sign("E9_SignFinish", 153, 1086, 40, 10, "Fim da corrida")

# Pontos reservados das fases 4 e 5 (marcadores sem efeito: sem colisão, consulta nem toque).
RESERVED = {"B": "Bouncer", "L": "Blade", "J": "Jupiter", "M": "Mercury", "V": "Vulcan", "S": "Saturn"}
for x, y, letter, note in S.reserved:
    reserved.append((group_of(x, y), x, y, RESERVED[letter], note))
