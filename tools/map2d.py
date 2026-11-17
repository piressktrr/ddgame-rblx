"""Greybox do mapa 2.5D (layout v3, Fase 2) para o Studio, a partir de `tools/map_layout.py`.

Gera em maps/map01/:
  - layout.json : peças (nome, tipo, classe, centro, tamanho, rotação em Z, tags e atributos)
  - build.luau  : monta Workspace.Maps.Map01 no Studio (apaga o antigo antes). Rodar em modo Edit,
                  pelo MCP `execute_luau` ou na barra de comandos.
  - map01.svg   : vista lateral das peças geradas (o que o build.luau monta) com as rotas do rascunho

Como funciona: o layout é pintado numa grade de 1 stud dentro da caixa do mapa (ar + margem de rocha),
na ordem das formas: ar abre, sólido fecha (rocha), zonas (mortal, gelo, descongelar, checkpoint, fim,
início) só ocupam o que não é rocha, roxo e verde cobrem tudo. Sólido com atributos (ex.:
`RequiresHookLevel`) vira peça própria. Cada tipo é juntado em poucos retângulos (junção gulosa).
Bordas inclinadas do ar viram WedgePart, e zonas desenhadas como polígono inclinado viram uma Part
girada em Z. Placas (`Sign`) e pontos reservados (`Reserved`) ficam fora da grade.

Ajuste do 3D (não muda o desenho): uma zona apoiada numa faixa mortal desce até o chão, para a
faixa mortal não ficar embaixo dela (ex.: gelo e laranja no fundo do E6 viram ilhas no chão mortal).

Uso: python -I -X utf8 tools/map2d.py [--check caminho.luau]
     --check também grava um script Luau de verificação (contagens e ar livre) para rodar no Studio.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # `python -I` não põe a pasta do script no path

import map_layout as L  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "maps" / "map01"
NAME = "Map01"
DEPTH = 12  # profundidade das peças do plano (Z de -6 a 6)
MARGIN = 10  # rocha em volta do ar
BACKDROP_Z = -10  # parede de fundo, atrás do plano (a câmera fica em +Z)
MIN_CLEARANCE = 7  # altura mínima de passagem
MIN_WIDTH = 4  # largura mínima de passagem

# Tipos do desenho -> tipos do greybox.
SKETCH_KIND = {
    "solid": "Rock",
    "kill": "Kill",
    "ice": "Ice",
    "unfreeze": "Unfreeze",
    "nohook": "NoHook",
    "hookonce": "HookOnce",
    "checkpoint": "Checkpoint",
    "start": "Spawn",
    "finish": "Finish",
}
# Zonas pintam só sobre ar (ou zona anterior), na ordem: as últimas ganham.
ZONE_ORDER = ["Kill", "Ice", "Unfreeze", "Checkpoint", "Spawn", "Finish"]
# Variantes de sólido: pintam por cima de tudo.
SOLID_VARIANTS = ["NoHook", "HookOnce"]
COLLIDABLE_ZONES = {"Ice", "Unfreeze", "Checkpoint", "Spawn", "Finish"}  # zonas que descem até o chão

KINDS = {
    "Rock": {"color": L.COL["rock"], "tags": [], "label": "rocha e sólidos (gancho gruda)"},
    "SlopeR": {"color": L.COL["rock"], "tags": [], "class": "WedgePart", "yaw": -90,
               "label": "rampa de rocha, sobe para a esquerda"},
    "SlopeL": {"color": L.COL["rock"], "tags": [], "class": "WedgePart", "yaw": 90,
               "label": "rampa de rocha, sobe para a direita"},
    "Kill": {"color": L.COL["kill"], "tags": ["KillZone"], "label": "mortal (sólida e grudável, ADR 0049)"},
    "Ice": {"color": L.COL["ice"], "tags": ["FreezeZone"], "label": "gelo"},
    "Unfreeze": {"color": L.COL["unfreeze"], "tags": ["UnfreezeZone"], "label": "descongelar"},
    "NoHook": {"color": L.COL["nohook"], "tags": ["NoHook"], "label": "não gruda"},
    "HookOnce": {"color": L.COL["hookonce"], "tags": ["HookOnce"], "label": "gruda 1 vez"},
    "Checkpoint": {"color": L.COL["checkpoint"], "tags": ["Checkpoint"], "label": "checkpoint (atributo Order)"},
    "Finish": {"color": L.COL["finish"], "tags": ["RaceFinish", "Checkpoint"], "label": "fim (também o último checkpoint)"},
    "Spawn": {"color": L.COL["start"], "tags": ["RaceStart"], "class": "SpawnLocation", "depth": 1,
              "label": "início da corrida (SpawnLocation desligado; nasce-se no lobby, ADR 0044)"},
    "Backdrop": {"color": "#23252c", "tags": [], "collide": False, "ghost": True, "z": BACKDROP_Z, "depth": 1,
                 "label": "fundo, não gruda"},
    "Sign": {"color": L.COL["sign"], "tags": [], "collide": False, "ghost": True, "z": -9.3, "depth": 0.4,
             "label": "placa no fundo (estágio), texto na face +Z"},
    "Reserved": {"color": L.COL["reserved"], "tags": [], "collide": False, "ghost": True, "transparency": 0.8,
                 "depth": 6, "label": "ponto reservado (fases 4 e 5), sem efeito; atributo Reserved"},
}
SIGN_DEPTH = KINDS["Sign"]["depth"]
RESERVED_SIZE = 6

ROCK, AIR = 0, 1


# ---------------------------------------------------------------- geometria


def is_rect(pts):
    return len(pts) == 4 and len({x for x, _ in pts}) == 2 and len({y for _, y in pts}) == 2


def bbox(pts):
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def inside(pt, pts):
    """Ponto dentro do polígono (paridade de cruzamentos)."""
    x, y = pt
    c = False
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i], pts[i - 1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def slope_wedges(pts):
    """Triângulos de rocha sob as bordas inclinadas de um polígono de ar."""
    out = []
    for i in range(len(pts)):
        a, b = pts[i - 1], pts[i]
        if a[0] == b[0] or a[1] == b[1]:
            continue
        for c in ((a[0], b[1]), (b[0], a[1])):
            centroid = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)
            if not inside(centroid, pts):
                break
        else:
            raise ValueError(f"borda inclinada sem lado de rocha: {a} {b}")
        x1, y1, x2, y2 = bbox([a, b, c])
        if c[1] != y1:
            raise NotImplementedError("rampa de teto (canto reto em cima) ainda não é suportada")
        kind = "SlopeR" if c[0] == x1 else "SlopeL"
        out.append({"tri": [a, b, c], "kind": kind, "box": (x1, y1, x2, y2)})
    return out


def oriented_box(pts):
    """Retângulo girado que cobre um polígono, alinhado à sua borda mais longa."""
    best = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[i - 1][0]) ** 2 + (pts[i][1] - pts[i - 1][1]) ** 2)
    (ax, ay), (bx, by) = pts[best - 1], pts[best]
    ln = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    ux, uy = (bx - ax) / ln, (by - ay) / ln
    if ux < 0:
        ux, uy = -ux, -uy
    nx, ny = -uy, ux
    us = [(x - ax) * ux + (y - ay) * uy for x, y in pts]
    ns = [(x - ax) * nx + (y - ay) * ny for x, y in pts]
    cu, cn = (min(us) + max(us)) / 2, (min(ns) + max(ns)) / 2
    return {
        "center": (ax + ux * cu + nx * cn, ay + uy * cu + ny * cn),
        "size": (max(us) - min(us), max(ns) - min(ns)),
        "rotZ": math.degrees(math.atan2(uy, ux)),
    }


# ---------------------------------------------------------------- grade


class Grid:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.w, self.h = x0, y0, x1 - x0, y1 - y0
        self.c = [[ROCK] * self.w for _ in range(self.h)]

    def cells(self, x1, y1, x2, y2):
        """(linha, índice, x, y) de cada célula do retângulo, recortado à caixa."""
        for y in range(max(y1, self.y0), min(y2, self.y0 + self.h)):
            row = self.c[y - self.y0]
            for x in range(max(x1, self.x0), min(x2, self.x0 + self.w)):
                yield row, x - self.x0, x, y

    def get(self, x, y):
        if self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h:
            return self.c[y - self.y0][x - self.x0]
        return ROCK

    def by_owner(self):
        out = {}
        for iy, row in enumerate(self.c):
            for ix, o in enumerate(row):
                out.setdefault(o, []).append((ix, iy))
        return out


def merge(grid, pts):
    """Junção gulosa das células `pts` em retângulos; testa linhas primeiro e colunas primeiro e
    fica com o que der menos peças."""
    if not pts:
        return []

    def run(transpose):
        used = set()
        rects = []
        order = sorted(pts, key=(lambda p: (p[0], p[1])) if transpose else (lambda p: (p[1], p[0])))
        on = set(pts)
        for ix, iy in order:
            if (ix, iy) in used:
                continue
            if not transpose:
                rw = 1
                while (ix + rw, iy) in on and (ix + rw, iy) not in used:
                    rw += 1
                rh = 1
                while all((ix + k, iy + rh) in on and (ix + k, iy + rh) not in used for k in range(rw)):
                    rh += 1
            else:
                rh = 1
                while (ix, iy + rh) in on and (ix, iy + rh) not in used:
                    rh += 1
                rw = 1
                while all((ix + rw, iy + k) in on and (ix + rw, iy + k) not in used for k in range(rh)):
                    rw += 1
            for a in range(rw):
                for b in range(rh):
                    used.add((ix + a, iy + b))
            rects.append((grid.x0 + ix, grid.y0 + iy, grid.x0 + ix + rw, grid.y0 + iy + rh))
        assert used == on
        return rects

    a, b = run(False), run(True)
    return a if len(a) <= len(b) else b


# ---------------------------------------------------------------- montagem


def build():
    shapes = list(L.shapes)
    air = [s for s in shapes if s[0] == "air"]
    ax1, ay1, ax2, ay2 = bbox([p for _, pts, _ in air for p in pts])
    box = (int(ax1) - MARGIN, int(ay1) - MARGIN, int(ax2) + MARGIN, int(ay2) + MARGIN)
    grid = Grid(*box)
    owners = {ROCK: ("Rock", "Rock", {}), AIR: ("Air", "Air", {})}  # dono -> (tipo, grupo, atributos)
    wedges, tilted, notes = [], [], []
    next_owner = 2

    def is_solid_owner(o):
        return o == ROCK or (o > AIR and owners[o][0] in SOLID_VARIANTS + ["Rock"])

    # Uma passada, na ordem das formas: ar abre, sólido fecha, zonas só onde não é sólido, roxo e
    # verde (e sólido com atributos) cobrem tudo.
    for index, (k, pts, g) in enumerate(shapes):
        extra = L.attrs.get(index, {})
        if k == "air":
            if is_rect(pts):
                x1, y1, x2, y2 = (int(v) for v in bbox(pts))
                for row, i, _, _ in grid.cells(x1, y1, x2, y2):
                    row[i] = AIR
                continue
            # polígono: os triângulos das rampas também são ar; a rampa vira WedgePart
            ws = slope_wedges(pts)
            for wdg in ws:
                wdg["group"] = g
            wedges += ws
            x1, y1, x2, y2 = (int(v) for v in bbox(pts))
            for row, i, x, y in grid.cells(x1, y1, x2, y2):
                p = (x + 0.5, y + 0.5)
                if inside(p, pts) or any(inside(p, wdg["tri"]) for wdg in ws):
                    row[i] = AIR
            continue
        if k == "solid" and not extra:
            if not is_rect(pts):
                raise NotImplementedError("sólido não retangular")
            x1, y1, x2, y2 = (int(v) for v in bbox(pts))
            for row, i, _, _ in grid.cells(x1, y1, x2, y2):
                row[i] = ROCK
            continue
        kind = "Rock" if k == "solid" else SKETCH_KIND[k]
        if not is_rect(pts):
            tilted.append({"kind": kind, "group": g, "attributes": extra, **oriented_box(pts)})
            continue
        owners[next_owner] = (kind, g, extra)
        x1, y1, x2, y2 = (int(v) for v in bbox(pts))
        covers = kind in SOLID_VARIANTS or kind == "Rock"
        skipped = 0
        for row, i, _, _ in grid.cells(x1, y1, x2, y2):
            if covers or not is_solid_owner(row[i]):
                row[i] = next_owner
            else:
                skipped += 1
        if skipped:
            notes.append(f"{g} {kind} ({x1},{y1})-({x2},{y2}): {skipped} células sobre sólido ficaram de fora")
        next_owner += 1

    # zona apoiada em faixa mortal desce até o chão
    lowered = {}
    for iy in range(grid.h):
        for ix in range(grid.w):
            o = grid.c[iy][ix]
            if o > AIR and owners[o][0] in COLLIDABLE_ZONES:
                y = iy - 1
                while y >= 0 and grid.c[y][ix] > AIR and owners[grid.c[y][ix]][0] == "Kill":
                    grid.c[y][ix] = o
                    lowered.setdefault(o, set()).add(grid.x0 + ix)
                    y -= 1
    for o, xs in lowered.items():
        notes.append(f"{owners[o][1]} {owners[o][0]} x {min(xs)}..{max(xs) + 1}: desceu até o chão, sobre a faixa mortal")
    return grid, box, owners, wedges, tilted, notes


def parts_from(grid, box, owners, wedges, tilted):
    parts = []
    counters = {}

    def name(group, kind):
        key = (group, kind)
        counters[key] = counters.get(key, 0) + 1
        return f"{group}_{kind}{counters[key]}"

    def add(nm, kind, cx, cy, w, h, rot=0.0):
        k = KINDS[kind]
        part = {
            "name": nm,
            "kind": kind,
            "class": k.get("class", "Part"),
            "center": [round(cx, 3), round(cy, 3), k.get("z", 0)],
            "size": [round(w, 3), round(h, 3), k.get("depth", DEPTH)],
        }
        if rot:
            part["rotZ"] = round(rot, 3)
        if "yaw" in k:
            part["slopeFaces"] = "+X" if kind == "SlopeR" else "-X"
        if k["tags"]:
            part["tags"] = list(k["tags"])
        parts.append(part)
        return part

    cells = grid.by_owner()
    for i, (x1, y1, x2, y2) in enumerate(merge(grid, cells.get(ROCK, [])), 1):
        add(f"Rock{i:03d}", "Rock", (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
    for wdg in wedges:
        x1, y1, x2, y2 = wdg["box"]
        add(name(wdg["group"], "Slope"), wdg["kind"], (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
    for kind in ZONE_ORDER + SOLID_VARIANTS + ["Rock"]:
        for o, (k, g, extra) in owners.items():
            if k != kind or o <= AIR:
                continue
            for x1, y1, x2, y2 in merge(grid, cells.get(o, [])):
                label = "HookLv" + str(extra["RequiresHookLevel"]) + "_" if "RequiresHookLevel" in extra else kind
                part = add(name(g, label), kind, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
                if extra:
                    part["attributes"] = dict(extra)
        for t in tilted:
            if t["kind"] == kind:
                part = add(name(t["group"], kind), kind, *t["center"], *t["size"], t["rotZ"])
                if t["attributes"]:
                    part["attributes"] = dict(t["attributes"])
    for nm, x, y, w, h, text in L.signs:
        add(nm, "Sign", x, y, w, h)["text"] = text
    for g, x, y, what, note in L.reserved:
        part = add(name(g, "Reserved" + what), "Reserved", x, y, RESERVED_SIZE, RESERVED_SIZE)
        part["attributes"] = {"Reserved": what, "Note": note}
    bx1, by1, bx2, by2 = box
    add("Backdrop", "Backdrop", (bx1 + bx2) / 2, (by1 + by2) / 2, bx2 - bx1, by2 - by1)
    return parts


# ---------------------------------------------------------------- conferências


def checks(grid, owners):
    """Passagens baixas ou estreitas demais (só ar conta como espaço livre; a faixa mortal é sólida)."""

    def free(x, y):
        return grid.get(x, y) == AIR

    low, narrow = {}, {}
    for x in range(grid.x0, grid.x0 + grid.w):
        for y in range(grid.y0 + 1, grid.y0 + grid.h):
            if free(x, y) and not free(x, y - 1):
                n = 0
                while free(x, y + n):
                    n += 1
                if n < MIN_CLEARANCE:
                    low.setdefault((y, n), []).append(x)
    for y in range(grid.y0, grid.y0 + grid.h):
        for x in range(grid.x0 + 1, grid.x0 + grid.w):
            if free(x, y) and not free(x - 1, y):
                n = 0
                while free(x + n, y):
                    n += 1
                if n < MIN_WIDTH:
                    narrow.setdefault((x, n), []).append(y)
    out = []
    for (y, n), xs in sorted(low.items()):
        out.append(f"passagem baixa: {n} studs acima de y={y}, x {min(xs)}..{max(xs) + 1}")
    for (x, n), ys in sorted(narrow.items()):
        out.append(f"passagem estreita: {n} studs a partir de x={x}, y {min(ys)}..{max(ys) + 1}")
    return out


def free_air_rects(grid, owners):
    """Ar (e zonas que o script de conferência não conta como sólido) que nenhuma peça sólida pode
    ocupar, em retângulos. Mortal, roxo, verde e rocha com atributo são sólidos e ficam de fora."""
    pts = [
        (ix, iy)
        for iy, row in enumerate(grid.c)
        for ix, o in enumerate(row)
        if o == AIR or (o > AIR and owners[o][0] not in SOLID_VARIANTS + ["Kill", "Rock"])
    ]
    return merge(grid, pts)


# ---------------------------------------------------------------- saída


def fmt(v):
    return f"{v:.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def luau(parts, fallen):
    kinds = []
    for kind, k in KINDS.items():
        fields = [f'color = Color3.fromHex("{k["color"].lstrip("#")}")']
        if k["tags"]:
            fields.append("tags = { " + ", ".join(f'"{t}"' for t in k["tags"]) + " }")
        if "class" in k:
            fields.append(f'class = "{k["class"]}"')
        if "yaw" in k:
            fields.append(f'yaw = {k["yaw"]}')
        if k.get("collide") is False:
            fields.append("collide = false")
        if k.get("ghost"):
            fields.append("ghost = true")
        if "z" in k:
            fields.append(f'z = {k["z"]}')
        if "depth" in k:
            fields.append(f'depth = {k["depth"]}')
        if "transparency" in k:
            fields.append(f'transparency = {k["transparency"]}')
        kinds.append(f"\t{kind} = {{ {', '.join(fields)} }}, -- {k['label']}")
    head = f"""--!strict
-- GERADO por tools/map2d.py a partir de tools/map_layout.py (layout {L.VERSION}). Não editar à mão.
-- Monta Workspace.Maps.{NAME} (greybox 2.5D, plano Z = 0, X horizontal, Y altura, studs).
-- Rodar no Studio em modo Edit (MCP execute_luau ou barra de comandos). Apaga o {NAME} antigo antes.
type Kind = {{
	color: Color3,
	tags: {{ string }}?,
	class: string?,
	yaw: number?,
	collide: boolean?,
	ghost: boolean?,
	z: number?,
	depth: number?,
	transparency: number?,
}}
local KINDS: {{ [string]: Kind }} = {{
{chr(10).join(kinds)}
}}

local maps = workspace:FindFirstChild("Maps") or Instance.new("Folder")
maps.Name = "Maps"
maps.Parent = workspace
local old = maps:FindFirstChild("{NAME}")
if old then
	old:Destroy()
end
local model = Instance.new("Model")
model.Name = "{NAME}"

-- Peça com centro (x, y) e tamanho (w, h) no plano; rz = giro em Z (graus). Rampas: WedgePart
-- deitada no plano (yaw -90 = rampa virada para +X, sobe para a esquerda; yaw 90 = o contrário).
local function p(
	name: string,
	kind: string,
	x: number,
	y: number,
	w: number,
	h: number,
	rz: number?
): BasePart
	local k = KINDS[kind]
	local part = Instance.new(k.class or "Part") :: BasePart
	local depth = k.depth or {DEPTH}
	if k.yaw then
		part.Size = Vector3.new(depth, h, w)
		part.CFrame = CFrame.new(x, y, 0) * CFrame.Angles(0, math.rad(k.yaw), 0)
	else
		part.Size = Vector3.new(w, h, depth)
		part.CFrame = CFrame.new(x, y, k.z or 0) * CFrame.Angles(0, 0, math.rad(rz or 0))
	end
	part.Name = name
	part.Anchored = true
	part.Color = k.color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.CanCollide = k.collide ~= false
	part.Transparency = k.transparency or 0
	if k.ghost then
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
	end
	if part:IsA("SpawnLocation") then
		-- Desligado: o jogador nasce no lobby (ADR 0044); a tag RaceStart marca o início.
		part.Enabled = false
		part.Neutral = true
		part.Duration = 0
	end
	part:SetAttribute("Kind", kind)
	for _, tag in k.tags or {{}} do
		part:AddTag(tag)
	end
	part.Parent = model
	return part
end

-- Atributos da peça (Order dos checkpoints, RequiresHookLevel, Reserved...).
local function set(part: BasePart, attributes: {{ [string]: any }})
	for key, value in attributes do
		part:SetAttribute(key, value)
	end
end

-- Placa de texto no fundo (SurfaceGui na face +Z, a que olha para a câmera), como no tutorial.
local function sign(name: string, x: number, y: number, w: number, h: number, text: string)
	local part = p(name, "Sign", x, y, w, h)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Text"
	gui.Face = Enum.NormalId.Back
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 20
	gui.LightInfluence = 0
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = text
	label.TextScaled = true
	label.TextWrapped = true
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = Color3.fromHex("ffffff")
	label.Parent = gui
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, 12)
	padding.PaddingRight = UDim.new(0, 12)
	padding.PaddingTop = UDim.new(0, 8)
	padding.PaddingBottom = UDim.new(0, 8)
	padding.Parent = label
end
"""
    lines = []
    for pt in parts:
        cx, cy, _ = pt["center"]
        w, h, _ = pt["size"]
        if pt["kind"] == "Sign":
            lines.append(f'sign("{pt["name"]}", {fmt(cx)}, {fmt(cy)}, {fmt(w)}, {fmt(h)}, "{pt["text"]}")')
            continue
        args = [f'"{pt["name"]}"', f'"{pt["kind"]}"', fmt(cx), fmt(cy), fmt(w), fmt(h)]
        if "rotZ" in pt:
            args.append(fmt(pt["rotZ"]))
        line = f"p({', '.join(args)})"
        if pt.get("attributes"):
            fields = ", ".join(f'{key} = {f"\"{val}\"" if isinstance(val, str) else fmt(val)}'
                               for key, val in pt["attributes"].items())
            line = f"set({line}, {{ {fields} }})"
        lines.append(line)
    tail = f"""
model.Parent = maps
workspace.FallenPartsDestroyHeight = math.min(workspace.FallenPartsDestroyHeight, {fallen})
return #model:GetChildren()
"""
    return head + "\n".join(lines) + "\n" + tail


def check_luau(parts, air_rects, has_wedges):
    """Script de verificação: contagens por tag e por Kind, Order dos checkpoints, início, ar livre,
    zona mortal sólida, placas, reservados e a rota que exige nível."""
    rects = ",\n".join("\t{" + ", ".join(str(v) for v in r) + "}" for r in air_rects)
    expected, kinds = {}, {}
    for pt in parts:
        for t in pt.get("tags", []):
            expected[t] = expected.get(t, 0) + 1
        if pt["kind"] in ("Sign", "Reserved"):
            kinds[pt["kind"]] = kinds.get(pt["kind"], 0) + 1
    exp = ", ".join(f"{t} = {n}" for t, n in sorted(expected.items()))
    expk = ", ".join(f"{t} = {n}" for t, n in sorted(kinds.items()))
    lv2 = sum(1 for pt in parts if "RequiresHookLevel" in pt.get("attributes", {}))
    ramps = RAMPS if has_wedges else ""
    return f"""-- Verificação do {NAME} (gerado por tools/map2d.py --check). Só lê, não muda nada.
local CollectionService = game:GetService("CollectionService")
local model = workspace.Maps.{NAME}
local out = {{}}
local function say(s) table.insert(out, s) end
say("pecas: " .. #model:GetChildren())
local expected = {{ {exp} }}
for tag, n in expected do
	local got = 0
	for _, inst in CollectionService:GetTagged(tag) do
		if inst:IsDescendantOf(model) then got += 1 end
	end
	say(tag .. ": " .. got .. (got == n and "" or (" (esperado " .. n .. ")")))
end
local kindsExpected = {{ {expk} }}
for kind, n in kindsExpected do
	local got, ok = 0, 0
	for _, c in model:GetChildren() do
		if c:GetAttribute("Kind") == kind then
			got += 1
			if not c.CanCollide and not c.CanQuery and not c.CanTouch then ok += 1 end
		end
	end
	say("Kind " .. kind .. ": " .. got .. ", sem colisao/consulta/toque: " .. ok .. (got == n and ok == n and "" or (" (esperado " .. n .. ")")))
end
for _, inst in CollectionService:GetTagged("Checkpoint") do
	if inst:IsDescendantOf(model) then
		say("checkpoint " .. inst.Name .. " Order=" .. tostring(inst:GetAttribute("Order")) .. " em " .. tostring(inst.Position))
	end
end
local killSoft = 0
for _, inst in CollectionService:GetTagged("KillZone") do
	if inst:IsDescendantOf(model) and not (inst.CanCollide and inst.CanQuery) then killSoft += 1 end
end
say("KillZone sem colisao ou consulta: " .. killSoft .. " (esperado 0, ADR 0049)")
local lv2 = {{}}
for _, c in model:GetChildren() do
	if c:GetAttribute("RequiresHookLevel") == 2 then table.insert(lv2, c.Name) end
end
say("RequiresHookLevel = 2: " .. #lv2 .. (#lv2 == {lv2} and "" or " (esperado {lv2})") .. " " .. table.concat(lv2, ","))
for _, inst in CollectionService:GetTagged("RaceStart") do
	say("RaceStart " .. inst:GetFullName() .. " @ " .. tostring(inst.Position) .. " Enabled=" .. tostring((inst :: any).Enabled))
end
local spawns = {{}}
for _, d in workspace:GetDescendants() do
	if d:IsA("SpawnLocation") then table.insert(spawns, d:GetFullName() .. " @ " .. tostring(d.Position) .. " Enabled=" .. tostring(d.Enabled)) end
end
say("spawns: " .. table.concat(spawns, " | "))
local solids = {{}}
for _, c in model:GetChildren() do
	if c:IsA("Part") and c.CanCollide and c:GetAttribute("Kind") ~= "Checkpoint" and c:GetAttribute("Kind") ~= "Ice"
		and c:GetAttribute("Kind") ~= "Unfreeze" and c:GetAttribute("Kind") ~= "Finish" and not c:IsA("SpawnLocation") then
		table.insert(solids, c)
	end
end
local params = OverlapParams.new()
params.FilterType = Enum.RaycastFilterType.Include
params.FilterDescendantsInstances = solids
local AIR = {{
{rects}
}}
local bad = 0
for _, r in AIR do
	local size = Vector3.new(r[3] - r[1] - 0.02, r[4] - r[2] - 0.02, 11.98)
	local cf = CFrame.new((r[1] + r[3]) / 2, (r[2] + r[4]) / 2, 0)
	local hits = workspace:GetPartBoundsInBox(cf, size, params)
	if #hits > 0 then
		bad += 1
		if bad <= 10 then say("AR OCUPADO " .. table.concat(r, ",") .. " por " .. hits[1].Name) end
	end
end
say("retangulos de ar livre: " .. #AIR .. ", ocupados: " .. bad)
local boxCf, boxSize = model:GetBoundingBox()
say("caixa: centro " .. tostring(boxCf.Position) .. " tamanho " .. tostring(boxSize))
{ramps}
say("FallenPartsDestroyHeight: " .. workspace.FallenPartsDestroyHeight)
return table.concat(out, "\\n")
"""


# Conferência das rampas do v2 (vale só se o layout tiver bordas inclinadas no lugar delas).
RAMPS = """local wedges = {}
for _, c in model:GetChildren() do
	if c:IsA("WedgePart") then table.insert(wedges, c) end
end
local rp = RaycastParams.new()
rp.FilterType = Enum.RaycastFilterType.Include
rp.FilterDescendantsInstances = wedges
for _, x in { 305, 320, 335, 385, 400, 415 } do
	local hit = workspace:Raycast(Vector3.new(x, 125, 0), Vector3.new(0, -100, 0), rp)
	local want = if x < 360 then 90 - (x - 300) * 1.25 else 40 + (x - 380) * 1.25
	say(string.format("rampa x=%d: %s y=%.2f (esperado %.2f)", x, hit and hit.Instance.Name or "nada", hit and hit.Position.Y or 0, want))
end"""


SVG_ORDER = ["Rock", "SlopeR", "SlopeL", "Kill", "Ice", "Unfreeze", "NoHook", "HookOnce", "Checkpoint", "Spawn", "Finish",
             "Sign", "Reserved"]
ROUTE_COL = {"rapida": "#ff4fa3", "media": "#00e5ff", "segura": "#ffffff"}


def render_svg(parts, box):
    """Vista lateral das peças geradas (o que o build.luau monta), com as rotas do rascunho."""
    s = 1.0
    bx1, by1, bx2, by2 = box
    top = 50

    def X(x):
        return (x - bx1) * s

    def Y(y):
        return (by2 - y) * s + top

    w, h = (bx2 - bx1) * s, (by2 - by1) * s + top + 10
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="Segoe UI, sans-serif">',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="#1b1d22"/>',
         f'<text x="10" y="32" fill="#fff" font-size="24" font-weight="600">Map01 · greybox {L.VERSION} (Fase 2) · '
         f'vista lateral em studs · caixa {bx2 - bx1} × {by2 - by1}</text>',
         f'<rect x="0" y="{top}" width="{w:.0f}" height="{(by2 - by1) * s:.0f}" fill="{L.COL["air"]}"/>']
    for kind in SVG_ORDER:
        for pt in parts:
            if pt["kind"] != kind:
                continue
            cx, cy, _ = pt["center"]
            pw, ph, _ = pt["size"]
            col = KINDS[kind]["color"]
            extra = ' fill-opacity="0.5" stroke="#ffd23f"' if kind == "Reserved" else ""
            o.append(f'<rect x="{X(cx - pw / 2):.1f}" y="{Y(cy + ph / 2):.1f}" width="{pw * s:.1f}" height="{ph * s:.1f}" '
                     f'fill="{col}"{extra}/>')
            if "RequiresHookLevel" in pt.get("attributes", {}):
                o.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="6" fill="none" stroke="#ffd23f" stroke-width="2"/>')
    dash = {"rapida": "8 5", "media": "3 5", "segura": ""}
    for _stage, _name, cls, pts in L.routes:
        d = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y, _ in pts)
        da = f' stroke-dasharray="{dash[cls]}"' if dash[cls] else ""
        o.append(f'<polyline points="{d}" fill="none" stroke="{ROUTE_COL[cls]}" stroke-width="1.5" stroke-opacity="0.8"{da}/>')
    for x, y, t, fs in L.labels:
        o.append(f'<text x="{X(x):.0f}" y="{Y(y):.0f}" fill="#fff" font-size="{fs * 0.8:.0f}" stroke="#1b1d22" '
                 f'stroke-width="2" paint-order="stroke">{t}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    grid, box, owners, wedges, tilted, notes = build()
    parts = parts_from(grid, box, owners, wedges, tilted)
    fallen = box[1] - 20
    OUT.mkdir(parents=True, exist_ok=True)
    layout = {
        "name": NAME,
        "source": "tools/map_layout.py (layout " + L.VERSION + "), gerado por tools/map2d.py. Não editar à mão.",
        "description": "Greybox 2.5D. X = horizontal, Y = altura, em studs; tudo no plano Z = 0. "
        "center e size em studs (size = largura X, altura Y, profundidade Z). rotZ em graus. "
        "WedgePart: size em X/Y do plano; slopeFaces diz para que lado a rampa olha.",
        "depth": DEPTH,
        "bounds": {"x1": box[0], "y1": box[1], "x2": box[2], "y2": box[3]},
        "fallenPartsDestroyHeight": fallen,
        "kinds": {k: {"color": v["color"], "tags": v["tags"], "label": v["label"]} for k, v in KINDS.items()},
        "parts": parts,
    }
    (OUT / "layout.json").write_text(json.dumps(layout, ensure_ascii=False, indent=1) + "\n", encoding="utf8", newline="\n")
    (OUT / "build.luau").write_text(luau(parts, fallen), encoding="utf8", newline="\n")
    (OUT / "map01.svg").write_text(render_svg(parts, box), encoding="utf8", newline="\n")
    counts = {}
    for pt in parts:
        counts[pt["kind"]] = counts.get(pt["kind"], 0) + 1
    print("ok", OUT, "| caixa", box, "|", len(parts), "peças:", counts)
    for n in notes:
        print(" nota:", n)
    for c in checks(grid, owners):
        print(" aviso:", c)
    if "--check" in sys.argv:
        path = Path(sys.argv[sys.argv.index("--check") + 1])
        path.write_text(check_luau(parts, free_air_rects(grid, owners), bool(wedges)), encoding="utf8", newline="\n")
        print("verificação:", path)


if __name__ == "__main__":
    main()
