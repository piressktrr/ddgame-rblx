"""Greybox do mapa 2.5D (rascunho v2) para o Studio, a partir de `tools/map_layout.py`.

Gera em maps/map01/:
  - layout.json : peças (nome, tipo, classe, centro, tamanho, rotação em Z, tags e atributos)
  - build.luau  : monta Workspace.Maps.Map01 no Studio (apaga o antigo antes). Rodar em modo Edit,
                  pelo MCP `execute_luau` ou na barra de comandos.
  - map01.svg   : o próprio desenho v2 (de `tools/map_sketch.py`)

Como funciona: o layout é pintado numa grade de 1 stud dentro da caixa do mapa (ar + margem de rocha).
Tudo o que não é ar vira rocha; peças sólidas do desenho também são rocha. As zonas (mortal, gelo,
descongelar, checkpoint, fim, início) só ocupam células de ar; roxo e verde podem cobrir rocha. Cada
tipo é juntado em poucos retângulos (junção gulosa). Bordas inclinadas do ar viram WedgePart, e
zonas desenhadas como polígono inclinado viram uma Part girada em Z. O grupo "Tutorial" fica de fora.

Ajuste do 3D (não muda o desenho): uma zona apoiada numa faixa mortal desce até o chão, para a
faixa mortal não ficar embaixo dela (ex.: gelo e laranja no fundo do E6 viram ilhas no chão mortal).

Uso: python tools/map2d.py [--check caminho.luau]
     --check também grava um script Luau de verificação (contagens e ar livre) para rodar no Studio.
"""

import json
import math
import sys
from pathlib import Path

import map_layout as L
from map_sketch import render_svg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "maps" / "map01"
NAME = "Map01"
DEPTH = 12  # profundidade das peças do plano (Z de -6 a 6)
MARGIN = 10  # rocha em volta do ar
BACKDROP_Z = -10  # parede de fundo, atrás do plano (a câmera fica em +Z)
SKIP_GROUPS = {"Tutorial"}  # sala separada, fica para depois
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
COLLIDABLE_ZONES = {"Ice", "Unfreeze", "Checkpoint", "Spawn", "Finish"}

KINDS = {
    "Rock": {"color": L.COL["rock"], "tags": [], "label": "rocha e sólidos (gancho gruda)"},
    "SlopeR": {"color": L.COL["rock"], "tags": [], "class": "WedgePart", "yaw": -90,
               "label": "rampa de rocha, sobe para a esquerda"},
    "SlopeL": {"color": L.COL["rock"], "tags": [], "class": "WedgePart", "yaw": 90,
               "label": "rampa de rocha, sobe para a direita"},
    "Kill": {"color": L.COL["kill"], "tags": ["KillZone"], "collide": False, "label": "mortal (sem colisão, grudável)"},
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
}

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
    shapes = [(k, pts, g) for k, pts, g in L.shapes if g not in SKIP_GROUPS]
    air = [s for s in shapes if s[0] == "air"]
    ax1, ay1, ax2, ay2 = bbox([p for _, pts, _ in air for p in pts])
    box = (int(ax1) - MARGIN, int(ay1) - MARGIN, int(ax2) + MARGIN, int(ay2) + MARGIN)
    grid = Grid(*box)
    owners = {ROCK: ("Rock", "Rock"), AIR: ("Air", "Air")}  # dono -> (tipo, grupo)
    wedges, tilted, notes = [], [], []

    # 1) ar (com os triângulos das rampas também como ar; a rampa vira WedgePart)
    for _, pts, g in air:
        if is_rect(pts):
            x1, y1, x2, y2 = (int(v) for v in bbox(pts))
            for row, i, _, _ in grid.cells(x1, y1, x2, y2):
                row[i] = AIR
            continue
        ws = slope_wedges(pts)
        for wdg in ws:
            wdg["group"] = g
        wedges += ws
        x1, y1, x2, y2 = (int(v) for v in bbox(pts))
        for row, i, x, y in grid.cells(x1, y1, x2, y2):
            p = (x + 0.5, y + 0.5)
            if inside(p, pts) or any(inside(p, wdg["tri"]) for wdg in ws):
                row[i] = AIR

    # 2) sólidos do desenho = rocha
    for k, pts, g in shapes:
        if k == "solid":
            if not is_rect(pts):
                raise NotImplementedError("sólido não retangular")
            x1, y1, x2, y2 = (int(v) for v in bbox(pts))
            for row, i, _, _ in grid.cells(x1, y1, x2, y2):
                row[i] = ROCK

    # 3) zonas (só sobre ar) e 4) variantes de sólido (por cima de tudo)
    next_owner = 2
    for kind in ZONE_ORDER + SOLID_VARIANTS:
        for k, pts, g in shapes:
            if SKETCH_KIND.get(k) != kind:
                continue
            if not is_rect(pts):
                tilted.append({"kind": kind, "group": g, **oriented_box(pts)})
                continue
            owners[next_owner] = (kind, g)
            x1, y1, x2, y2 = (int(v) for v in bbox(pts))
            skipped = 0
            for row, i, _, _ in grid.cells(x1, y1, x2, y2):
                if kind in SOLID_VARIANTS or row[i] != ROCK:
                    row[i] = next_owner
                else:
                    skipped += 1
            if skipped:
                notes.append(f"{g} {kind} ({x1},{y1})-({x2},{y2}): {skipped} células sobre sólido ficaram de fora")
            next_owner += 1

    # 5) zona apoiada em faixa mortal desce até o chão
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
    order = 0
    for kind in ZONE_ORDER + SOLID_VARIANTS:
        for o, (k, g) in owners.items():
            if k != kind or o <= AIR:
                continue
            for x1, y1, x2, y2 in merge(grid, cells.get(o, [])):
                part = add(name(g, kind), kind, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
                if kind in ("Checkpoint", "Finish"):
                    order += 1
                    part["attributes"] = {"Order": order}
        for t in tilted:
            if t["kind"] == kind:
                add(name(t["group"], kind), kind, *t["center"], *t["size"], t["rotZ"])
    bx1, by1, bx2, by2 = box
    add("Backdrop", "Backdrop", (bx1 + bx2) / 2, (by1 + by2) / 2, bx2 - bx1, by2 - by1)
    return parts


# ---------------------------------------------------------------- conferências


def checks(grid, owners):
    """Passagens baixas ou estreitas demais (só ar e faixa mortal contam como espaço livre)."""

    def free(x, y):
        o = grid.get(x, y)
        return o == AIR or (o > AIR and owners[o][0] == "Kill")

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
    """Ar (e zonas sem colisão por cima) que nenhuma peça sólida pode ocupar, em retângulos."""
    pts = [
        (ix, iy)
        for iy, row in enumerate(grid.c)
        for ix, o in enumerate(row)
        if o == AIR or (o > AIR and owners[o][0] not in SOLID_VARIANTS)
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
        kinds.append(f"\t{kind} = {{ {', '.join(fields)} }}, -- {k['label']}")
    head = f"""--!strict
-- GERADO por tools/map2d.py a partir de tools/map_layout.py (rascunho {L.VERSION}). Não editar à mão.
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
"""
    lines = []
    for pt in parts:
        cx, cy, _ = pt["center"]
        w, h, _ = pt["size"]
        args = [f'"{pt["name"]}"', f'"{pt["kind"]}"', fmt(cx), fmt(cy), fmt(w), fmt(h)]
        if "rotZ" in pt:
            args.append(fmt(pt["rotZ"]))
        line = f"p({', '.join(args)})"
        for key, val in pt.get("attributes", {}).items():
            line += f':SetAttribute("{key}", {fmt(val)})'
        lines.append(line)
    tail = f"""
model.Parent = maps
workspace.FallenPartsDestroyHeight = math.min(workspace.FallenPartsDestroyHeight, {fallen})
return #model:GetChildren()
"""
    return head + "\n".join(lines) + "\n" + tail


def check_luau(parts, air_rects):
    """Script de verificação: contagens por tag, Order dos checkpoints, spawn e ar livre."""
    rects = ",\n".join("\t{" + ", ".join(str(v) for v in r) + "}" for r in air_rects)
    expected = {}
    for pt in parts:
        for t in pt.get("tags", []):
            expected[t] = expected.get(t, 0) + 1
    exp = ", ".join(f"{t} = {n}" for t, n in sorted(expected.items()))
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
for _, inst in CollectionService:GetTagged("Checkpoint") do
	if inst:IsDescendantOf(model) then
		say("checkpoint " .. inst.Name .. " Order=" .. tostring(inst:GetAttribute("Order")) .. " em " .. tostring(inst.Position))
	end
end
local spawns = {{}}
for _, d in workspace:GetDescendants() do
	if d:IsA("SpawnLocation") then table.insert(spawns, d:GetFullName() .. " @ " .. tostring(d.Position)) end
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
local wedges = {{}}
for _, c in model:GetChildren() do
	if c:IsA("WedgePart") then table.insert(wedges, c) end
end
local rp = RaycastParams.new()
rp.FilterType = Enum.RaycastFilterType.Include
rp.FilterDescendantsInstances = wedges
for _, x in {{ 305, 320, 335, 385, 400, 415 }} do
	local hit = workspace:Raycast(Vector3.new(x, 125, 0), Vector3.new(0, -100, 0), rp)
	local want = if x < 360 then 90 - (x - 300) * 1.25 else 40 + (x - 380) * 1.25
	say(string.format("rampa x=%d: %s y=%.2f (esperado %.2f)", x, hit and hit.Instance.Name or "nada", hit and hit.Position.Y or 0, want))
end
say("FallenPartsDestroyHeight: " .. workspace.FallenPartsDestroyHeight)
return table.concat(out, "\\n")
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    grid, box, owners, wedges, tilted, notes = build()
    parts = parts_from(grid, box, owners, wedges, tilted)
    fallen = box[1] - 20
    OUT.mkdir(parents=True, exist_ok=True)
    layout = {
        "name": NAME,
        "source": "tools/map_layout.py (rascunho " + L.VERSION + "), gerado por tools/map2d.py. Não editar à mão.",
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
    (OUT / "map01.svg").write_text(render_svg(), encoding="utf8", newline="\n")
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
        path.write_text(check_luau(parts, free_air_rects(grid, owners)), encoding="utf8", newline="\n")
        print("verificação:", path)


if __name__ == "__main__":
    main()
