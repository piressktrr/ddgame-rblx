# mapkit — ferramentas de mapa como dados (ADR 0052)

Biblioteca Python (só biblioteca padrão) para medir, converter e validar mapas fora do Studio.

| Arquivo | O que faz |
|---|---|
| `tiles.py` | formato de grade `race-and-escape/tiles@1`: ler/gravar, células ↔ studs, retângulos, `to_world()` |
| `convert_layout.py` | converte `maps/<mapa>/layout.json` (do `tools/map2d.py`) em `maps/<mapa>/tiles.json` |
| `export_editor.luau` | colar no Command Bar ou rodar pelo MCP `execute_luau`: devolve o JSON do `Workspace.Maps.Editor` |
| `tests/` | `python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .` (da raiz) |

`luau_config.py`, `physics.py` e `metrics.py` são da etapa 1/3 (medidas e simulador).

## Formato `race-and-escape/tiles@1`

Um JSON por mapa em `maps/<nome>/tiles.json`. A grade é a do MapBuilder: células quadradas no plano
Z = 0, X horizontal, Y altura, em studs.

```json
{
 "format": "race-and-escape/tiles@1",
 "name": "Exemplo",
 "source": "MapBuilder (Workspace.Maps.Editor)",
 "cell": 2,
 "origin": [-4, 6],
 "width": 5,
 "height": 3,
 "legend": {
  ".": null,
  "#": "Block",
  "o": "OneWay",
  "c": "Checkpoint"
 },
 "collide": {
  "Kill": true
 },
 "spawn": [1, 1],
 "directions": {
  "2,1": "Left"
 },
 "attributes": {
  "4,1": {"Order": 1}
 },
 "rows": [
  "....c",
  "..o.c",
  "#####"
 ]
}
```

(O `legend` gravado pelas ferramentas sempre traz a legenda inteira; aqui foi encurtado.)

| Campo | Significado |
|---|---|
| `format` | sempre `race-and-escape/tiles@1` (outro valor = erro) |
| `name`, `source` | nome do mapa e de onde veio (texto livre) |
| `cell` | lado da célula em studs. O MapBuilder usa 2; para importar no plugin tem de ser múltiplo de 2 |
| `origin` | `[x0, y0]`: studs do **canto inferior esquerdo** da célula (0, 0) |
| `width`, `height` | colunas e linhas |
| `legend` | caractere → id do elemento (`null` = vazio). Ao ler, vale a legenda do arquivo |
| `collide` | opcional. Liga/desliga a colisão de um elemento no mapa todo (padrão: a do MapBuilder) |
| `spawn` | `[i, j]` da célula onde o personagem nasce (o pé fica na base da célula), ou `null` |
| `directions` | `"i,j"` → `"Up"`/`"Down"`/`"Left"`/`"Right"`, só para `OneWay` (faltando = `"Up"`) |
| `attributes` | `"i,j"` → atributos da peça naquela célula (ex.: `Order` do checkpoint) |
| `rows` | as linhas da grade, **`rows[0]` = a linha mais alta** |

**Convenção das células (vale para `directions`, `attributes` e `spawn`):** `i` = coluna, da
esquerda para a direita, a partir de 0; `j` = linha **de baixo para cima**, a partir de 0. A célula
(i, j) cobre x em `[x0 + i·cell, x0 + (i+1)·cell)` e y em `[y0 + j·cell, y0 + (j+1)·cell)`. No
arquivo, ela é o caractere `rows[height - 1 - j][i]`: o arquivo se lê como o mapa visto de frente.

Legenda padrão:

| Car. | Elemento | Car. | Elemento |
|---|---|---|---|
| `.` | vazio | `k` | Kill |
| `#` | Block | `g` | HookOnce |
| `x` | Unhookable | `S` | StartLine |
| `h` | HookThrough | `F` | FinishLine |
| `f` | Freeze | `s` | SoloStart |
| `u` | Unfreeze | `e` | SoloEnd |
| `o` | OneWay | `c` | Checkpoint (só mapas antigos) |
| | | `R` | RaceStart (só mapas antigos) |

`Checkpoint` e `RaceStart` não são elementos do MapBuilder: existem para os mapas antigos (map01). O
plugin os pula ao importar (e avisa), assim como `collide` e `attributes`.

**JSON estável:** as ferramentas gravam as chaves sempre na mesma ordem, uma linha da grade por linha
do arquivo e uma entrada de `legend`/`collide`/`directions`/`attributes` por linha, ordenadas por
(j, i). O plugin escreve exatamente o mesmo texto, então exportar → gravar → ler → gravar não muda
nada no diff.

## `tiles.py`

```python
from tools.mapkit.tiles import TileMap, from_rows
tm = TileMap.load("maps/map01/tiles.json")
tm.get(i, j)            # id do elemento ou None
tm.cell_at(x, y)        # (i, j) que contém o ponto
tm.cell_min(i, j)       # canto inferior esquerdo em studs; cell_center(i, j) = centro
tm.rects()              # retângulos de células iguais (mesma junção do GridMerge.luau)
tm.counts()             # células por elemento
tm.save("saida.json")   # JSON estável
world = tm.to_world()   # consultas em studs para o simulador
```

### Interface do `world` (para o simulador)

| Método | Devolve |
|---|---|
| `is_solid(x, y, vx=0, vy=0)` | o corpo bate nesta posição? |
| `zone_at(x, y)` | `"freeze"`, `"unfreeze"`, `"kill"`, `"start"`, `"finish"`, `"solo_start"`, `"solo_end"`, `"checkpoint"` ou `None` |
| `hook_surface_at(x, y)` | `"hook"`, `"nohook"`, `"once"`, `"through"` ou `None` (o gancho passa reto) |
| `raycast_hook(origin, direction, max_dist)` | `HookHit(point, surface, cell, distance)` ou `None` |
| `one_way_at(x, y)` | direção da mão única na posição, ou `None` |
| `element_at(x, y)`, `attributes_at(x, y)`, `is_solid_cell(i, j, vx, vy)` | auxiliares |

`to_world(outside_solid=False)`: fora da grade é ar (mapa do MapBuilder no céu); `True` = parede.

Regras e aproximações (tiradas do jogo):

- **Sólido para o corpo:** Block, Unhookable, HookThrough e HookOnce (`CanCollide = true` em
  `MapElements.luau`), mais o que `collide` ligar. Zonas e linhas do MapBuilder são atravessáveis.
- **Mão única:** no jogo (`OneWayController`) a peça vira sólida quando o personagem inteiro está do
  lado sólido (ex.: `"Up"` vira chão para quem está em cima). Aqui, sem a caixa do corpo, a
  aproximação é: sólida só quando o movimento `(vx, vy)` vai contra a seta (produto escalar < 0);
  parado ou de lado, passa. Um simulador fiel deve usar `one_way_at` com a caixa do corpo.
- **Zonas:** `zone_at` olha só a célula do ponto. Zona sólida (`collide`, mapas antigos) age quando
  o corpo encosta: consulte os pontos da caixa do corpo crescida pela folga
  (`Config.Zones.TouchMargin`), como o `ZoneService`.
- **Gancho** (`HookController`: raio com `RespectCanCollide`, e `HookThrough`/`OneWay` atravessados):
  para em `"hook"` (prende), `"nohook"` (barra, não prende) e `"once"` (prende uma vez); atravessa
  `"through"` e tudo sem colisão. Zona sólida sem tag de gancho conta como `"hook"` (no map01, o
  vermelho segura o gancho, ADR 0049). `raycast_hook` anda célula a célula (DDA), ignora a célula de
  onde sai (o raycast do Roblox não acerta a peça em que começa) e devolve o ponto de entrada na
  célula. Não tem a esfera de ajuda da mira nem o "uma vez por peça" do HookOnce (fica com o
  simulador).
- Tudo é decidido pela célula: rampas e peças giradas já foram rasterizadas na conversão.

## `convert_layout.py` (map01)

`python -I -X utf8 tools/mapkit/convert_layout.py [maps/map01]` grava `maps/map01/tiles.json` e
imprime a contagem por elemento e a conferência de ida e volta. Regras:

- célula de 2 studs, origem no canto da caixa (`bounds`) do layout: X -10..1910, Y -10..1170 →
  960 × 590 células;
- a célula recebe o tipo da peça que contém o seu **centro** (meio aberto `[x1, x2)`); bordas em
  stud ímpar andam até 1 stud;
- `WedgePart` vira o triângulo de rocha (`slopeFaces` `"+X"`: canto reto embaixo à esquerda; `"-X"`:
  embaixo à direita); peça com `rotZ` é testada no espaço local;
- Rock/SlopeR/SlopeL → Block, Kill → Kill, Ice → Freeze, Unfreeze → Unfreeze, NoHook → Unhookable,
  HookOnce → HookOnce, Checkpoint → Checkpoint, Finish → FinishLine, Spawn → RaceStart; Sign,
  Reserved e Backdrop ficam de fora. Atributos (`Order`, `RequiresHookLevel`) vão para `attributes`;
- sobreposição: vence a de maior prioridade (Block < Unhookable = HookOnce < Kill < Freeze <
  Unfreeze < Checkpoint < RaceStart < FinishLine). No layout atual não há nenhuma: o `map2d.py` já
  pinta a grade com rocha vencendo zona, e só peça girada (que o `build.luau` põe por cima) poderia
  se sobrepor;
- no map01 todas as zonas são **sólidas** (`build.luau`: `CanCollide = true`; Kill pelo ADR 0049),
  ao contrário do MapBuilder: o arquivo leva `collide` com Checkpoint, FinishLine, Freeze, Kill,
  RaceStart e Unfreeze;
- `spawn` = célula logo acima do meio da faixa de início (`RaceStart`).

Mudou o `map_layout.py`? Rode `tools/map2d.py` e depois `convert_layout.py`; o teste
`test_map01_file_matches_layout` acusa `tiles.json` desatualizado.
