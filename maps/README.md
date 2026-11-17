# Mapas

Cada mapa é **dado**, não script: um gerador em `tools/` produz o layout e o código que monta o mapa
no Studio. Nenhum script fica dentro do mapa; o comportamento vem de **tags** (CollectionService).

## Mapa atual: `map01` (greybox 2.5D do layout v3, mapa da Fase 2, ADR 0047, 0049 e 0050)

```
tools/map_sketch_fase2.py rascunho aprovado (9 estágios, 22 rotas): fonte dos números
tools/map_layout.py       layout v3: importa o rascunho e soma os ajustes do greybox (fonte única)
tools/map2d.py            gera os três arquivos abaixo a partir do layout
maps/map01/
  layout.json             peças: nome, tipo, classe, centro, tamanho, rotZ, tags e atributos
  build.luau              monta Workspace.Maps.Map01 no Studio (apaga e recria)
  map01.svg               vista lateral das peças geradas, com as rotas do rascunho
```

Fluxo: editar `tools/map_layout.py` (ou os números em `tools/map_sketch_fase2.py`) →
`python -I -X utf8 tools/map2d.py` → rodar o `build.luau` no Studio (MCP `execute_luau`, modo Edit)
→ jogar → salvar o place (`place/RaceAndEscape.rbxl`). `python -I -X utf8 tools/map2d.py --check
arquivo.luau` grava também um script que confere o mapa montado (contagens por tag e por `Kind`,
`Order`, `RaceStart`, zona mortal sólida, placas e reservados sem colisão, `RequiresHookLevel`, ar
livre, caixa). O v2 (6 estágios) saiu do place; o histórico fica no Git. `tools/map_sketch.py`
(desenho do v2) e `tools/mapgen.py` (map01 antigo) ficaram obsoletos.

**Caixa:** X -10..1910, Y -10..1170 (1.920 × 1.180 studs, ar de 1.900 × 1.160 + 10 de rocha em volta),
Z -10..6. Não encosta no lobby (X -1100..-900), no tutorial (X -1608..-1100) nem no `TestHook`
(X -704..-400). `FallenPartsDestroyHeight` fica em no máximo -30.

| Estágio (nome de trabalho) | Onde (X, Y) | Fim / checkpoint |
|---|---|---|
| E1 Clareira dos Troncos → | 0..420, 0..140 | início `RaceStart` em (20, 71) |
| E2 Copa e Raízes → | 460..880, 0..280 | |
| E3 Garganta Gelada → | 920..1320, 0..320 | Farol 1, `Checkpoint` `Order` 1, (1250..1310, 270) |
| E4 Escombros Flutuantes ↗ | 1360..1900, 240..466 | |
| E5 Torre Partida ↑ | 1680..1900, 470..820 | |
| E6 Pontes Quebradas ← | 1300..1900, 820..910 | Farol 2, `Checkpoint` `Order` 2, (1302..1338, 860) |
| E7 Galeria dos Cristais ← | 800..1260, 830..960 | |
| E8 Coração da Montanha ← (3 andares) | 200..800, 440..890 | |
| E9 Torre do Mago ↑ | 0..200, 440..1160 | fim `RaceFinish` + `Checkpoint` `Order` 3, (130..176, 1060) |

Respiros de 40 com placa (`Kind = "Sign"`, nome `R*_Sign*`): R1 X 420..460 · R2 X 880..920 (dois
andares) · R3 X 1320..1360 · R4 patamar X 1800..1840 (topo 446) embaixo de uma boca no chão do E5 ·
R5 chão em volta da boca do poço do E5 (X 1820..1900, Y 820) · R6 X 1260..1300 · R7 patamar X
800..840 (topo 860) ao lado do salão de descida do E8 · R8 os últimos 40 de cada andar do E8 (X
200..240). Placas também no início do E1, nos dois faróis e no fim.

Ajustes do greybox sobre o rascunho (todos comentados em `tools/map_layout.py`): portas entre E4/E5,
E5/E6 e E7/E8 (o desenho as tampava); vazios fechados embaixo dos faróis; patamares do salão do E8 só
na metade de dentro; as trocas de andar furam a faixa mortal; gelo tirado de cima dos pontos onde a
rota para (E5 poço, E6 vigas e ponte, E8 gruta, E9 dentro); parede do canal do E9 roxa; buraco no
topo da torre para o lance de dentro (o fim fica entre as duas bocas); E7: as 3 âncoras de saída dos
saltos de embalo descem para Y 934 (alvo seguinte ~12 mais alto, como no tutorial, para exigir o
pulo duplo; no E4 os vãos do arco já sobem ~18).

**Rota que exige nível de gancho (ADR 0050, Q49):** "corrente alta" do E3, 8 âncoras cinza
`E3_HookLv2_1..8` com atributo **`RequiresHookLevel = 2`**, de (942, 262) a (1257, 292), vãos de ~45-46,
por cima da cascata até o Farol 1. Opcional: cascata e chaminé continuam. Atenção: pela física de hoje
(embalo + A/D no ar a ~50 studs/s², sem freio) dá para chegar a 40 de uma âncora a ~45 voando na
direção dela, então a distância sozinha não barra ninguém; para a rota exigir nível de verdade, o
gancho terá de ler o atributo quando a evolução do gancho (Q23) entrar. Fica para o dono decidir.

**Pontos reservados** (fases 4 e 5): peças `Kind = "Reserved"`, amarelas, transparência 0,8, sem
colisão, consulta nem toque, atributos `Reserved` (`Bouncer`, `Blade`, `Jupiter`, `Mercury`,
`Vulcan`, `Saturn`) e `Note` (texto do estudo). Nenhuma rota depende delas.

Convenções:

- Visto de lado: X horizontal, Y altura. Todo o percurso jogável no plano **Z = 0**; as peças do plano
  têm 12 studs de profundidade (Z de -6 a 6). Atrás, em Z = -10, um fundo escuro sem colisão,
  consulta nem toque (não gruda). Placas em Z = -9,3 (0,4 de espessura), texto na face +Z.
- "Ar" é onde se joga; o resto da caixa do mapa (ar + 10 studs de margem) é **rocha**, juntada em
  poucos retângulos. Bordas inclinadas do ar viram `WedgePart` (o v3 não tem).
- As formas do layout são pintadas na ordem: ar abre, sólido fecha, zonas só onde não é sólido, roxo e
  verde (e sólido com atributo) cobrem tudo.
- Tipos de peça (atributo `Kind`) e tags: `Rock` cinza (gruda); `SlopeR`/`SlopeL` rampas de rocha;
  `Kill` vermelho, `KillZone`, **sólido** (`CanCollide = true`, o gancho prende nele, ADR 0049; a
  morte vem da consulta por caixa do `ZoneService`); `Ice` `FreezeZone`; `Unfreeze` laranja
  `UnfreezeZone`; `NoHook` roxo; `HookOnce` verde; `Checkpoint` dourado, `Checkpoint` + atributo
  `Order`; `Finish` branco, `RaceFinish` + `Checkpoint` (último `Order`); `Spawn` = `SpawnLocation`
  (Neutral, Duration 0, **`Enabled = false`**, tag `RaceStart`): é só o ponto de início; ninguém nasce
  nele (ADR 0044, o nascimento é no lobby); `Sign` placa; `Reserved` ponto reservado.
- Zonas só ocupam ar (a faixa mortal não passa por baixo de pilares); uma zona apoiada em faixa
  mortal desce até o chão (vira ilha).

## Lobby: `lobby` (greybox 2.5D, ADR 0044)

```
maps/lobby/build.luau    monta Workspace.Lobby no Studio (apaga e recria); escrito à mão
```

Sala fechada em X -1100..-900, Y 100..160 (chão com topo em Y = 104), no plano Z = 0, mesmas cores
e convenções do Map01 (profundidade 12, fundo escuro em Z = -10). Peças:

- `Spawn`: `SpawnLocation` ligado (Neutral, Duration 0, profundidade 1), tag `LobbySpawn`. Único
  spawn ligado do place: todo jogador nasce aqui.
- `Portal`: peça turquesa sem colisão, tag `LobbyPortal`, texto "Corrida" (BillboardGui). Entrar
  nele (conferência por zona no `LobbyService`) leva ao `RaceStart` do mapa.

Fluxo: editar `maps/lobby/build.luau` → rodar no Studio (MCP `execute_luau`, modo Edit) → salvar o
place.

A parede oeste do lobby (`WallLeft`) vai só de Y 116 a 156: a abertura Y 104..116 leva ao tutorial.

## Tutorial do gancho: `tutorial` (greybox 2.5D, ADR 0041 e 0046)

```
maps/tutorial/build.luau monta Workspace.Tutorial no Studio (apaga e recria); escrito à mão
```

Sala colada ao lobby, à esquerda: X -1608..-1100, Y 96..228 (chão com topo em Y = 104, o do lobby;
teto em 196 até X -1500, mais alto que o do lobby para caber as subidas, e em 224 na lição 7). Entra-se pela abertura na parede oeste do lobby e
anda-se para a esquerda. O portal do lobby continua indo direto à corrida (quem já sabe jogar pula o
tutorial). Sem `KillZone`, gelo nem `SpawnLocation`: cair numa lição leva ao começo dela por chão
(rampas). Dicas em placas no fundo (`Kind = "Sign"`, Z = -9,3, `SurfaceGui` na face +Z, sem colisão,
consulta nem toque). Os degraus têm 20 ou mais de altura e os vãos 30 ou mais: sem gancho não passa
(pulo duplo alcança ~13 de altura e ~22 de distância a 24 studs/s).

| Lição | Onde (X) | Peças | O que ensina |
|---|---|---|---|
| 1 | -1144..-1104, chão 104 | `Step1` (topo 124), `Target1` (-1146, 138) | clicar num bloco e ser puxado |
| 2 | fosso -1284..-1184, chão 104 | `Ramp2`, `Perch2` (topo 136), `Target2` (-1211, 147) | segurar para ficar preso e cair na plataforma |
| 3 | mesmo fosso | `Target3a` (-1236, 152), `Target3b` (-1260, 156), `Step2` (topo 140) | encadear alvos no ar |
| 4 | -1314..-1284, chão 140 | `Wall4` e `Decoy4` roxos, `Target4` (-1306, 175), `Step3` (topo 164) | roxo não prende |
| 5 | vão -1397..-1352, chão 140 | `Ramp5`, `Target5` verde (-1374, 178), `Step4` (topo 164) | verde só uma vez |
| 6 | vão -1457..-1427, chão 140 | `Ramp6`, `Target6` (-1451, 172), `Step5` roxo (topo 172, X -1500..-1457) | pulo duplo depois do gancho |
| 7 | vão -1556..-1500, chão 140 | `Ramp7` (volta a `Step5`), `Target7a` (-1521, 187,5), `Target7b` (-1565,5, 199), `Step6` roxo (topo 184) | salto de embalo: puxar sem segurar, pulo duplo no ar, próximo gancho (ADR 0050) |
| fim | `Step6`, X -1604..-1556 | `Portal` (-1592, 191), tag `LobbyPortal` | começa a corrida (LobbyService) |

Lição 7: os alvos ficam a 44,5 em X e 11,5 em Y (46 de centro a centro). Segurando embaixo de
`Target7a`, `Target7b` fica a ~48,6 do root (alcance 40). Soltando no fim do puxão sobra ~20 studs/s
em X; com o pulo duplo logo depois (~0,15 s), `Target7b` entra no alcance (medido em playtest, com ou
sem A). Sem pulo duplo, ou soltando depois de segurar, não alcança.

O teto acima das lições 5 a 7 (X < -1340) e a parede oeste são roxos, para ninguém pular as lições
pelo teto. O verde só volta ao renascer ou num checkpoint; quem cair depois de usá-lo sobe pelas
paredes cinza do vão com o gancho.

Fluxo: editar `maps/tutorial/build.luau` → rodar no Studio (MCP `execute_luau`, modo Edit), depois do
`maps/lobby/build.luau` → salvar o place.

## Regras de medida (Config de hoje: JumpHeight 7,2, WalkSpeed 24, pulo duplo 50, gancho 40)

Contas do [estudo do mapa da Fase 2](../memory-palace/04-game-design/estudos/mapa-fase2.md) §2 (até o
playtest dizer outra coisa):

- Pulo simples: sobe **7**, alcança **~13** no mesmo nível. Pulo duplo: sobe **~13,5**, alcança **~22**.
- Sem gancho não passa: vão **≥ 30**, degrau **≥ 20**. Respiro sem desafio: vão **≤ 10**, degrau **≤ 5**.
- Gancho: alcance de **40** a partir do `HumanoidRootPart` (~3 acima dos pés); entre pontos de chegada,
  no máximo 35 (rota segura), 36 (média) e 38 (rápida). Alvo para cima até **~34** acima do root (o
  que aparece na tela); queda maior que 24 é "às cegas".
- Salto de embalo: soltar o gancho com embalo (~26 studs/s) e dar o pulo duplo leva a âncoras a
  ~48-50. Como o A/D no ar acelera ~50 studs/s² durante o embalo, um vão de ~45-48 na **mesma
  altura** passa sem pulo duplo; para exigir o pulo duplo, o alvo seguinte fica **~12 mais alto**.
- Gelo só onde se encosta voando, fora do ponto onde a rota para, com laranja na linha da queda.
- Passagem por baixo de algo: pelo menos **7** de altura e **4** de largura. A faixa mortal é sólida
  e conta como chão.
- Cair abaixo de `workspace.FallenPartsDestroyHeight` (no map01, até -30; o mapa é fechado em
  rocha) mata; o jogador volta ao último checkpoint.
- Personagem com ~5 de altura. Se a velocidade ou o alcance mudarem no Config, estas medidas mudam.
