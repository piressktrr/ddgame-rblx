"""Trechos da proposta A (ids `p-…`). Ver o topo de `proposta_a.py` para as convenções do desenho.

Nomes de seção/tema são de trabalho (o tema final está adiado, Q24). Padrões vindos do estudo do vídeo de
referência (memory-palace/04-game-design/estudos/referencia-video-2026-11-14.md) são só PADRÕES; o traçado
é original (regra 1 do AGENTS.md). Medidas em blocos de 4 studs; números de movimento de maps/metrics.json:
pulo 2,9 blocos (degrau confortável 2), pulo duplo 5,4 (confortável 4), vão de pulo 9 (confortável 6), vão de
pulo duplo 15 (confortável 12), gancho 10 do root (regra 9; até 8 para cima, 5 para baixo), tela 26 x 15.
"""

from __future__ import annotations

from typing import Any

from tools.mapkit.proposals.kit import G, chunk, lane, meta

# --------------------------------------------------------------------------------------------------
# Peças de desenho reutilizadas
# --------------------------------------------------------------------------------------------------


def freeze_pit(g: G, i0: int, i1: int, top: int, depth: int = 3) -> None:
    """Vão i0..i1 entre duas bordas com os pés em `top`, com REDE DE SEGURANÇA: "chão falso" de gelo na linha
    top-1 (de i0+2 a i1), fundo de degelo (pés em top-depth) e, em i0, um degrau de volta (pés em top-1) com a
    coluna i0+1 sem gelo por cima. Quem cai congela, pousa no degelo (descongela na hora) e volta pelo degrau.
    O gelo nunca é chão e fica a 1 bloco de qualquer lugar onde se pisa."""
    bottom = top - depth
    g.box(i0, 0, i1, bottom - 1, "x")
    g.box(i0, bottom, i1, top - 1, ".")
    g.ground(i0, i0, top - 1)
    g.box(i0 + 2, top - 1, i1, top - 1, "f")
    g.box(i0 + 1, bottom, i1, bottom, "u")


def red_pit(g: G, i0: int, i1: int, top: int, depth: int = 3) -> None:
    """Vão i0..i1 com fundo vermelho (Kill: volta ao checkpoint) `depth` blocos abaixo dos pés `top`."""
    floor = top - depth - 1
    g.box(i0, 0, i1, floor - 1, "x")
    g.box(i0, floor, i1, floor, "k")
    g.box(i0, floor + 1, i1, top - 1, ".")


def anchor(g: G, i0: int, i1: int, j: int, ch: str = "#", stalk: bool = True) -> None:
    """Ponto de gancho (bloco prendível) pendurado por uma haste Unhookable até o teto."""
    g.box(i0, j, i1, j, ch)
    if stalk:
        m = (i0 + i1) // 2
        g.box(m, j + 1, m, g.h - 2, "x")


# ==================================================================================================
# S1 — Vale do Despertar (aquecimento: pulo, pulo duplo, 1º gancho, 1º gelo)
# ==================================================================================================
S1 = "vale"


@chunk
def p_s1_escadaria() -> dict[str, Any]:
    g = G(72, 12).shell()
    for i0, i1, feet in (
        (10, 19, 2), (20, 29, 3), (30, 37, 5), (38, 45, 4), (46, 70, 6),
    ):
        g.ground(i0, i1, feet)
    g.door("L", 1, "entry", "in").door("R", 6, "exit", "out")
    return meta(
        "p-s1-escadaria", g, name="Escadaria de boas-vindas", theme=S1, pattern="original: degraus de pulo",
        rhythm="respiro", difficulty=2, required=["jump"], optional=["walk", "double"],
        notes="Abertura do mapa. Degraus de 1–2 blocos (pulo simples confortável), patamares de 8–10 e descidas a pé. "
        "Tudo Unhookable: aqui o gancho não ajuda, o jogador pega o ritmo do pulo. Sem risco nenhum.",
    )


@chunk
def p_s1_fosso_duplo() -> dict[str, Any]:
    g = G(66, 14).shell()
    top = 6
    g.ground(1, 9, top)
    g.box(21, top - 1, 26, top - 1, "x")  # laje A
    g.box(38, top - 1, 43, top - 1, "x")  # laje B
    for i0 in (15, 31, 46):
        g.ground(i0, i0 + 1, 3)  # calombos do fosso
    g.ground(49, 51, 3)
    g.ground(52, 54, 5)  # degraus de saída do fosso
    g.ground(55, 64, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    lanes = [
        lane("alto", "por cima, três pulos duplos", "rapida", (10, 6, 54, 10)),
        lane("fosso", "pelo fosso, pulando calombos", "segura", (11, 1, 48, 4)),
    ]
    return meta(
        "p-s1-fosso-duplo", g, name="Fosso do pulo duplo", theme=S1, pattern="ensinar→cobrar (vídeo, padrão 2)",
        rhythm="amplo", difficulty=3, required=["double"], optional=["walk", "jump"], lanes=lanes,
        notes="Primeira bifurcação. Por cima: três vãos de 11 blocos que só o pulo duplo passa, com lajes de 6 "
        "para pousar. Por baixo: desce 5 blocos (queda ainda visível), atravessa o fosso pulando três calombos e "
        "sobe dois degraus. Quem erra o pulo duplo cai no fosso e segue pela rota segura: rede de segurança sem "
        "castigo. Na dupla: nada especial.",
    )


@chunk
def p_s1_primeiro_gancho() -> dict[str, Any]:
    g = G(72, 20).shell()
    # batida A: vão de 16 com um ponto só
    g.ground(1, 9, 6)
    g.ground(10, 11, 5)
    g.ground(12, 13, 3)
    g.ground(26, 37, 7)
    anchor(g, 16, 18, 11)
    # batida B: parede de 6 com a quina prendível
    g.ground(38, 47, 13)
    g.box(38, 12, 39, 12, "#")
    # batida C: vão de 20 mais alto, com um ponto e fosso de volta
    g.box(48, 0, 67, 7, "x")
    g.ground(48, 49, 12)
    g.ground(50, 51, 10)
    anchor(g, 54, 56, 17)
    g.ground(68, 70, 14)
    g.door("L", 6, "entry", "in").door("R", 14, "exit", "out")
    return meta(
        "p-s1-primeiro-gancho", g, name="O primeiro gancho", theme=S1,
        pattern="sala de um ponto só (vídeo), versão de ensino", rhythm="gargalo", difficulty=3,
        required=["hook"], optional=["momentum", "double"],
        notes="Ensina o gancho em três batidas: (A) um único bloco prendível pendurado sobre um vão de 16; (B) uma "
        "parede de 6 blocos que só se sobe prendendo na quina de cima (o resto é Unhookable); (C) um vão de 20, "
        "mais alto, com um ponto só. Quem cai em A ou C anda até os degraus do fundo e tenta de novo (sem gelo, sem "
        "vermelho). Gargalo de propósito: uma rota só.",
    )


@chunk
def p_s1_cortinas() -> dict[str, Any]:
    g = G(92, 14).shell()
    top = 4
    g.ground(1, 8, top)
    freeze_pit(g, 9, 14, top)  # vão 6
    g.ground(15, 20, top)
    freeze_pit(g, 21, 31, top)  # vão 11: pulo duplo
    g.box(26, 9, 26, 12, "f")  # cortina: castiga o duplo cedo
    g.ground(32, 37, top)
    g.ground(38, 90, top + 4)  # degrau de 4: pulo duplo
    g.box(36, 10, 37, 12, "f")  # cortina sobre a quina
    top2 = top + 4
    for i0, i1 in ((44, 48), (52, 57), (61, 67), (71, 77), (81, 85)):
        freeze_pit(g, i0, i1, top2)  # vãos 5, 6, 7, 7, 5
    g.door("L", top, "entry", "in").door("R", top2, "exit", "out")
    return meta(
        "p-s1-cortinas", g, name="Cortinas de gelo", theme=S1,
        pattern="freeze como chão falso + rede de segurança (vídeo, padrões 3, 6 e 10)", rhythm="amplo",
        difficulty=3, required=["jump", "double"], optional=["unfreeze"],
        notes="Primeiro gelo. Cada vão tem um 'chão falso' de gelo: quem cai atravessa, congela, pousa no degelo logo "
        "abaixo (descongela na hora) e volta pelo degrauzinho — o gelo nunca é chão. Cortinas curtas de gelo "
        "penduradas no teto castigam o pulo duplo dado cedo demais (bater nelas congela ~1 s e derruba). No fim, "
        "cinco vãos seguidos (5, 6, 7, 7, 5) no ritmo 'respira e salta'. Fecha a seção 1.",
        checkpoint_end=True,
    )


# ==================================================================================================
# S2 — Torres Geladas (gelo + teto prendível; pilares sem gancho)
# ==================================================================================================
S2 = "torres"


@chunk
def p_s2_galeria() -> dict[str, Any]:
    g = G(70, 14).shell()
    for i0, i1, feet in ((10, 19, 2), (20, 27, 4), (28, 37, 3), (38, 47, 5), (48, 68, 6)):
        g.ground(i0, i1, feet)
    for i in (24, 33, 43, 56):
        g.box(i, 11, i, 12, "f")  # cortinas altas: só decoração e aviso do tema
    g.door("L", 1, "entry", "in").door("R", 6, "exit", "out")
    return meta(
        "p-s2-galeria", g, name="Galeria das cortinas", theme=S2, pattern="original: respiro com o tema do gelo",
        rhythm="respiro", difficulty=2, required=["jump"], optional=["walk"],
        notes="Respiro logo depois do checkpoint 1: patamares de 8–10 e degraus de 1–2, sem vão. Cortinas de gelo altas "
        "(fora do alcance do pulo simples) mostram o tema da seção sem castigar ninguém.",
    )


@chunk
def p_s2_patamar() -> dict[str, Any]:
    g = G(72, 16).shell()
    # chão (segura): calombos de 2 e uma covinha
    for i0 in (15, 22, 29, 36, 43):
        g.ground(i0, i0 + 1, 3)
    g.ground(50, 55, 3)
    g.ground(56, 70, 5)
    # ponte alta (rápida): HookThrough, reta, com dois vãos de 5
    g.box(4, 2, 7, 2, "h")
    g.box(9, 4, 12, 4, "h")
    g.box(14, 6, 27, 6, "h")
    g.box(32, 6, 43, 6, "h")
    g.box(48, 6, 53, 6, "h")
    g.door("L", 1, "entry", "in").door("R", 5, "exit", "out")
    lanes = [
        lane("ponte", "pela ponte alta", "rapida", (14, 7, 53, 11)),
        lane("chao", "pelo chão, pulando calombos", "segura", (14, 1, 49, 4)),
    ]
    return meta(
        "p-s2-patamar", g, name="Patamar das pontes", theme=S2, pattern="original: duas pistas paralelas",
        rhythm="amplo", difficulty=3, required=["jump"], optional=["walk", "double", "hookthrough"], lanes=lanes,
        notes="Duas pistas paralelas, sem gancho: a ponte alta (HookThrough — pisa, "
        "mas o gancho atravessa) é reta com dois vãos de 4–5; o chão tem calombos de 2. Ninguém se perde aqui.",
    )


@chunk
def p_s2_torres() -> dict[str, Any]:
    g = G(70, 15).shell()
    g.ground(1, 7, 6)
    g.ground(8, 9, 5)
    g.ground(10, 11, 3)  # volta do fundo
    g.box(15, 4, 59, 4, "f")  # chão falso de gelo
    g.box(12, 1, 59, 1, "u")  # fundo de degelo
    for i0, top in ((13, 7), (20, 8), (27, 7), (34, 9), (41, 8), (48, 9), (55, 8)):
        g.box(i0, 3, i0 + 2, top - 1, "x")  # pilar pendurado (passagem por baixo)
    g.box(12, 14, 59, 14, "#")  # teto prendível
    g.ground(60, 68, 8)
    g.door("L", 6, "entry", "in").door("R", 8, "exit", "out")
    return meta(
        "p-s2-torres", g, name="Torres geladas", theme=S2, pattern="torres geladas (vídeo), sem gelo no topo",
        rhythm="apertado", difficulty=4, required=[], optional=["jump", "hook", "momentum", "unfreeze"],
        notes="Sete pilares Unhookable de 3 blocos, topos desencontrados (1–2) e um teto todo prendível. Dois jeitos: "
        "atravessar pendurado no teto, de balanço em balanço (pousando nos pilares altos), ou pular de pilar em pilar "
        "(vãos de 4) sem gancho. Embaixo, chão falso de gelo e fundo de degelo; quem cai anda de volta por baixo dos "
        "pilares e sobe os degraus. Na dupla: um fica no pilar e puxa o outro (padrão do vídeo); o validador não "
        "simula dupla.",
    )



@chunk
def p_s2_teto_de_gelo() -> dict[str, Any]:
    gaps = (4, 5, 5, 5, 6, 6, 5, 6)
    plat = 4
    w = 7 + sum(gaps) + plat * (len(gaps) - 1) + 12
    feet_end = 3 + 2 * len(gaps)
    g = G(w, feet_end + 7).shell()
    feet = 3
    g.ground(1, 6, feet)
    seg0 = 1
    x = 7
    for n, gap in enumerate(gaps):
        freeze_pit(g, x, x + gap - 1, feet)
        g.box(seg0, feet + 5, x + gap - 1, feet + 5, "f")  # teto de gelo: castiga o pulo duplo
        g.box(seg0, feet + 6, x + gap - 1, g.h - 1, "x")
        x += gap
        seg0 = x
        feet += 2
        last = n == len(gaps) - 1
        g.ground(x, (w - 2) if last else x + plat - 1, feet)
        if not last:
            x += plat
    g.door("L", 3, "entry", "in").door("R", feet_end, "exit", "out")
    return meta(
        "p-s2-teto-de-gelo", g, name="Escada sob o gelo", theme=S2, pattern="original: teto de freeze que proíbe o pulo duplo",
        rhythm="apertado", difficulty=4, required=["jump"], optional=["unfreeze"],
        notes="Escada de oito degraus de 2 blocos (patamares de 4), cada um depois de um vão de 4–6 com chão falso de gelo. O teto de cada "
        "degrau é uma pele de gelo a 5 blocos dos pés: o pulo simples passa raspando, o pulo duplo congela (e derruba). "
        "Ensina a medir o pulo simples. Quem cai descongela no fundo e volta pelo degrau do vão.",
    )

@chunk
def p_s2_brasas() -> dict[str, Any]:
    gaps = (6, 7, 7, 8, 6, 8, 7, 8, 6, 8, 7)
    w = 6 + sum(gaps) + 2 * (len(gaps) - 1) + 12
    g = G(w, 11).shell()
    top = 5
    g.ground(1, 6, top)
    x = 7
    for n, gap in enumerate(gaps):
        freeze_pit(g, x, x + gap - 1, top)
        x += gap
        if n < len(gaps) - 1:
            g.ground(x, x + 1, top)  # ilha de 2
            x += 2
    g.ground(x, w - 2, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s2-brasas", g, name="Corredor de brasas", theme=S2, pattern="corredor de freeze com ilhas (vídeo), em pulos",
        rhythm="apertado", difficulty=4, required=["jump"], optional=["double", "unfreeze"],
        notes="Corredor baixo (5 blocos de altura livre) sem gancho nenhum: ilhas de só 2 blocos e onze vãos de 6 a 8 "
        "sobre chão falso de gelo — pulo no limite ou pulo duplo baixo (o teto corta o duplo alto). Ritmo de 'respira "
        "e salta'. Quem cai descongela no fundo e volta pelo degrau do próprio vão (perde ~3 s). Fecha a seção 2.",
        checkpoint_end=True,
    )


# ==================================================================================================
# S3 — Ventania (embalo do gancho, verde de uso único, vermelho)
# ==================================================================================================
S3 = "ventania"


@chunk
def p_s3_planicie() -> dict[str, Any]:
    g = G(72, 16).shell()
    for i0, i1, feet in ((10, 19, 2), (20, 29, 4), (30, 39, 3), (40, 49, 5), (50, 57, 4), (58, 70, 6)):
        g.ground(i0, i1, feet)
    anchor(g, 34, 35, 12)  # atalho de embalo opcional
    g.door("L", 1, "entry", "in").door("R", 6, "exit", "out")
    return meta(
        "p-s3-planicie", g, name="Planície do vento", theme=S3, pattern="original: colinas de respiro",
        rhythm="respiro", difficulty=2, required=["jump"], optional=["hook", "momentum"],
        notes="Respiro depois do checkpoint: colinas de 1–2 blocos com patamares largos. Um único ponto de gancho "
        "pendurado no meio deixa quem já sabe cortar caminho com um balanço (opcional; o resto é Unhookable).",
    )


@chunk
def p_s3_balanco() -> dict[str, Any]:
    g = G(90, 20).shell()
    top, low = 10, 5
    g.ground(1, 11, top)
    g.ground(12, 39, low)  # piso de baixo (segura)
    for i0 in (17, 25):
        g.ground(i0, i0 + 1, low + 2)  # calombos
    g.box(31, 6, 33, 6, "h")
    g.box(35, 8, 37, 8, "h")  # subida em HookThrough (pés 7 e 9)
    anchor(g, 18, 20, 16)  # o ponto do balanço
    g.ground(40, 54, top)
    red_pit(g, 55, 60, top)  # vão curto vermelho (pulo)
    g.ground(61, 66, top)
    red_pit(g, 67, 80, top)  # vão vermelho de 14: pulo duplo no limite, ou o ponto de cima
    anchor(g, 72, 73, top + 6)
    g.ground(81, 88, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    lanes = [
        lane("balanco", "um balanço só, por cima", "rapida", (12, 10, 39, 18)),
        lane("baixo", "por baixo, a pé", "segura", (13, 5, 29, 8)),
    ]
    return meta(
        "p-s3-balanco", g, name="Balanço do vale", theme=S3, pattern="original: vão de embalo sobre rota baixa",
        rhythm="amplo", difficulty=3, required=[], optional=["hook", "momentum", "double", "jump", "hookthrough", "kill"],
        lanes=lanes,
        notes="Bifurcação do embalo. Rápida: prender no único ponto e soltar no embalo (com pulo duplo no fim) para "
        "cruzar 28 blocos de uma vez. Segura: descer 5 blocos, andar pelo piso de baixo pulando calombos e subir "
        "por duas plataformas HookThrough. O ponto não é alcançável de baixo (fora da tela), então as rotas não se "
        "misturam; quem erra o balanço cai na rota segura. Depois, o vermelho aparece: um vão de 6 (pulo simples) e "
        "um de 14 (pulo duplo no limite, ou um balanço curto no ponto de cima).",
    )



@chunk
def p_s3_rajada() -> dict[str, Any]:
    g = G(86, 18).shell()
    top = 7
    g.ground(1, 8, top)
    freeze_pit(g, 9, 74, top, depth=3)
    for i0 in (24, 39, 53, 67):
        g.box(i0, top - 1, i0 + 1, top - 1, ".")  # sem gelo embaixo do poleiro
        g.box(i0, top, i0 + 1, top, "h")  # poleiro HookThrough de 2 (pés 1 acima da borda)
    for i0 in (16, 31, 45, 59):
        anchor(g, i0, i0 + 1, top + 7)
    g.ground(75, 84, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s3-rajada", g, name="Rajada", theme=S3, pattern="original: balanço e pouso de precisão",
        rhythm="apertado", difficulty=4, required=["hook", "momentum"], optional=["double", "hookthrough", "unfreeze"],
        notes="Quatro balanços seguidos, cada um terminando num poleiro HookThrough de só 2 blocos (não prende o gancho): "
        "prender, soltar na hora certa e frear no poleiro. Embaixo, 66 blocos de chão falso de gelo sobre degelo; "
        "quem cai volta andando até o degrau da entrada (cair no fim custa caro). A dupla pode esperar no poleiro e "
        "puxar o parceiro.",
    )

@chunk
def p_s3_verde() -> dict[str, Any]:
    g = G(72, 18).shell()
    top = 7
    g.ground(1, 9, top)
    red_pit(g, 10, 59, top, depth=5)
    g.box(28, 0, 31, top - 2, "x")
    g.box(28, top - 1, 31, top - 1, "h")  # ilha de descanso (HookThrough)
    anchor(g, 16, 17, 14, ch="g")
    anchor(g, 38, 39, 14, ch="g")
    anchor(g, 45, 46, 14, ch="g")
    g.ground(60, 70, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s3-verde", g, name="Ponte dos verdes", theme=S3, pattern="original: corrente de gancho único sobre o vermelho",
        rhythm="gargalo", difficulty=4, required=["hookonce", "hook"], optional=["momentum", "double", "hookthrough", "kill"],
        notes="Gargalo da seção: três pontos VERDES (gancho único: cada um prende uma vez só) sobre um fosso vermelho "
        "de 50 blocos, com uma ilha HookThrough no meio para respirar. Errou = vermelho = volta ao checkpoint, e os "
        "verdes voltam junto (ADR 0053). Na dupla: quem passou pode puxar o parceiro com o gancho em jogador. "
        "Fecha a seção 3.",
        checkpoint_end=True,
    )


# ==================================================================================================
# S4 — Casa das Portas (precisão: furos com moldura sem gancho, mão única)
# ==================================================================================================
S4 = "portas"


@chunk
def p_s4_saguao() -> dict[str, Any]:
    g = G(68, 14).shell()
    for i0, i1, feet in ((12, 19, 2), (20, 29, 3), (30, 37, 1), (38, 47, 3), (48, 55, 5), (56, 66, 5)):
        g.ground(i0, i1, feet)
    for i, feet in ((24, 3), (42, 3), (60, 5)):
        g.box(i, feet + 2, i, 12, "x")  # paredes com porta de 2 de altura (passa andando)
    g.door("L", 1, "entry", "in").door("R", 5, "exit", "out")
    return meta(
        "p-s4-saguao", g, name="Saguão das portas", theme=S4, pattern="portas de parede (vídeo), versão andando",
        rhythm="respiro", difficulty=2, required=["walk", "jump"], optional=[],
        notes="Respiro e apresentação das portas: paredes finas com uma abertura de 2 blocos no chão (passa andando, "
        "não dá para pular dentro dela). Degraus de 1–2. Prepara a sala seguinte.",
    )


@chunk
def p_s4_portas() -> dict[str, Any]:
    walls = (2, 3, 2, 4, 3, 4, 2, 4, 3, 4, 4, 3)  # altura da base do furo, parede a parede
    w = 8 + 6 * len(walls) + 10
    g = G(w, 16).shell()
    floor = 1
    for n, b in enumerate(walls):
        i = 8 + 6 * n
        g.box(i, floor, i, 14, "x")
        g.box(i, floor + b, i, floor + b + 2, ".")  # furo de 3 de altura
        g.set(i, floor + b + 3, "f")  # pele de gelo em cima do furo
    g.ground(w - 8, w - 2, floor + 2)
    g.door("L", floor, "entry", "in").door("R", floor + 2, "exit", "out")
    return meta(
        "p-s4-portas", g, name="Casa das portas", theme=S4, pattern="portas de parede (vídeo)",
        rhythm="apertado", difficulty=4, required=["jump", "double"], optional=[],
        notes="Doze salas de 5 blocos separadas por paredes finas com um furo de 3 blocos de altura (o corpo tem 1,4) a "
        "2, 3 ou 4 blocos do chão: pulo simples ou pulo duplo bem medido, sala após sala. Em cima de cada furo, uma "
        "pele de gelo: quem pula alto demais congela ~1 s e cai na sala (perde tempo, nunca fica preso). Tudo "
        "Unhookable.",
    )


@chunk
def p_s4_valvulas() -> dict[str, Any]:
    g = G(80, 17).shell()
    low, top = 1, 9
    g.ground(1, 8, top)
    g.box(9, top - 1, 67, top - 1, "x")  # piso do corredor de cima
    g.oneway(11, top - 1, 13, top - 1, "Down")  # alçapões de mão única (desce, não sobe)
    g.oneway(40, top - 1, 42, top - 1, "Down")
    # corredor de cima (rápida): piso vermelho longo (15 blocos), teto prendível em cima, cortina de gelo no meio
    g.box(17, top - 1, 33, top - 1, "k")
    g.box(47, top - 1, 63, top - 1, "k")
    g.box(17, 16, 33, 16, "#")
    g.box(47, 16, 63, 16, "#")
    g.box(38, 12, 38, 15, "f")
    # corredor de baixo (segura): calombos, sem gancho
    for i0 in (12, 20, 28, 36, 44, 52, 58):
        g.ground(i0, i0 + 1, low + 2)
    g.ground(62, 64, low + 2)
    g.ground(65, 67, low + 4)
    g.ground(68, 70, top - 3)
    g.box(71, 1, 71, 15, "x")
    g.oneway(71, top - 3, 71, top + 1, "Right")  # válvula: passa para a direita, não volta
    g.ground(72, 78, top - 3)
    g.door("L", top, "entry", "in").door("R", top - 3, "exit", "out")
    lanes = [
        lane("cima", "corredor de cima: gancho no teto sobre o vermelho", "rapida", (16, 9, 67, 16)),
        lane("baixo", "corredor de baixo: a pé", "segura", (10, 1, 61, 6)),
    ]
    return meta(
        "p-s4-valvulas", g, name="Válvulas", theme=S4, pattern="original: corredores paralelos com mão única",
        rhythm="amplo", difficulty=3, required=[], optional=["hook", "momentum", "jump", "oneway", "kill", "freeze"],
        lanes=lanes,
        notes="Dois corredores. Em cima (rápida): dois trechos de 17 blocos de piso vermelho (longe demais para o pulo "
        "duplo) que se cruzam pendurado no teto prendível, com uma cortina de gelo entre eles (obriga a pousar no meio). "
        "Embaixo (segura): corredor a pé com calombos. Alçapões de MÃO ÚNICA (para baixo) no piso de cima deixam "
        "desistir para a rota de baixo, mas ninguém sobe por eles; no fim, uma válvula de mão única para a direita "
        "impede voltar. O validador trata mão única como ar (alçapão = buraco, válvula = abertura); as rotas dele "
        "andam no sentido da seta.",
    )



@chunk
def p_s4_dica() -> dict[str, Any]:
    g = G(80, 15).shell()
    top = 6
    g.ground(1, 8, top)
    red_pit(g, 9, 70, top, depth=4)
    g.box(9, 14, 70, 14, "#")  # teto todo prendível...
    g.box(27, 14, 35, 14, "x")  # ...menos a "dica negativa": 9 blocos sem gancho onde o próximo ponto estaria
    g.box(52, 14, 60, 14, "x")  # e outra antes da saída
    g.ground(36, 39, top)  # ilhas de pouso
    g.ground(59, 62, top)
    g.ground(71, 78, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s4-dica", g, name="Galeria do teto falso", theme=S4, pattern="dica negativa (vídeo) sobre o vermelho",
        rhythm="gargalo", difficulty=4, required=["hook", "momentum"], optional=["double", "kill"],
        notes="Galeria com piso vermelho e teto todo prendível: dá para atravessar pendurado, de gancho em gancho, até "
        "a 'dica negativa' — 9 blocos de teto sem gancho bem onde o próximo ponto estaria. Ali é preciso balançar, "
        "soltar no embalo e pousar numa ilha de 4; depois, outra faixa sem gancho e outra ilha antes da saída. Ensina que o xadrez "
        "no teto muda o plano.",
    )

@chunk
def p_s4_sala_um_ponto() -> dict[str, Any]:
    g = G(86, 22).shell()
    top = 5
    g.ground(1, 8, top)
    freeze_pit(g, 9, 30, top, depth=3)
    anchor(g, 17, 18, 13)  # o ponto da 1ª sala
    top2 = top + 4
    g.ground(31, 40, top2)  # patamar entre as salas (do fundo, só pelo gancho)
    freeze_pit(g, 41, 64, top2, depth=3)
    g.ground(41, 41, top2 - 1)
    anchor(g, 50, 51, top2 + 8)  # o ponto da 2ª sala, mais longe da borda
    g.ground(65, 84, top2 + 4)
    g.door("L", top, "entry", "in").door("R", top2 + 4, "exit", "out")
    return meta(
        "p-s4-sala-um-ponto", g, name="Sala de um ponto só", theme=S4, pattern="sala de um ponto só (vídeo), solo",
        rhythm="gargalo", difficulty=4, required=["hook"], optional=["momentum", "double", "unfreeze"],
        notes="Duas salas seguidas, todas Unhookable, cada uma com um único ponto prendível no alto; o chão é gelo falso "
        "sobre degelo (quem cai volta pelo degrau da entrada da sala). O ponto fica longe demais para prender parado "
        "na borda: é pular, prender no topo do pulo e soltar no embalo até a saída da sala, 4 blocos acima. A 2ª sala "
        "é mais larga. No vídeo o parceiro martelava; aqui o solo passa e a dupla só encurta. Fecha a seção 4.",
        checkpoint_end=True,
    )


# ==================================================================================================
# S5 — Poço Fundo (vertical: chaminés, furo que troca de lado, HookThrough)
# ==================================================================================================
S5 = "poco"


@chunk
def p_s5_descida() -> dict[str, Any]:
    g = G(70, 26).shell()
    feet = 20
    g.ground(1, 9, feet)
    x = 10
    for n in range(5):
        feet -= 4  # cada patamar 4 abaixo (queda visível, < 5 blocos)
        g.ground(x, x + 9, feet)
        g.box(x + 3, feet + 6, x + 3, 24, "f")  # cortina: quem pula alto em vez de descer congela
        x += 10
    g.ground(x, 68, feet)
    g.door("L", 20, "entry", "in").door("R", feet, "exit", "out")
    return meta(
        "p-s5-descida", g, name="Descida das cortinas", theme=S5, pattern="original: escada de descida com cortinas",
        rhythm="respiro", difficulty=2, required=["walk"], optional=["jump"],
        notes="Respiro depois do checkpoint: desce 20 blocos em cinco patamares de 10, 4 blocos de cada vez (a queda "
        "fica na tela). Cortinas de gelo penduradas alto só pegam quem pula à toa. Prepara a subida das chaminés.",
    )


@chunk
def p_s5_ilhas() -> dict[str, Any]:
    g = G(72, 18).shell()
    top = 6
    g.ground(1, 8, top)
    g.ground(10, 11, 4)  # degrau de volta (o fundo só volta para a esquerda)
    for i0, i1, feet in ((12, 16, 6), (20, 24, 7), (28, 32, 6), (37, 41, 7), (45, 49, 6), (53, 58, 7)):
        g.box(i0, feet - 1, i1, feet - 1, "h")  # ilhas HookThrough
    g.box(34, 9, 37, 9, "h")  # poleiro alto da rota de cima (pés 10)
    anchor(g, 18, 19, 14)
    anchor(g, 46, 47, 14)
    g.ground(62, 70, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    lanes = [
        lane("ganchos", "dois balanços por cima, com um poleiro alto", "rapida", (17, 9, 54, 16)),
        lane("ilhas", "de ilha em ilha", "segura", (12, 5, 58, 8)),
    ]
    return meta(
        "p-s5-ilhas", g, name="Ilhas suspensas", theme=S5, pattern="campo de ilhas flutuantes (vídeo), sem freeze",
        rhythm="amplo", difficulty=3, required=["jump"], optional=["hook", "momentum", "hookthrough"], lanes=lanes,
        notes="Campo de ilhas HookThrough (pisa, o gancho atravessa) com vãos de 3–4 e degraus de 1. Rápida: dois "
        "pontos de gancho altos e um poleiro no meio para atravessar em dois balanços. Segura: pular de ilha em ilha. "
        "Quem cai pousa no chão 5 blocos abaixo e volta pela esquerda (o fundo não leva à saída). Respiro antes da "
        "subida.",
    )


@chunk
def p_s5_chamine() -> dict[str, Any]:
    g = G(32, 34).shell()
    g.box(1, 0, 30, 32, "x")
    g.box(1, 1, 30, 5, ".")  # salão de baixo (pés na 1)
    # poço da esquerda (segura): 6 de largura, ressaltos HookThrough de 3 alternados a cada 3 blocos
    g.box(3, 6, 8, 26, ".")
    for k, j in enumerate(range(3, 27, 3)):
        side = 3 if k % 2 == 0 else 6
        g.box(side, j, side + 2, j, "h")
    # poço da direita (rápida): salão alto de 14 com pontos de gancho soltos, em zigue-zague
    g.box(14, 6, 27, 26, ".")
    for i, j in ((17, 9), (23, 15), (17, 21)):
        g.box(i, j, i + 1, j, "#")
    g.box(1, 28, 30, 32, ".")  # salão de cima (piso na linha 27, pés na 28)
    g.box(3, 27, 8, 27, ".")
    g.box(14, 27, 20, 27, ".")
    g.box(21, 27, 22, 27, "#")  # quina prendível da saída do poço da direita
    g.door("L", 1, "entry", "in").door("R", 28, "exit", "out")
    lanes = [
        lane("gancho", "salão da direita, de gancho em gancho", "rapida", (13, 6, 28, 27)),
        lane("degraus", "poço da esquerda, de ressalto em ressalto", "segura", (2, 6, 9, 26)),
    ]
    return meta(
        "p-s5-chamine", g, name="Chaminés gêmeas", theme=S5, pattern="chaminé / poço (vídeo)",
        rhythm="apertado", difficulty=4, required=[], optional=["double", "hook", "hookthrough", "jump"], lanes=lanes,
        notes="Subida de 27 blocos por dois caminhos paralelos. Esquerda (segura): poço de 6 com ressaltos HookThrough "
        "de 3 alternados a cada 3 blocos (oito pulos duplos curtos). Direita (rápida): salão alto com três pontos de gancho "
        "soltos em zigue-zague e a quina da saída prendível (gancho, solta, gancho). Quem cai volta ao salão de "
        "baixo, sem castigo. Lugar RESERVADO para o Bouncer: o chão embaixo do salão da direita (quando existir, "
        "ADR 0054, pode lançar direto para o meio da subida).",
    )


@chunk
def p_s5_furo() -> dict[str, Any]:
    g = G(26, 42).shell()
    g.box(1, 0, 24, 40, "x")
    floors = 9
    holes = (6, 18, 9, 16, 12, 20, 7, 17, 10)  # coluna do furo de cada andar (troca de lado)
    for k in range(floors):
        f = 1 + 4 * k
        g.box(1, f, 24, f + (4 if k == floors - 1 else 2), ".")  # sala de 3 de altura livre (a última, 5)
        if k + 1 < floors:
            h = holes[k + 1]
            g.box(h, f + 3, h + 2, f + 3, ".")  # furo de 3 no teto
    g.door("L", 1, "entry", "in", width=3).door("R", 1 + 4 * (floors - 1), "exit", "out")
    return meta(
        "p-s5-furo", g, name="Furo que troca de lado", theme=S5, pattern="furo que troca de lado (vídeo)",
        rhythm="gargalo", difficulty=3, required=["double"], optional=["jump"],
        notes="Nove salas empilhadas (3 blocos livres, piso de 1, tudo Unhookable) ligadas por um furo de 3 blocos no "
        "teto que troca de lado a cada andar. Sobe-se com pulo duplo na diagonal, passando pelo furo sem raspar a "
        "borda (precisão; o gancho não ajuda). Quem erra bate a cabeça e cai na própria sala (nada de queda longa). "
        "Furo de 1 bloco, como no vídeo, ficou impossível sozinho no validador (ver relatório). Fecha a seção 5.",
        checkpoint_end=True,
    )


# ==================================================================================================
# S6 — Cume (tudo junto: HookThrough, vermelho, verde, gelo, embalo)
# ==================================================================================================
S6 = "cume"


@chunk
def p_s6_mirante() -> dict[str, Any]:
    g = G(64, 14).shell()
    for i0, i1, feet in ((10, 19, 3), (20, 27, 2), (28, 37, 4), (38, 45, 3), (46, 62, 5)):
        g.ground(i0, i1, feet)
    g.door("L", 1, "entry", "in").door("R", 5, "exit", "out")
    return meta(
        "p-s6-mirante", g, name="Mirante", theme=S6, pattern="original: respiro antes do final",
        rhythm="respiro", difficulty=2, required=["jump"], optional=["walk"],
        notes="Respiro largo depois do checkpoint: patamares de 8–10, degraus de 1–2 e descidas a pé. Lugar para a dupla "
        "se reagrupar antes do final.",
    )


@chunk
def p_s6_gaiola() -> dict[str, Any]:
    g = G(92, 18).shell()
    top = 4
    g.ground(1, 8, top)
    g.box(1, 11, 90, 11, "h")  # teto de grade HookThrough, de parede a parede
    for i in range(12, 82, 7):
        g.box(i, 15, i + 1, 15, "#")  # pontos acima da grade
    plats = ((9, 14), (20, 24), (31, 35), (42, 46), (53, 57), (64, 68), (75, 80))
    for a, b in plats:
        g.ground(a, b, top)
    for (_, a), (b, _) in zip(plats, plats[1:]):
        red_pit(g, a + 1, b - 1, top, depth=2)
    g.box(22, top, 22, 8, "h")  # paredes de grade (o gancho atravessa, o corpo não)
    g.box(44, top, 44, 8, "h")
    g.box(66, top, 66, 8, "h")
    g.ground(81, 90, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s6-gaiola", g, name="Gaiola", theme=S6, pattern="original: gancho através da grade",
        rhythm="apertado", difficulty=4, required=["hook", "hookthrough"], optional=["momentum", "double", "kill"],
        notes="Corredor com teto de grade HookThrough: o gancho atravessa a grade e prende nos blocos de cima, e o "
        "corpo fica colado embaixo da grade. Piso de plataformas com seis vãos vermelhos de 5–6 e três paredes de grade "
        "de 5 blocos no caminho (o corpo bate, o gancho passa): passa-se pela fresta de 2 entre a parede e o teto, "
        "puxado pelo gancho ou num pulo duplo certeiro. Ensina a ler o preto.",
    )


@chunk
def p_s6_ponte() -> dict[str, Any]:
    g = G(72, 20).shell()
    top = 8
    g.ground(1, 9, top)
    red_pit(g, 10, 61, top, depth=6)
    anchor(g, 15, 16, 15)
    anchor(g, 22, 23, 15, ch="g")
    g.box(30, 1, 33, top - 1, "x")  # ilha
    g.box(35, 15, 36, 18, "f")  # cortina sobre a ilha: não pule alto demais
    anchor(g, 40, 41, 15, ch="g")
    g.box(47, 14, 48, 14, "k")  # ponto vermelho: prende, mas encostar volta ao checkpoint
    g.box(47, 15, 47, 18, "x")
    anchor(g, 54, 55, 15)
    g.ground(62, 70, top)
    g.box(4, top, 4, top + 4, "s")  # entra no modo solo (sem colisão nem gancho entre jogadores)
    g.box(66, top, 66, top + 4, "e")  # sai do modo solo
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    return meta(
        "p-s6-ponte", g, name="Ponte do cume", theme=S6, pattern="original: corrente de gancho com verde, vermelho e gelo",
        rhythm="gargalo", difficulty=5, required=["hook", "solo"], optional=["hookonce", "momentum", "double", "kill", "freeze"],
        notes="O gargalo final: 52 blocos de vermelho com uma ilha no meio. Primeira metade: um ponto normal e um "
        "VERDE (uso único), com pouso na ilha. Segunda: outro verde, um ponto VERMELHO (prende o gancho, mas encostar "
        "nele volta ao checkpoint) e um ponto normal antes da chegada. Uma cortina de gelo sobre a ilha castiga o "
        "pulo alto. Errou = checkpoint, e os verdes voltam. É TRECHO SOLO avisado (padrão do vídeo): linhas SoloStart e "
        "SoloEnd na entrada e na saída; cada um da dupla passa sozinho (placas com os ícones riscados ficam para o "
        "MapBuilder).",
    )


@chunk
def p_s6_reta() -> dict[str, Any]:
    g = G(76, 18).shell()
    top, low = 9, 4
    g.ground(1, 9, top)
    g.ground(10, 64, low)
    for i0 in (16, 26, 36, 46, 56):
        g.ground(i0, i0 + 2, low + 2)
    anchor(g, 19, 20, 15)
    g.box(30, top - 1, 31, top - 1, "h")  # poleiros entre os balanços
    anchor(g, 37, 38, 15)
    g.box(47, top - 1, 48, top - 1, "h")
    anchor(g, 54, 55, 15)
    g.ground(60, 64, low + 3)
    g.ground(65, 74, top)
    g.door("L", top, "entry", "in").door("R", top, "exit", "out")
    lanes = [
        lane("embalo", "balanços por cima, com poleiros", "rapida", (12, 9, 62, 16)),
        lane("chao", "a pé pelo vale", "segura", (11, 4, 58, 7)),
    ]
    return meta(
        "p-s6-reta", g, name="Reta final", theme=S6, pattern="original: bifurcação de chegada",
        rhythm="amplo", difficulty=3, required=["jump"], optional=["hook", "momentum", "double", "hookthrough"],
        lanes=lanes,
        notes="Chegada. Rápida: balanços por cima do vale, com dois poleiros HookThrough para pousar entre um e outro. "
        "Segura: descer 5 e atravessar o vale a pé, pulando cinco calombos, e subir no fim. Quem erra um balanço "
        "cai no vale e segue a pé. A chegada vem logo depois (montador).",
    )
