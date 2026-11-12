"""Gera, a partir de maps/<mapa>/layout.json:
  - <mapa>.svg   : vista lateral 2D do mapa (para revisar o level design)
  - build.luau   : código Luau que monta o mapa em Workspace.Maps.<Nome> (rodar no Studio via MCP
                   ou na barra de comandos). Mapa é dado, não script: o layout.json é a fonte da verdade.

Uso: python tools/mapgen.py maps/map01
"""

import json
import sys
from pathlib import Path

SCALE = 3  # px por stud no SVG
PAD = 30


def load(folder: Path) -> dict:
    return json.loads((folder / "layout.json").read_text(encoding="utf8"))


def svg(d: dict) -> str:
    xs = [v for b in d["blocks"] for v in b["box"][:2]]
    ys = [v for b in d["blocks"] for v in b["box"][2:]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w = (x1 - x0) * SCALE + 2 * PAD
    h = (y1 - y0) * SCALE + 2 * PAD + 60

    def X(v):
        return (v - x0) * SCALE + PAD

    def Y(v):
        return (y1 - v) * SCALE + PAD + 40

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="sans-serif">',
        f'<rect width="{w:.0f}" height="{h:.0f}" fill="#1b1d24"/>',
    ]
    for s in d["sections"]:
        sx, ex = X(s["x1"]), X(s["x2"])
        out.append(f'<rect x="{sx:.0f}" y="10" width="{ex - sx:.0f}" height="{h - 20:.0f}" fill="none" stroke="#3a3f4f" stroke-dasharray="6 6"/>')
        out.append(f'<text x="{sx + 8:.0f}" y="30" fill="#c9cbe0" font-size="16">{s["id"]} · {s["name"]}</text>')
    for b in d["blocks"]:
        bx1, bx2, by1, by2 = b["box"]
        r, g, bl = d["kinds"][b["kind"]]["color"]
        op = "0.45" if b["kind"] == "kill" else "1"
        hh = max((by2 - by1) * SCALE, 2)
        out.append(
            f'<rect x="{X(bx1):.1f}" y="{Y(by2):.1f}" width="{(bx2 - bx1) * SCALE:.1f}" height="{hh:.1f}" '
            f'fill="rgb({r},{g},{bl})" fill-opacity="{op}"><title>{b["name"]}</title></rect>'
        )
    sx, sy = d["spawn"]
    out.append(f'<circle cx="{X(sx):.0f}" cy="{Y(sy) - 8:.0f}" r="6" fill="#5ad07a"/>')
    out.append(f'<text x="{X(sx) + 10:.0f}" y="{Y(sy) - 4:.0f}" fill="#5ad07a" font-size="13">spawn</text>')
    out.append("</svg>")
    return "\n".join(out)


def luau(d: dict) -> str:
    lines = [
        "-- GERADO por tools/mapgen.py a partir de layout.json. Não editar à mão.",
        "local maps = workspace:FindFirstChild(\"Maps\") or Instance.new(\"Folder\")",
        "maps.Name = \"Maps\"",
        "maps.Parent = workspace",
        f"local old = maps:FindFirstChild(\"{d['name']}\")",
        "if old then old:Destroy() end",
        "local model = Instance.new(\"Model\")",
        f"model.Name = \"{d['name']}\"",
        "local function block(name, kind, x1, x2, y1, y2, r, g, b)",
        "\tlocal p = Instance.new(\"Part\")",
        "\tp.Name = name",
        "\tp.Anchored = true",
        f"\tp.Size = Vector3.new(x2 - x1, math.max(y2 - y1, 0.2), {d['depth']})",
        "\tp.Position = Vector3.new((x1 + x2) / 2, (y1 + y2) / 2, 0)",
        "\tp.Color = Color3.fromRGB(r, g, b)",
        "\tp.Material = Enum.Material.SmoothPlastic",
        "\tp.TopSurface = Enum.SurfaceType.Smooth",
        "\tp.BottomSurface = Enum.SurfaceType.Smooth",
        "\tp:SetAttribute(\"Kind\", kind)",
        "\tif kind == \"kill\" then p.CanCollide = false; p.Transparency = 0.5 end",
        "\tp.Parent = model",
        "end",
    ]
    for b in d["blocks"]:
        x1, x2, y1, y2 = b["box"]
        r, g, bl = d["kinds"][b["kind"]]["color"]
        lines.append(f'block("{b["name"]}", "{b["kind"]}", {x1}, {x2}, {y1}, {y2}, {r}, {g}, {bl})')
    sx, sy = d["spawn"]
    lines += [
        "local spawn = Instance.new(\"SpawnLocation\")",
        "spawn.Name = \"Spawn\"",
        "spawn.Anchored = true",
        "spawn.Neutral = true",
        "spawn.Duration = 0",
        "spawn.Size = Vector3.new(6, 1, 6)",
        f"spawn.Position = Vector3.new({sx}, {sy} + 0.5, 0)",
        "spawn.Parent = model",
        "model.Parent = maps",
        f"workspace.FallenPartsDestroyHeight = {d['killHeight']}",
        "return #model:GetChildren()",
    ]
    return "\n".join(lines) + "\n"


def main():
    folder = Path(sys.argv[1])
    d = load(folder)
    (folder / f"{folder.name}.svg").write_text(svg(d), encoding="utf8", newline="\n")
    (folder / "build.luau").write_text(luau(d), encoding="utf8", newline="\n")
    print("ok", folder)


if __name__ == "__main__":
    main()
