# mapkit — ferramentas de mapa como dados (ADR 0052)

Biblioteca Python (só biblioteca padrão) para medir, converter e validar mapas fora do Studio.

| Arquivo | O que faz |
|---|---|
| `tiles.py` | formato de grade `race-and-escape/tiles@1`: ler/gravar, células ↔ studs, retângulos, `to_world()` |
| `convert_layout.py` | converte `maps/<mapa>/layout.json` (do `tools/map2d.py`) em `maps/<mapa>/tiles.json` |
| `export_editor.luau` | colar no Command Bar ou rodar pelo MCP `execute_luau`: devolve o JSON do `Workspace.Maps.Editor` |
| `validate.py` + `report.py` | validador (etapa 3): joga o mapa pela simulação e grava o relatório `.md` + `.svg` (seção "Validador") |
| `chunks.py` | trechos `chunk@1` (etapa 4): carregar, conferir, encaixe, validar cada trecho sozinho (seção "Trechos e montador") |
| `assemble.py` | montador (etapa 4): plano → mapa `tiles.json` + validação + relatório por seção |
| `preview.py` | prévias SVG/PNG de trechos e do mapa montado (cores do `MapElements.luau`) |
| `proposals/` | gerador dos trechos de proposta (`p-*`), ferramentas de inspeção e números do mapa (seção "Propostas") |
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

## Trechos e montador (`chunks.py`, `assemble.py`, `preview.py`; ADR 0052 etapa 4)

Biblioteca de **trechos** (pedaços de mapa com metadados) e um **montador** que junta trechos num mapa
candidato, valida o mapa inteiro com 1 jogador e relata. Ferramenta só: o mapa novo só entra no jogo com o
dono (ADR 0055). Só biblioteca padrão.

### Trecho (`race-and-escape/chunk@1`)

Formato completo em [`maps/trechos/README.md`](../../maps/trechos/README.md): uma grade `tiles@1` (mesma
legenda) + `id`, `name`, `theme`, `pattern`, `rhythm`, `difficulty` (alvo 1–5), `solo`, `checkpoint_end`,
`mechanics` (`required`/`optional`), `doors` (entradas e saídas: lado L/R/T/B, `pos`, `width`) e `lanes`
(faixas de uma bifurcação). Desenhado em blocos (`tiles.cell` = bloco em studs; padrão de
`maps/scale.json`, senão 4 studs).

```
python -I -X utf8 tools/mapkit/chunks.py                 # confere + valida cada trecho sozinho + prévias
python -I -X utf8 tools/mapkit/chunks.py --static        # só a conferência estática
```

Opções: `--out pasta` (padrão `maps/trechos/previa/`), `--full` (validador completo), `--no-refine`,
`--jobs N` (um trecho por processo). Em código:

```python
from tools.mapkit.chunks import load_library, check_chunk, fit, validate_chunk
lib = load_library()                         # id -> Chunk (maps/trechos)
check_chunk(lib["ex-corredor"])              # ["erro: ...", "aviso: ..."]: portas, chão das portas, metadados
fit(a, "out", b, "in")                       # (ok, motivo): lados opostos e abertura que deixa o corpo passar
rep = validate_chunk(lib["ex-bifurcacao"])   # ChunkReport
```

`validate_chunk` monta um mapa de teste (`isolated_map`: o trecho com almofadas — corredor com o spawn na
entrada, corredor/sala com a FinishLine na saída, laterais fechadas com bloco sem gancho) e roda o
`validate.py`. O `ChunkReport` traz: `ok` (rota solo da entrada à saída), tempos e menor janela das três
rotas (mais rápida, jogador médio, mais segura), `mechanics_used` (rótulos das manobras + gancho em
HookOnce + passar por mão única/degelo + andar), `paths` (caminhos de verdade), `lanes` (cada faixa: passa?
tempo, chance sem erro), `measured` × `target` e `problems`.

- **Dificuldade medida:** pela menor janela da rota **mais segura** (1 = sem precisão, 2 ≥ 0,4 s,
  3 = 0,2–0,4 s, 4 = 0,1–0,2 s, 5 < 0,1 s; +1 com 3+ manobras < 0,2 s). Diferença de 2+ da alvo = aviso.
- **Caminhos:** com faixas, as que passam sem tocar a área das outras (2+ = bifurcação); sem faixas, os
  caminhos por plataformas diferentes do validador (`disjoint_between`, guloso: um piso).
- **Faixas:** tempo = caminho mais rápido da faixa; risco = caminho mais seguro dela; as duas com a janela
  da família (a mesma régua). Aviso se a `rapida` não for mais rápida que a `segura` ou se a `segura` for
  mais arriscada (folga de 2 pontos percentuais).

### Plano (`race-and-escape/plan@1`)

```json
{
 "format": "race-and-escape/plan@1",
 "name": "Mapa novo (proposta A)",
 "library": "maps/trechos",
 "block": null,
 "max_width": 1200,
 "turn": "up",
 "target_minutes": 8,
 "sections": [
  {"id": "s1", "name": "Bosque", "theme": "floresta",
   "chunks": ["ex-corredor", {"chunk": "ex-bifurcacao", "mirror": false}, {"connector": "respiro", "blocks": 6}]},
  {"id": "s2", "name": "Gruta", "theme": "gruta", "chunks": ["ex-vao-gancho", {"connector": "degraus", "rise": 4}]}
 ]
}
```

| Campo | Significado |
|---|---|
| `library` | pasta(s) ou arquivo(s) de trechos (texto ou lista; relativo à pasta do plano ou à raiz). Padrão `maps/trechos` |
| `block` | células por bloco das peças geradas; `null` = `maps/scale.json` (ou 2) |
| `max_width` | studs de largura antes de virar (curva); padrão 1200 |
| `turn` | `up` (a próxima fileira fica em cima) ou `down` |
| `target_minutes` | duração alvo do jogador médio (padrão 8) |
| `origin` | studs da célula (0, 0) do mapa montado (padrão `[0, 0]`) |
| `row_gap_blocks`, `start_blocks`, `checkpoint_blocks`, `finish_blocks`, `respiro_blocks` | folga entre fileiras (2) e comprimentos das salas geradas (10, 8, 10, 6), em blocos |
| `sections` | seções temáticas, na ordem. Cada uma: `id`, `name`, `theme`, `chunks` (itens) |
| `chunks` | (no lugar de `sections`) lista única; as seções são cortadas depois de cada trecho com `checkpoint_end` |

Itens de `chunks`: `"id"` (trecho), `{"chunk": id, "mirror": true/false, "entry": porta, "exit": porta}`
(sem `mirror` o montador escolhe o sentido; sem `entry`/`exit`, as portas que seguem o sentido da fileira),
ou um conector gerado: `{"connector": "respiro", "blocks": n}` (corredor reto), `{"connector": "degraus",
"rise": n}` (n blocos; negativo desce) ou `{"connector": "curva"}` (vira já; `rise` opcional, em blocos).

### Montador

```
python -I -X utf8 tools/mapkit/assemble.py plano.json --out maps/<nome>/          # monta + valida (rápido) + relata
python -I -X utf8 tools/mapkit/assemble.py plano.json --out maps/<nome>/ --full   # validador completo
python -I -X utf8 tools/mapkit/assemble.py plano.json --no-validate               # só monta e desenha
python -I -X utf8 tools/mapkit/assemble.py plano.json --chunks                    # + cada trecho sozinho no relatório
```

Opções: `--jobs N` (padrão CPUs − 1), `--no-refine`, `--block N`. Grava em `--out` (padrão
`maps/<nome do plano>/`):

| Arquivo | O quê |
|---|---|
| `tiles.json` | o mapa montado (`tiles@1`, células de 2 studs) |
| `montagem.json` | onde ficou cada peça (células e studs), portas usadas, espelhado ou não, seção |
| `relatorio.md` | resumo (rota solo? tempo total × alvo), tempo por seção (parcial de cada checkpoint), curva de dificuldade por peça (alvo × medida), bifurcações (faixas no mapa montado), problemas, peças |
| `mapa.svg`, `mapa.png` | prévia com as cores do MapBuilder, caixas e rótulos dos trechos/seções, entradas/saídas, checkpoints com o parcial, rota mais rápida (azul) e do jogador médio (laranja tracejada). O PNG não tem texto |
| `validacao.md`, `validacao.svg` | o relatório completo do validador (etapa 3), com um "estágio" por peça |

Como monta:

1. **Largada**: sala com parede atrás, spawn e `StartLine` (coluna) perto da saída.
2. **Trechos** na ordem do plano, cada entrada colada na saída anterior (alinhada pelo chão nas laterais,
   pela 1ª coluna em cima/embaixo). O trecho é **espelhado** quando a fileira corre para a esquerda.
3. **Mapa enrolado**: se o próximo trecho passar de `max_width` (ou de x = 0, voltando), entra uma
   **curva**: torre com patamares em zigue-zague a cada degrau confortável (`step_jump_comfort`), metade da
   largura cada um, subindo (ou descendo) até a próxima fileira ficar `row_gap_blocks` acima (abaixo) de
   tudo o que já foi posto. Depois dela a corrida volta no sentido contrário.
4. **Sem sobreposição**: se o trecho encostar em outra peça, entram **degraus** gerados antes dele
   (metade do degrau confortável, 4 studs) até ele caber; se ainda encostar, vira erro no relatório.
5. **Checkpoint** no fim de cada seção (menos a última): sala com uma faixa de `Checkpoint` no chão, com os
   atributos `Order` (1, 2, ...), `Split = true` (marca de **tempo parcial**), `Section` (id) e `Name`
   (nome da seção). O MapBuilder ainda não tem elemento Checkpoint: o plugin pula essas células ao
   importar (e avisa); o validador já usa o `Order`.
6. **Chegada**: sala com `FinishLine` no chão e parede no fim.
7. Peças geradas: chão de bloco, teto e paredes **sem gancho** (corredor fechado: ninguém salta para a
   fileira de cima), altura livre = `ceiling_jump_free` (pulo inteiro sem bater a cabeça).

Análise (`analyze`): rota solo (todos os checkpoints na ordem até a chegada), tempo por seção pelas
`sections` das rotas do validador (mais rápida e jogador médio) e total × alvo (±25% = ok), dificuldade
medida por peça (rota mais segura dentro da caixa da peça), caminhos por peça (faixas no mapa montado ou
`disjoint_between` no trecho da rota) e avisos: seção sem bifurcação, seção sem trecho fácil (medida ≤ 2),
3+ trechos difíceis (≥ 4) seguidos, dificuldade só subindo por 4 trechos, medida longe da alvo, trecho
com `checkpoint_end` no meio da seção, faixa que não passa no mapa montado.

### Desempenho (7 processos, validador rápido)

- Um trecho sozinho: 2–5 s (trechos de exemplo, 100–150 studs de largura); com refinamento, até ~10 s.
- Mapa com 20 trechos de exemplo (28 peças, 1.184 × 184 studs, 2 curvas): ~50 s para montar, validar e
  desenhar. Trechos maiores ou `--full` custam mais (o map01 inteiro leva ~3 min no rápido).

### Limitações

- O que o validador não simula continua fora: parceiro, martelo, empurrão, Bouncer, nível do gancho.
- O trecho sozinho é jogado com almofadas que imitam o vizinho; entrada por baixo começa parada num piso
  logo abaixo do buraco, saída por cima termina numa sala com chão em volta do buraco. A validação que vale
  é a do mapa montado.
- O montador não gera adaptador entre saída vertical e entrada lateral (vira erro: ponha um trecho de
  transição). A curva e os degraus só existem para portas laterais.
- A colocação é gulosa (um trecho de cada vez, sem voltar atrás) e as caixas são retangulares: um trecho
  fundo empurra a fileira para cima com degraus, e podem sobrar vãos entre as fileiras.
- Dificuldade medida = janela de acerto; não conta distância, tela nem quanto o erro custa além do `RETRY`
  fixo do validador.
- `validate.py` ganhou só o parâmetro opcional `stages` (`validate(..., stages=[(nome, x1, y1, x2, y2)])` e
  `build_geometry(..., stages=...)`): uma caixa por peça, que dá nome aos estágios do relatório.

## Propostas (`proposals/`, ADR 0055)

O Claude gera trechos de proposta e um mapa candidato; o dono aprova. Os trechos `p-*` de `maps/trechos/` saem
de um gerador (não edite o JSON à mão: mude o gerador e rode de novo).

| Arquivo | O que faz |
|---|---|
| `proposals/kit.py` | desenho em blocos (`G`: `box`, `ground`, `door`, `oneway`, `shell`) e metadados do `chunk@1` (`meta`, `lane`) |
| `proposals/trechos_a.py` | os trechos da proposta A, um por função (convenções no topo de `proposta_a.py`) |
| `proposals/proposta_a.py` | grava `maps/trechos/p-*.json` (`--ascii` imprime as grades; ids na linha = só esses) |
| `proposals/inspect_chunk.py` | um trecho sozinho, manobra por manobra das três rotas (rótulo, tempo, janela, de onde para onde, em blocos) |
| `proposals/stats_proposta.py` | monta e valida o plano de novo e imprime o mix de manobras (mapa todo × só trechos), erros esperados e a conferência da mão única |

```
python -I -X utf8 tools/mapkit/proposals/proposta_a.py
python -I -X utf8 tools/mapkit/chunks.py maps/trechos/p-*.json --out maps/proposta-a/trechos
python -I -X utf8 tools/mapkit/assemble.py maps/proposta-a/plano.json --out maps/proposta-a/
python -I -X utf8 tools/mapkit/proposals/stats_proposta.py maps/proposta-a/plano.json
```

Lições do validador para quem desenha (2026-11-22): a janela do pulo duplo refinada fica em ~0,37 s (régua do
refinamento), então trecho com pulo duplo na rota mede 3; trecho "fácil" (medida 2) é feito de degraus de 1–2,
descidas a pé e patamares largos (≥ 8), com o último patamar longo; a mão única é ar para o simulador.
