# Trechos (`race-and-escape/chunk@1`)

Biblioteca de **trechos** de mapa (ADR 0052, etapa 4): pedaços prontos que o montador
(`tools/mapkit/assemble.py`) junta num mapa candidato. Cada trecho é um JSON nesta pasta (subpastas
valem); o id tem de ser único. Os arquivos `ex-*.json` são **exemplos mínimos** só para os testes — não
são propostas de mapa.

Regras de jogo que todo trecho segue (ADR 0053/0055): dá para passar **sozinho** (o validador joga com 1
jogador; é o critério), gelo trava (sozinho = fracasso da manobra), vermelho (Kill) é sólido, segura o
gancho e volta ao último checkpoint. Largada, checkpoints e chegada **não** vão no trecho: quem põe é o
montador.

## Exemplo

```json
{
 "format": "race-and-escape/chunk@1",
 "id": "ex-bifurcacao",
 "name": "Fosso com atalho (exemplo)",
 "theme": "exemplo",
 "pattern": "fosso-atalho",
 "rhythm": "amplo",
 "difficulty": 2,
 "solo": true,
 "checkpoint_end": false,
 "mechanics": {"required": [], "optional": ["walk", "jump", "double", "hook", "momentum"]},
 "doors": [
  {"id": "in", "role": "entry", "side": "L", "pos": 5, "width": 5},
  {"id": "out", "role": "exit", "side": "R", "pos": 5, "width": 5}
 ],
 "lanes": [
  {"id": "alto", "name": "por cima, no gancho", "kind": "rapida", "area": [10, 6, 17, 12]},
  {"id": "fosso", "name": "pelo fosso, andando", "kind": "segura", "area": [7, 1, 16, 2]}
 ],
 "notes": "texto livre",
 "tiles": {
  "cell": 4,
  "origin": [0, 0],
  "width": 36,
  "height": 14,
  "legend": {".": null, "#": "Block", "x": "Unhookable", "...": "..."},
  "rows": [
   "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
   "....................................",
   "............####....................",
   "...",
   "####################################"
  ]
 }
}
```

## Campos

| Campo | Significado |
|---|---|
| `format` | sempre `race-and-escape/chunk@1` |
| `id`, `name` | id único (nome do arquivo, de preferência) e nome de trabalho |
| `theme` | tema/região (ex.: `floresta`); o montador usa no relatório e para cortar seções |
| `pattern` | padrão de design que o trecho usa (id livre, ex.: do estudo do vídeo de referência — só o padrão, regra 1 do AGENTS.md) |
| `rhythm` | opcional: `apertado`, `amplo`, `gargalo` ou `respiro` (a alternância do ADR 0052) |
| `difficulty` | dificuldade **alvo** 1–5 (o validador mede a real; diferença de 2+ vira aviso) |
| `solo` | tem de ser `true` (ADR 0055: nenhum trecho exige parceiro) |
| `checkpoint_end` | `true` = o trecho fecha um trecho temático (o checkpoint com tempo parcial vem depois dele) |
| `mechanics` | `required` (o trecho exige) e `optional` (ajudam/atalhos). Valores: `walk`, `jump`, `double`, `hook`, `momentum`, `hookonce`, `hookthrough`, `unhookable`, `freeze`, `unfreeze`, `oneway`, `kill`, `solo`, `hammer`, `bouncer` |
| `doors` | portas: `id`, `role` (`entry`/`exit`), `side` (`L`/`R`/`T`/`B`), `pos`, `width` (ver abaixo). Pode haver mais de uma de cada |
| `lanes` | opcional: faixas de uma bifurcação (2+), cada uma com `id`, `name`, `kind` (`rapida`/`segura`/`outra`) e `area` `[i0, j0, i1, j1]` |
| `notes` | texto livre |
| `tiles` | a grade, igual ao `tiles@1` (`tools/mapkit/README.md`): `cell`, `origin`, `width`, `height`, `legend`, `rows` e, se precisar, `directions`/`attributes`/`collide`. `format`, `name` e `spawn` não são usados |

**Células e bloco.** `tiles.cell` é o lado do caractere em studs. Desenhe em **blocos**: `cell` = bloco
padrão em studs (2 × células do bloco). O bloco padrão sai de `maps/scale.json` (chave `block_cells` ou
`block_studs`, em qualquer nível do JSON); sem o arquivo, 2 células = **4 studs**. Se `tiles.cell` faltar,
vale o bloco padrão. O montador converte tudo para células de 2 studs (cada caractere vira k × k células).
As coordenadas `(i, j)` seguem o `tiles@1`: `i` = coluna da esquerda, `j` = linha **de baixo para cima**,
`rows[0]` = linha de cima.

**Portas.** Abertura na borda do trecho, em caracteres do trecho:

- `L`/`R` (laterais): `pos` = linha do **pé** (a 1ª linha livre, logo acima do chão da porta) e `width` =
  quantas linhas livres (altura da abertura, pelo menos o corpo: 5,5 studs). A célula logo abaixo da
  abertura, na coluna da borda, tem de ser sólida (o chão da porta).
- `T`/`B` (em cima/embaixo): `pos` = 1ª coluna livre e `width` = quantas colunas (pelo menos 2 studs; 4 é
  o confortável).
- Encaixe: saída `R` → entrada `L` (e `L` → `R`, `T` → `B`, `B` → `T`). Nas laterais as portas se alinham
  pelo chão; em cima/embaixo, pela 1ª coluna. O montador espelha o trecho quando a corrida vai para a
  esquerda (L ↔ R, mão única Left ↔ Right), então desenhe da esquerda para a direita.
- Prefira portas laterais: a ligação em cima/embaixo funciona, mas o trecho seguinte precisa ter a entrada
  do lado certo (o montador não gera adaptador vertical).

**Faixas (bifurcação).** Cada faixa é uma área por onde a rota passa (um nó em pé/pendurado ou um gancho
preso dentro dela). O validador procura, para cada faixa, a rota mais rápida que passa por ela **sem
tocar as áreas das outras** — 2+ faixas que passam = bifurcação de verdade. `rapida` tem de ser mais
rápida que `segura`, e `segura` não pode ser mais arriscada (chance de fazer sem errar, com 2 pontos de
folga); senão vira aviso.

## Conferir e ver os trechos

```
python -I -X utf8 tools/mapkit/chunks.py                 # todos: conferência + validação sozinho + prévias
python -I -X utf8 tools/mapkit/chunks.py maps/trechos/ex-vao-gancho.json --out pasta/
python -I -X utf8 tools/mapkit/chunks.py --static        # só a conferência estática (sem simular)
```

Grava em `maps/trechos/previa/` (ou `--out`): `trechos.md` (tabela: rota solo, tempos, menor janela,
dificuldade alvo × medida, caminhos, faixas, problemas) e `<id>.svg`/`<id>.png` de cada trecho, com as
cores do MapBuilder, entradas (verde), saídas (laranja), faixas (tracejado) e a rota mais rápida (azul).

Como o trecho é validado sozinho: ele vai para um mapa de teste com almofadas em volta — corredor com o
spawn na entrada, corredor/sala com a FinishLine na saída, laterais fechadas com bloco sem gancho, ar em
cima e embaixo. A almofada só imita o vizinho; o que vale no fim é a validação do mapa montado.
