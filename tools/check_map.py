"""Confere por cálculo se cada pulo das rotas do mapa 3D cabe no pulo padrão do Roblox.

Não substitui jogar: é uma checagem de medidas (vão horizontal x subida) para cada salto entre duas
peças consecutivas de uma rota. Uso: python tools/check_map.py
"""

import math

import stages3d

GRAVITY = 196.2
JUMP_HEIGHT = 7.2  # Humanoid.JumpHeight padrão
WALK_SPEED = 16
MARGIN = 1.5  # folga para decolar antes da borda e pousar com o pé inteiro
JUMP_SPEED = math.sqrt(2 * GRAVITY * JUMP_HEIGHT)

# Rotas: nomes das peças na ordem em que o jogador pisa (sem o prefixo "E<n>_").
ROUTES = {
    1: {
        "principal": ["Entrada", "Plat1", "Plat2", "Plat3", "Plat4", "Saida"],
        "atalho": ["Entrada", "AtalhoViga", "Saida"],
    },
    2: {
        "principal": ["Entrada", "Passarela1", "Travessia1", "Passarela2", "Travessia2", "Passarela3",
                      "Travessia3", "Passarela4", "Travessia4", "Passarela5", "Saida"],
        "atalho": ["Entrada", "AtalhoPino1", "Travessia1", "AtalhoPino2", "Travessia2", "AtalhoPino3",
                   "Travessia3", "AtalhoPino4", "Travessia4", "AtalhoPino5", "Saida"],
    },
    3: {
        "principal": ["Entrada", "RampaSobe1", "Plato1", "RampaDesce", "RampaSobe2", "Plato2", "RampaDesce2", "Saida"],
        "atalho": ["Plato1", "AtalhoPonte1", "AtalhoPonte2", "Plato2"],
    },
    4: {
        "principal": ["Entrada", "Degrau1", "Degrau2", "Degrau3", "Degrau4", "Degrau5", "Degrau6", "Saida"],
        "atalho": ["Entrada", "AtalhoRampa1", "AtalhoRampa2", "AtalhoRampa3", "Saida"],
    },
    6: {
        "principal": ["Entrada", "Acesso", "Espiral1", "Espiral2", "Espiral3", "Espiral4", "Espiral5",
                      "Espiral6", "Espiral7", "Espiral8", "Pilar", "Chegada"],
        "atalho": ["Espiral5", "AtalhoPino1", "AtalhoPino2", "AtalhoPino3", "Chegada"],
    },
}


def reach(rise):
    """Distância horizontal máxima de um pulo que termina `rise` studs acima (negativo = abaixo)."""
    disc = JUMP_SPEED**2 - 2 * GRAVITY * rise
    if disc < 0:
        return 0.0
    return WALK_SPEED * (JUMP_SPEED + math.sqrt(disc)) / GRAVITY


def footprint(p):
    """(x1, x2, z1, z2) do topo da peça e uma função topo(x)."""
    cx, cy, cz = p["center"]
    sx, sy, sz = p["size"]
    if "top" in p:
        (xa, ya), (xb, yb) = p["top"]
        ox = cx - (xa + xb) / 2 + (-math.sin(math.radians(p["rotZ"])) * sy / 2)  # desfaz o recuo do centro
        x1, x2 = xa + ox, xb + ox
        return x1, x2, cz - sz / 2, cz + sz / 2, lambda x: ya + (yb - ya) * (min(max(x, x1), x2) - x1) / (x2 - x1)
    return cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2, lambda x: cy + sy / 2


def hop(a, b):
    ax1, ax2, az1, az2, atop = footprint(a)
    bx1, bx2, bz1, bz2, btop = footprint(b)
    dx = max(0, bx1 - ax2, ax1 - bx2)
    dz = max(0, bz1 - az2, az1 - bz2)
    xa = min(max((bx1 + bx2) / 2, ax1), ax2)  # ponto de A mais perto de B
    xb = min(max(xa, bx1), bx2)
    return math.hypot(dx, dz), btop(xb) - atop(xa)


def main():
    d = stages3d.build()
    parts = {p["name"]: p for p in d["parts"]}
    problems = 0
    for stage, routes in ROUTES.items():
        for route, names in routes.items():
            worst = ""
            ok = True
            for a, b in zip(names, names[1:]):
                gap, rise = hop(parts[f"E{stage}_{a}"], parts[f"E{stage}_{b}"])
                if gap < 0.01 and abs(rise) <= 1.01:
                    continue  # encostadas: é só andar
                limit = reach(rise) - MARGIN
                fits = rise <= JUMP_HEIGHT - 0.7 and gap <= limit
                line = f"{a} -> {b}: vao {gap:.1f}, subida {rise:+.1f}, limite {limit:.1f}"
                if not fits:
                    ok = False
                    problems += 1
                    print(f"  FALHA  estagio {stage} {route}: {line}")
                elif not worst or gap / limit > worst[0]:
                    worst = (gap / limit, line)
            status = "ok   " if ok else "FALHA"
            extra = f" | salto mais justo: {worst[1]}" if worst else " | so andar"
            print(f"{status} estagio {stage} {route}{extra}")
    print("estagio 5 (labirinto): so andar; passagens de 6 de largura, buracos do atalho com 4 x 7")
    print(f"{problems} problema(s)")


if __name__ == "__main__":
    main()
