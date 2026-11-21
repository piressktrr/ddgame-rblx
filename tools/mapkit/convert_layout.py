"""Converte o greybox `maps/<mapa>/layout.json` (gerado por tools/map2d.py) para a grade de blocos
`maps/<mapa>/tiles.json` (formato race-and-escape/tiles@1, ver tools/mapkit/README.md).

Rasterização por centro de célula (cell = 2 studs, origem no canto da caixa `bounds`): a célula
recebe o tipo da peça que contém o seu centro (meio aberto: [x1, x2) x [y1, y2)). Part girada
(`rotZ`) é testada no espaço local; WedgePart (rampa) vira o triângulo de rocha (`slopeFaces`
"+X" = canto reto embaixo à esquerda, sobe para a esquerda; "-X" = canto reto embaixo à direita).

Mapeamento: Rock/SlopeR/SlopeL -> Block, Kill -> Kill, Ice -> Freeze, Unfreeze -> Unfreeze,
NoHook -> Unhookable, HookOnce -> HookOnce, Checkpoint -> Checkpoint (+ Order), Finish ->
FinishLine (+ Order), Spawn -> RaceStart (+ `spawn`). Sign, Reserved e Backdrop ficam de fora.
Outros atributos (ex.: RequiresHookLevel) vão para `attributes` de cada célula.

Onde peças se sobrepõem, vence a de maior PRIORITY. No map2d.py a grade já não deixa zona sobre
rocha (zona só pinta ar; roxo e verde cobrem tudo); sobreposição só aparece com peça girada, que
o build.luau põe por cima: aí a zona vence a rocha. As sobreposições encontradas são contadas.

No map01 todas as zonas são sólidas (CanCollide = true no build.luau; Kill pelo ADR 0049), ao
contrário do MapBuilder: isso vai no campo `collide` do arquivo.

Uso (da raiz): python -I -X utf8 tools/mapkit/convert_layout.py [maps/map01]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # `python -I` não põe a raiz no path

from tools.mapkit.tiles import TileMap  # noqa: E402

CELL = 2

KIND_TO_ELEMENT = {
    "Rock": "Block",
    "SlopeR": "Block",
    "SlopeL": "Block",
    "Kill": "Kill",
    "Ice": "Freeze",
    "Unfreeze": "Unfreeze",
    "NoHook": "Unhookable",
    "HookOnce": "HookOnce",
    "Checkpoint": "Checkpoint",
    "Finish": "FinishLine",
    "Spawn": "RaceStart",
}
IGNORED_KINDS = {"Sign", "Reserved", "Backdrop"}

# Maior vence onde as peças se sobrepõem (ordem do map2d.py: ZONE_ORDER, a última ganha).
PRIORITY = {
    "Block": 1,
    "Unhookable": 2,
    "HookOnce": 2,
    "Kill": 3,
    "Freeze": 4,
    "Unfreeze": 5,
    "Checkpoint": 6,
    "RaceStart": 7,
    "FinishLine": 8,
}

# Zonas que o build.luau do map01 monta com CanCollide = true (map2d.py: KINDS sem collide = false).
SOLID_ZONES = ["Checkpoint", "FinishLine", "Freeze", "Kill", "RaceStart", "Unfreeze"]


def part_contains(part: dict):
    """Função (x, y) -> bool para a área da peça no plano."""
    cx, cy = part["center"][0], part["center"][1]
    w, h = part["size"][0], part["size"][1]
    x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    if part.get("class") == "WedgePart" or part["kind"] in ("SlopeR", "SlopeL"):
        faces = part.get("slopeFaces") or ("+X" if part["kind"] == "SlopeR" else "-X")

        def wedge(x: float, y: float) -> bool:
            if not (x1 <= x < x2 and y1 <= y < y2):
                return False
            u = (x - x1) / w  # 0 à esquerda, 1 à direita
            v = (y - y1) / h  # 0 embaixo, 1 em cima
            return v < 1 - u if faces == "+X" else v < u

        return wedge
    rot = part.get("rotZ") or 0
    if rot:
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

        def rotated(x: float, y: float) -> bool:
            lx = (x - cx) * c + (y - cy) * s
            ly = -(x - cx) * s + (y - cy) * c
            return -w / 2 <= lx < w / 2 and -h / 2 <= ly < h / 2

        return rotated
    return lambda x, y: x1 <= x < x2 and y1 <= y < y2


def part_box(part: dict) -> tuple[float, float, float, float]:
    cx, cy = part["center"][0], part["center"][1]
    w, h = part["size"][0], part["size"][1]
    rot = math.radians(part.get("rotZ") or 0)
    hw = (abs(w * math.cos(rot)) + abs(h * math.sin(rot))) / 2
    hh = (abs(w * math.sin(rot)) + abs(h * math.cos(rot))) / 2
    return cx - hw, cy - hh, cx + hw, cy + hh


def convert(layout: dict, source: str = "") -> tuple[TileMap, dict]:
    b = layout["bounds"]
    x0, y0 = b["x1"], b["y1"]
    width = math.ceil((b["x2"] - x0) / CELL)
    height = math.ceil((b["y2"] - y0) / CELL)
    tm = TileMap(
        name=layout.get("name", ""),
        cell=CELL,
        origin=(x0, y0),
        width=width,
        height=height,
        source=source,
        collide={element: True for element in SOLID_ZONES},
    )
    report = {"overlaps": 0, "ignored": {}, "unknown": {}, "parts": 0, "empty_parts": []}
    spawn_cells: list[tuple[int, int]] = []
    for part in layout["parts"]:
        kind = part["kind"]
        if kind in IGNORED_KINDS:
            report["ignored"][kind] = report["ignored"].get(kind, 0) + 1
            continue
        element = KIND_TO_ELEMENT.get(kind)
        if element is None:
            report["unknown"][kind] = report["unknown"].get(kind, 0) + 1
            continue
        report["parts"] += 1
        contains = part_contains(part)
        bx1, by1, bx2, by2 = part_box(part)
        i1 = max(0, math.floor((bx1 - x0) / CELL))
        i2 = min(width - 1, math.ceil((bx2 - x0) / CELL))
        j1 = max(0, math.floor((by1 - y0) / CELL))
        j2 = min(height - 1, math.ceil((by2 - y0) / CELL))
        attrs = dict(part.get("attributes") or {})
        painted = 0
        for j in range(j1, j2 + 1):
            for i in range(i1, i2 + 1):
                cx, cy = tm.cell_center(i, j)
                if not contains(cx, cy):
                    continue
                painted += 1
                current = tm.get(i, j)
                if current is not None:
                    report["overlaps"] += 1
                    if PRIORITY[current] > PRIORITY[element]:
                        continue
                tm.set(i, j, element)
                if attrs:
                    tm.attributes[(i, j)] = dict(attrs)
                else:
                    tm.attributes.pop((i, j), None)
                if element == "RaceStart":
                    spawn_cells.append((i, j))
        if painted == 0:
            report["empty_parts"].append(part.get("name", kind))
    if spawn_cells:
        # Nasce em cima do centro da faixa de início (a célula de ar logo acima dela).
        top = max(j for _, j in spawn_cells)
        row = sorted(i for i, j in spawn_cells if j == top)
        tm.spawn = (row[len(row) // 2], min(top + 1, height - 1))
    return tm, report


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "maps" / "map01"
    if not folder.is_absolute():
        folder = ROOT / folder
    layout_path = folder / "layout.json"
    out_path = folder / "tiles.json"
    layout = json.loads(layout_path.read_text(encoding="utf8"))
    rel = layout_path.relative_to(ROOT).as_posix()
    tm, report = convert(layout, f"{rel} (tools/mapkit/convert_layout.py). Não editar à mão.")
    text = tm.dumps()
    out_path.write_text(text, encoding="utf8", newline="\n")

    print(f"ok {out_path.relative_to(ROOT).as_posix()} | {tm.width} x {tm.height} células de {CELL} studs,"
          f" origem {tm.origin}, {len(text):,} bytes")
    print(f" peças convertidas: {report['parts']} | ignoradas: {report['ignored']} | desconhecidas: {report['unknown']}")
    print(f" sobreposições: {report['overlaps']} | peças sem célula: {report['empty_parts'] or 'nenhuma'}")
    print(f" spawn: {tm.spawn} -> {tm.cell_min(*tm.spawn) if tm.spawn else None} studs (pé)")
    print(" células por elemento:")
    for element, n in tm.counts().items():
        print(f"   {element:<12} {n:>7}")
    print(f"   {'(vazio)':<12} {tm.width * tm.height - len(tm.cells):>7}")
    print(f" retângulos (como o MapBuilder juntaria): {len(tm.rects())}")
    print(f" atributos em {len(tm.attributes)} células")

    again = TileMap.load(out_path)
    same = again.dumps() == text and again.cells == tm.cells and again.attributes == tm.attributes
    print(" ida e volta (salvar -> ler -> salvar):", "ok" if same else "DIFERENTE")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
