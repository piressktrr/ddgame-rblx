"""Gera o mapa 3D em estágios (ADR 0029, 0031) a partir de definições de estágio em Python.

Cada estágio é um "prefab": peças em coordenadas locais, com entrada em (x=0, y=0) e saída em
(x=STAGE_LEN, y=exit_y). O gerador encaixa os estágios um depois do outro, somando X e Y.

Saídas em maps/map01-3d/:
  layout.json   lista de peças (fonte da verdade do greybox)
  build.luau    código que monta Workspace.Maps.Map01 no Studio (rodar via MCP)
  map01-3d.svg  vista de cima + perfil lateral, para revisar

Medidas do pulo padrão (JumpHeight 7,2 / WalkSpeed 16): alcance ~8,6 no mesmo nível e ~7,6 subindo 3.
Regra usada: vão <= 5 no mesmo nível; subida de 3 com vão <= 4,5.
Uso: python tools/stages3d.py
"""

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "maps" / "map01-3d"
STAGE_LEN = 96
WIDTH = 24  # largura das plataformas de entrada/saída
KILL_HEIGHT = -40

COLORS = {
    "solid": [163, 162, 165],
    "start": [90, 160, 110],
    "checkpoint": [255, 210, 63],
    "finish": [245, 245, 245],
    "shortcut": [120, 170, 220],
}


# Tags do CollectionService por tipo de peça (nomes iguais aos de src/shared/Config.luau).
KIND_TAGS = {"checkpoint": ["Checkpoint"], "finish": ["RaceFinish"]}


def box(name, x1, x2, y1, y2, z1, z2, kind="solid"):
    return {
        "name": name,
        "kind": kind,
        "center": [(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2],
        "size": [x2 - x1, y2 - y1, z2 - z1],
        "rotZ": 0,
        "tags": list(KIND_TAGS.get(kind, [])),
    }


def ramp(name, xa, ya, xb, yb, z1, z2, kind="solid", thick=2):
    """Rampa de (xa, ya) até (xb, yb), com o topo passando por esses pontos."""
    dx, dy = xb - xa, yb - ya
    length = math.hypot(dx, dy)
    ang = math.atan2(dy, dx)
    # desloca o centro para baixo (perpendicular) metade da espessura, para o topo ficar na linha
    nx, ny = -math.sin(ang), math.cos(ang)
    cx = (xa + xb) / 2 - nx * thick / 2
    cy = (ya + yb) / 2 - ny * thick / 2
    return {
        "name": name,
        "kind": kind,
        "center": [cx, cy, (z1 + z2) / 2],
        "size": [length, thick, z2 - z1],
        "rotZ": math.degrees(ang),
        "tags": [],
        "top": [[xa, ya], [xb, yb]],  # linha do topo, usada por tools/check_map.py
    }


def pads(entry_kind="solid", exit_y=0, exit_kind="checkpoint"):
    """Plataforma de entrada (x 0..12) e de saída (x 84..96)."""
    return [
        box("Entrada", 0, 12, -2, 0, -WIDTH / 2, WIDTH / 2, entry_kind),
        box("Saida", STAGE_LEN - 12, STAGE_LEN, exit_y - 2, exit_y, -WIDTH / 2, WIDTH / 2),
        box("SaidaMarco", STAGE_LEN - 8, STAGE_LEN - 4, exit_y, exit_y + 0.4, -WIDTH / 2, WIDTH / 2, exit_kind),
    ]


# ---------------------------------------------------------------- estágios
def stage1():
    """Aquecimento: plataformas com vãos curtos. Atalho: viga estreita contínua pela lateral."""
    p = pads()
    heights = [0, 1, 2, 1]
    xs = [(16, 28), (32, 44), (48, 60), (64, 80)]
    for i, ((a, b), h) in enumerate(zip(xs, heights)):
        p.append(box(f"Plat{i + 1}", a, b, h - 2, h, -5, 5))
    p.append(box("AtalhoViga", 12, 84, -1, 0, 8, 10, "shortcut"))
    return "Aquecimento", p, 0


def stage2():
    """Zigue-zague: passarela que vai e volta entre os dois lados (só andar).
    Atalho: pinos em linha reta pelo meio (pular no ritmo)."""
    p = pads()
    sides = {"A": (-12, -6), "B": (6, 12)}
    segs = [("A", 12, 28), ("B", 24, 44), ("A", 40, 60), ("B", 56, 76), ("A", 72, 84)]
    for i, (side, a, b) in enumerate(segs):
        z1, z2 = sides[side]
        p.append(box(f"Passarela{i + 1}", a, b, -2, 0, z1, z2))
    for i, a in enumerate([24, 40, 56, 72]):
        p.append(box(f"Travessia{i + 1}", a, a + 4, -2, 0, -6, 6))
    for i, a in enumerate([16.5, 32.5, 48.5, 64.5, 78.5]):
        p.append(box(f"AtalhoPino{i + 1}", a, a + 3, -1, 0, -1.5, 1.5, "shortcut"))
    return "Zigue-zague", p, 0


def stage3():
    """Rampas em V. Atalho: ponte estreita pela lateral cruzando o V, com um vão no meio."""
    p = pads()
    z1, z2 = -6, 6
    p += [
        ramp("RampaSobe1", 12, 0, 32, 8, z1, z2),
        box("Plato1", 32, 44, 6, 8, z1, z2),
        ramp("RampaDesce", 44, 8, 56, 0, z1, z2),
        ramp("RampaSobe2", 56, 0, 68, 8, z1, z2),
        box("Plato2", 68, 76, 6, 8, z1, z2),
        ramp("RampaDesce2", 76, 8, 84, 0, z1, z2),
        box("AtalhoPonte1", 44, 54, 7, 8, 6, 8, "shortcut"),
        box("AtalhoPonte2", 58, 68, 7, 8, 6, 8, "shortcut"),
    ]
    return "Rampas", p, 0


def stage4():
    """Serpentina subindo: degraus de +3 alternando lados.
    Atalho: rampa estreita pela borda, em 3 pedaços com vãos para pular."""
    top = 18
    p = pads(exit_y=top)
    for i in range(6):
        a = 14 + i * 12
        y = 3 * (i + 1)
        z1, z2 = (-9, -1) if i % 2 == 0 else (1, 9)
        p.append(box(f"Degrau{i + 1}", a, a + 8, y - 1, y, z1, z2))
    slope = top / 72  # linha de (12, 0) até (84, top)
    for i, (a, b) in enumerate([(12, 32), (36, 56), (60, 84)]):
        p.append(ramp(f"AtalhoRampa{i + 1}", a, (a - 12) * slope, b, (b - 12) * slope, 10, 12, "shortcut", thick=1))
    return "Serpentina", p, top


def stage5():
    """Labirinto de paredes alternadas. Atalho: buraco estreito no meio de duas paredes."""
    p = pads()
    p.append(box("Piso", 12, 84, -2, 0, -WIDTH / 2, WIDTH / 2))
    h, half = 9, WIDTH / 2
    for i, x in enumerate([24, 36, 48, 60, 72]):
        if i % 2 == 0:  # passagem do lado +Z
            p.append(box(f"Parede{i + 1}", x, x + 2, 0, h, -half, 6))
        else:  # passagem do lado -Z, com buraco (atalho) no meio
            p.append(box(f"Parede{i + 1}a", x, x + 2, 0, h, -6, -2))
            p.append(box(f"Parede{i + 1}b", x, x + 2, 0, h, 2, half))
            p.append(box(f"Parede{i + 1}Atalho", x, x + 2, 7, h, -2, 2, "shortcut"))
    return "Labirinto", p, 0


def stage6():
    """Torre final: espiral de degraus em volta de um pilar; do último degrau pula para o topo do
    pilar e dele para a chegada. Atalho: 3 pinos pequenos por fora, do 5º degrau direto à chegada."""
    top = 27
    p = [box("Entrada", 0, 12, -2, 0, -WIDTH / 2, WIDTH / 2)]
    cx = 48
    p.append(box("Pilar", cx - 4, cx + 4, -2, top, -4, 4))
    ring = [(-10, -10), (0, -10), (10, -10), (10, 0), (10, 10), (0, 10), (-10, 10), (-10, 0)]
    for i, (dx, dz) in enumerate(ring):
        y = 3 * (i + 1)
        p.append(box(f"Espiral{i + 1}", cx + dx - 4, cx + dx + 4, y - 1, y, dz - 4, dz + 4))
    p.append(box("Acesso", 16, 31, -2, 0, -14, -6))
    for i, a in enumerate([63, 69, 75]):
        y = 18 + 3 * i
        p.append(box(f"AtalhoPino{i + 1}", a, a + 3, y - 1, y, 13, 16, "shortcut"))
    p.append(box("Chegada", 56, STAGE_LEN, top - 2, top, -WIDTH / 2, WIDTH / 2))
    p.append(box("Fim", STAGE_LEN - 12, STAGE_LEN - 6, top, top + 0.4, -WIDTH / 2, WIDTH / 2, "finish"))
    return "Torre final", p, top


STAGES = [stage1, stage2, stage3, stage4, stage5, stage6]


# ---------------------------------------------------------------- montagem
def build():
    parts = [box("LobbyPiso", -40, 0, -2, 0, -20, 20, "start")]
    stages = []
    ox, oy = 0, 0
    for idx, fn in enumerate(STAGES, start=1):
        name, local, exit_y = fn()
        for part in local:
            c = part["center"]
            part = dict(part, center=[c[0] + ox, c[1] + oy, c[2]], stage=idx)
            part["name"] = f"E{idx}_{part['name']}"
            if part["kind"] == "checkpoint":
                part["attrs"] = {"Order": idx}
            parts.append(part)
        stages.append({"index": idx, "name": name, "x": ox, "y": oy, "exitY": oy + exit_y})
        ox += STAGE_LEN
        oy += exit_y
    return {
        "name": "Map01",
        "camera": "ThirdPerson",
        "stageLength": STAGE_LEN,
        "killHeight": KILL_HEIGHT,
        "spawn": [-20, 0, 0],
        "colors": COLORS,
        "stages": stages,
        "parts": parts,
    }


def num(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


def luau(d):
    """Código compacto: cada linha P(estágio, nome, tipo, centro xyz, tamanho xyz, rotZ[, order])."""
    kinds = ", ".join(f'{k} = Color3.fromRGB({c[0]}, {c[1]}, {c[2]})' for k, c in d["colors"].items())
    tags = ", ".join(f'{k} = "{v[0]}"' for k, v in KIND_TAGS.items())
    names = ", ".join(f'"{st["name"]}"' for st in d["stages"])
    out = [
        "-- GERADO por tools/stages3d.py. Não editar à mão.",
        'local CollectionService = game:GetService("CollectionService")',
        'local maps = workspace:FindFirstChild("Maps") or Instance.new("Folder")',
        'maps.Name = "Maps"',
        "maps.Parent = workspace",
        'local old = maps:FindFirstChild("Map01")',
        "if old then old:Destroy() end",
        'local model = Instance.new("Model")',
        'model.Name = "Map01"',
        f"local COLORS = {{ {kinds} }}",
        f"local TAGS = {{ {tags} }}",
        f"local STAGES = {{ {names} }}",
        "local folders = {}",
        "local function P(stage, name, kind, cx, cy, cz, sx, sy, sz, rz, order)",
        "\tlocal parent = model",
        "\tif stage > 0 then",
        "\t\tif not folders[stage] then",
        '\t\t\tlocal f = Instance.new("Model")',
        '\t\t\tf.Name = string.format("Estagio%d_%s", stage, STAGES[stage])',
        "\t\t\tf.Parent = model",
        "\t\t\tfolders[stage] = f",
        "\t\tend",
        "\t\tparent = folders[stage]",
        "\tend",
        '\tlocal p = Instance.new("Part")',
        "\tp.Name = name",
        "\tp.Anchored = true",
        "\tp.Size = Vector3.new(sx, sy, sz)",
        "\tp.CFrame = CFrame.new(cx, cy, cz) * CFrame.Angles(0, 0, math.rad(rz))",
        "\tp.Color = COLORS[kind]",
        '\tp:SetAttribute("Kind", kind)',
        '\tif order then p:SetAttribute("Order", order) end',
        "\tif TAGS[kind] then CollectionService:AddTag(p, TAGS[kind]) end",
        "\tp.Parent = parent",
        "end",
    ]
    for p in d["parts"]:
        c, s = p["center"], p["size"]
        vals = ", ".join(num(v) for v in (*c, *s, p["rotZ"]))
        order = p.get("attrs", {}).get("Order")
        tail = f", {order}" if order else ""
        out.append(f'P({p.get("stage", 0)}, "{p["name"]}", "{p["kind"]}", {vals}{tail})')
    sx, sy, sz = d["spawn"]
    out += [
        'local spawn = Instance.new("SpawnLocation")',
        'spawn.Name = "Spawn"',
        "spawn.Anchored = true",
        "spawn.Neutral = true",
        "spawn.Duration = 0",
        "spawn.Size = Vector3.new(6, 1, 6)",
        f"spawn.CFrame = CFrame.lookAlong(Vector3.new({sx}, {sy} + 0.5, {sz}), Vector3.xAxis)",
        "spawn.Parent = model",
        "model.Parent = maps",
        f"workspace.FallenPartsDestroyHeight = {d['killHeight']}",
        "return #model:GetDescendants()",
    ]
    return "\n".join(out) + "\n"


def svg(d):
    xs = [p["center"][0] for p in d["parts"]]
    x0, x1 = min(xs) - 20, max(xs) + 20
    s = 1.6
    w = (x1 - x0) * s
    top_h, side_h, pad = 40 * s, 50 * s, 30
    h = top_h + side_h + 3 * pad

    def X(v):
        return (v - x0) * s

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="sans-serif">',
           f'<rect width="{w:.0f}" height="{h:.0f}" fill="#1b1d24"/>',
           f'<text x="8" y="18" fill="#c9cbe0" font-size="13">Vista de cima</text>',
           f'<text x="8" y="{top_h + 2 * pad + 4:.0f}" fill="#c9cbe0" font-size="13">Perfil (altura)</text>']
    for st in d["stages"]:
        out.append(f'<line x1="{X(st["x"]):.0f}" y1="22" x2="{X(st["x"]):.0f}" y2="{h - 6:.0f}" stroke="#3a3f4f" stroke-dasharray="4 4"/>')
        out.append(f'<text x="{X(st["x"]) + 4:.0f}" y="{pad + top_h + pad - 6:.0f}" fill="#c9cbe0" font-size="12">{st["index"]}. {st["name"]}</text>')
    for p in d["parts"]:
        (cx, cy, cz), (sx, sy, sz) = p["center"], p["size"]
        r, g, b = d["colors"][p["kind"]]
        ex = sx * abs(math.cos(math.radians(p["rotZ"])))
        out.append(f'<rect x="{X(cx - ex / 2):.1f}" y="{pad + (cz - sz / 2 + 20) * s:.1f}" width="{ex * s:.1f}" height="{sz * s:.1f}" fill="rgb({r},{g},{b})" fill-opacity="0.8"/>')
        base = top_h + 2 * pad + 10
        ey = sy if p["rotZ"] == 0 else sx * abs(math.sin(math.radians(p["rotZ"]))) + sy
        out.append(f'<rect x="{X(cx - ex / 2):.1f}" y="{base + (35 - cy - ey / 2) * s:.1f}" width="{ex * s:.1f}" height="{max(ey * s, 1):.1f}" fill="rgb({r},{g},{b})" fill-opacity="0.8"/>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    (OUT / "layout.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf8", newline="\n")
    (OUT / "build.luau").write_text(luau(d), encoding="utf8", newline="\n")
    (OUT / "map01-3d.svg").write_text(svg(d), encoding="utf8", newline="\n")
    print(f"ok: {len(d['parts'])} pecas, {len(d['stages'])} estagios")


if __name__ == "__main__":
    main()
