# mapkit — ferramentas de mapa como dados (ADR 0052)

Biblioteca Python (só biblioteca padrão) para medir, converter e validar mapas fora do Studio.

| Arquivo | O que faz |
|---|---|
| `tiles.py` | formato de grade `race-and-escape/tiles@1`: ler/gravar, células ↔ studs, retângulos, `to_world()` |
| `convert_layout.py` | converte `maps/<mapa>/layout.json` (do `tools/map2d.py`) em `maps/<mapa>/tiles.json` |
| `export_editor.luau` | colar no Command Bar ou rodar pelo MCP `execute_luau`: devolve o JSON do `Workspace.Maps.Editor` |
| `validate.py` + `report.py` | validador (etapa 3): joga o mapa pela simulação e grava o relatório `.md` + `.svg` (seção "Validador") |
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

## Validador (`validate.py` + `report.py`, ADR 0052 etapa 3)

Joga o mapa sozinho pela simulação (`physics.py`) e relata o que achou. **Não muda o mapa.**

```
python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json --quick   # ~3 min no map01 (7 processos)
python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json           # completo: mais manobras, mais lento
```

Opções: `--out caminho.md` (o `.svg` vai junto, mesmo nome; padrão
`memory-palace/04-game-design/estudos/validacao-<pasta do mapa>.md`), `--jobs N` (processos; padrão CPUs − 1),
`--no-refine` (pula o refinamento das janelas). Em código: `validate(tm, Settings.quick(), jobs=1)` devolve um
`Validation` (`.results`, `.graph`), e `report.render(v)` devolve `(markdown, svg)`.

### Como funciona

1. **Plataformas e nós.** Plataforma = trecho contínuo de chão onde a caixa do corpo (2 × 5,5) fica em pé sem
   tocar Kill/Freeze. Cada uma ganha pontos nas duas bordas e a cada ~20 studs (`--quick`: ~32). Ficar
   pendurado num ponto de gancho também vira nó (no máximo 4 por quadrado de 40 × 40 studs; `--quick`: 2).
   Só conta a área ligada por ar ao spawn (bolsões fechados na rocha ficam de fora).
2. **Manobras (arestas).** De cada nó alcançado: andar e cair (também parar/voltar no ar); pulo parado e para
   os lados em vários lugares em volta do ponto; pulo e soltar A/D no ar; pulo duplo em vários momentos;
   gancho em cada alvo visível (o mais longe de cada setor de ângulo + as quinas de borda), segurando até
   pousar ou soltando em vários momentos, com e sem pulo duplo no topo depois de soltar; gancho do topo de um
   pulo. Pendurado: soltar (com/sem pulo duplo), balançar e soltar, prender no próximo alvo. Só valem alvos
   no alcance **e** na tela (`maps/metrics.json`). A manobra que pousa numa plataforma (ou pendura) vira
   aresta com o tempo, o rótulo (`walk`, `jump`, `double`, `hook`, `jump+hook`, `hook+momentum`,
   `hook+double`) e a **janela de acerto** (soma das variações vizinhas da família que dão no mesmo
   destino). Kill/queda = volta ao checkpoint e Freeze = trava: os dois contam como fracasso da variação.
3. **Rotas.** Busca em camadas (nó × checkpoints já feitos, na ordem do jogo; checkpoint e chegada contam com
   o root na coluna acima da peça, como o `Zones.isAbove`). Três rotas: *mais rápida* (tempo), *jogador médio*
   (tempo esperado com erro de tempo de 60 ms, 0,25 s para pensar e 4 s perdidos por erro) e *mais segura*
   (máxima chance de não errar).
4. **Refinamento.** Cada manobra das rotas é refeita mexendo uma entrada por vez (quando pular/soltar/disparar,
   de quadro em quadro; onde pular, de stud em stud; a mira, de grau em grau). Ela "dá certo" se o jogador
   não fica mais de 1 s atrás (pelo tempo que falta até a chegada). A janela é a da entrada mais apertada.
   As rotas são escolhidas de novo com as janelas refinadas, até estabilizar.
5. **Análises.** Alcançabilidade (cada checkpoint, ilhas, armadilhas = alcançadas mas sem caminho para a
   chegada); tipos de manobra por rota e "dá para terminar só com gancho / sem gancho / sem pulo duplo / sem
   embalo" (no mapa e por estágio); bifurcações (por estágio: caminhos por plataformas diferentes, guloso);
   desafio (janelas por estágio, curva de dificuldade); alturas (degraus até 60 studs pelas regras de desenho,
   quedas às cegas = destino mais baixo que a câmera mostra abaixo dos pés); pontos de gancho de propósito
   (HookOnce, blocos soltos até 40 células, `RequiresHookLevel`) usados, não usados, só fora da tela ou fora
   do alcance; tempos.

### Como ler o relatório

- **Janela de acerto:** < 0,1 s muito difícil (poucos quadros); 0,1–0,2 s difícil; 0,2–0,4 s médio;
  ≥ 0,4 s fácil; "livre" = sem tempo certo (andar, segurar o gancho).
- No SVG: verde = plataforma alcançada, laranja = ilha, rosa = armadilha; rota mais rápida em azul fino, a
  mais segura tracejada lilás, e a do jogador médio colorida pela janela (verde → vermelho); X vermelho =
  ponto de gancho fora do alcance, círculo laranja = só fora da tela, círculo tracejado = nunca usado.

### Limitações (o que os números querem dizer)

- **Um jogador só.** Sem gancho em parceiro, martelo, empurrão nem modo solo; gelo = fracasso. Trechos feitos
  para a dupla aparecem como difíceis, ilhas ou armadilhas.
- **Amostragem.** As manobras são um conjunto pequeno (1 gancho por manobra, alguns momentos de soltar e de
  pulo duplo, alguns alvos por setor). Então "não alcançado", ilha, armadilha, "não passa sem X" e "1 caminho
  só" querem dizer **"o validador não achou"**, não "impossível"; o tempo é um teto e as bifurcações, um piso.
  O `--quick` amostra menos que o modo completo e pode achar menos.
- A janela refinada mexe uma entrada de cada vez (as outras fixas); fora das rotas a janela é a da família
  (grosseira).
- O simulador tem as simplificações do topo do `physics.py` (caixa sem atrito, mundo em grade, Humanoid com
  velocidade instantânea, sem subida automática de degrau). Pousar com embalo conta como parar ali.
- "Na tela" usa a área visível com a câmera parada (sem o adiantamento nem o atraso da queda).
- Estágios (E1..E9, respiros R1..R8) só existem para o map01 (caixas de `tools/map_layout.py`).
