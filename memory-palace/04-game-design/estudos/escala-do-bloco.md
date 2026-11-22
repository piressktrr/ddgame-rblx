# Estudo — escala do bloco padrão do mapa novo (ADR 0055)

> Estudo de 2026-11-22 (Claude Code, subagente). Pergunta do ADR 0055: **de que tamanho é o bloco padrão do mapa
> novo**, "o tamanho mais adequado medido nos frames" do [vídeo de referência](referencia-video-2026-11-14.md).
> Do vídeo saem só **proporções e padrões**, nunca o traçado (regra 1 do AGENTS.md). As medidas do nosso jogo vêm do
> `Config` via [MEDIDAS_DO_MAPA](../MEDIDAS_DO_MAPA.md) / `maps/metrics.json`. A versão para máquina (gerador de
> trechos) está em `maps/scale.json`.

## Resposta curta

**Bloco padrão = 4 studs (2 células de 2 studs).** É o valor que já está em `Config.MapElements.DefaultGrid`, e
nenhum código precisa mudar. Com ele:

- **Furos, paredes e tampas de "1 tile" do vídeo viram 1 bloco.** O nosso corpo (2 de largura) passa num furo de
  1 bloco, como o boneco do DDNet passa num furo de 1 tile. Porta por onde se passa **andando** tem 2 blocos de altura
  (o corpo tem 5,5 de altura).
- **O gancho fica quase igual em blocos:** 10 blocos aqui, 11,9 tiles lá.
- **Pulo, vão e tela ficam pela metade em blocos**, mas casam **1 para 1 em células**: 1 tile do vídeo ≈ 1 célula
  (2,2 studs) para tudo que é distância de movimento. O gerador mede distâncias em células e desenha em blocos.

Nenhum tamanho casa tudo, porque a nossa física é um meio-termo: em relação à tela, o nosso pulo e a nossa
corrida são parecidos com os do DDNet, o gancho é ~1,5x mais longo e o corpo é 3x mais alto do que largo (o
boneco do DDNet é redondo). Detalhes abaixo.

## 1. O que foi medido no vídeo (DDNet), em tiles de lá

Como: frames lidos a olho e com perfis de cor por linha/coluna (script Python com Pillow, só leitura, no
scratchpad); movimento medido seguindo o chão e as paredes quadro a quadro em `todos/` (60 fps). A câmera do
DDNet fica **centrada no boneco** (sempre em x 768, y 430 do frame), então o boneco "parado" na tela e o cenário
andando é o movimento.

| Medida | Valor | Prova (frames) |
|---|---|---|
| **Tamanho do tile** | **34,3 px** (32 unidades do DDNet) | `1fps/s_0236` e `s_0182`: salas repetidas a cada 240 px = 7 tiles (6 de sala + 1 de parede); `s_0116`: plataforma de 3 tiles = 100 px; `s_2816`: sala de 5 tiles = 174 px. Bate com o zoom padrão do DDNet (34,4 px nesta resolução) |
| **Tiles na tela** | **44,8 × 25,2** | 1536 / 34,3 e 864 / 34,3. A câmera é simétrica: 12,6 tiles acima e abaixo do boneco, 22,4 para cada lado |
| **Boneco (tee)** | caixa de colisão **0,875 tile** (28 unidades, redonda); desenhado com ~45 px = **1,3 tile** | `s_0236`, linha 430: bonecos em x 645–690 e 746–791; coluna 768: y 406–451 |
| **Corrida** | ~540 px/s = **15,7 tiles/s** | `todos/f_013730`–`f_013748`: parede andando 52–57 px a cada 6 quadros |
| **Pulo** | **5,8 tiles** de altura; topo em 0,55 s; 1,08 s no ar | `todos/f_014288` (sai do chão) → `f_014321` (topo, chão 198 px abaixo) → `f_014353` (pousa) |
| **Pulo duplo** | **9,2 tiles** observado (máximo teórico ~10,3 com o duplo no topo); 7,6 tiles com o duplo cedo | `f_014152` → `f_014194` (sobe 316 px e congela numa cortina de freeze); `f_013955` → `f_014010` (261 px) |
| **Vão de pulo correndo** | ~**17 tiles** (15,7 tiles/s × 1,08 s; calculado, não medido num vão) | — |
| **Alcance do gancho** | **11,9 tiles** (380 unidades, valor padrão do DDNet); correntes vistas de 7,5–9,3 tiles e linha de mira de ~11,2 | `s_0116` (7,5), `s_0921` (8,7), `s_1066` (9,3), `s_2251` (linha de mira 386 px) |

Os números de pulo batem com a física padrão do DDNet (pulo 13,2 e gravidade 0,5 por tick → 5,65 tiles), então o
vídeo não usa física alterada nesses trechos.

### Larguras e alturas típicas (tiles)

| Peça | Medida no vídeo | Frames |
|---|---|---|
| Parede fina, tampa de furo, pele de freeze | **1 tile** | `s_0182`, `s_0236`, `s_0701`, `s_2816` |
| Furo de "porta" na parede | **1 tile** de altura (freeze), com 1 tile proibido acima e abaixo; base do furo a 3, 6 e 7 tiles do chão | `s_0236` (colunas 306 e 547), `s_0182` (coluna 868) |
| Furo no piso entre salas empilhadas | **1 tile**, ladeado por 1 tile proibido de cada lado; o furo do andar seguinte fica ~5 tiles para o lado | `s_2816`, `s_2666` |
| Sala com portas | **6 × 11** tiles por dentro | `s_0182`, `s_0236` |
| Salas empilhadas | **19 × 5** tiles, piso de 1 | `s_2816`, `s_2666` |
| Sala de um ponto só (martelo) | **~28 × 16** tiles | `s_0464` |
| Corredor (freeze) | **3 a 7** tiles de altura livre | `s_2131` (3), `s_0701` (7, com 1 de freeze no piso e no teto) |
| Ilha de descongelar | **4 a 6** tiles | `s_2131` (6, 4, 4), `s_0701` (calombo de 4 × 1) |
| Borda de resgate | **4** tiles; puxão horizontal de ~6 tiles | `s_3046` |
| Pilares | **2–3** de largura, **7–12** de altura, vão de **8** entre eles, topos diferindo **3–4**; teto a 19 do chão | `s_0921`, `s_0981`, `s_0276` |
| Chaminé / poço | **3–4** tiles de largura (o poço solo: 3) | `s_0581`, `s_1066`, `s_1813` |
| Labirinto | corredores de **1** tile, paredes de 1 | `s_0981`, `s_0276` |
| Degraus de plataforma | plataformas de **4–6** tiles, degrau de **1** | `s_1661` |
| Dica negativa | um proibido de **3 × 1** | `s_3362` |
| Trecho temático | salas com portas: **~80–90 tiles** na horizontal (~2 telas) em ~72 s (2:45–3:57 do vídeo); pilares: **~25–30 tiles** líquidos (sobe, desce, recomeça) em ~45 s (3:57–4:42). Progresso médio da dupla: ~0,6–1,2 tile/s (correndo seriam 15,7) | `folhas/min_03`, `min_05`; rastreio do cenário em `todos/f_009600`–`f_016560` |
| Checkpoints | a cada ~1–2 min de jogo, sempre na troca de trecho (estudo do vídeo) | folhas |

## 2. Conversão: quantos studs vale 1 tile do vídeo, por medida

"Studs por tile ideal" = nosso valor ÷ valor do DDNet. Se o bloco fosse esse número, a medida ficaria igual em
blocos e em tiles.

| Medida | DDNet (tiles) | Nosso (studs) | Studs por tile ideal | Bloco 2 | **Bloco 4** | Bloco 6 |
|---|---|---|---|---|---|---|
| Tela (largura) | 44,8 | 106,1 | 2,37 | 53 (1,2x) | **26,5 (0,6x)** | 17,7 (0,4x) |
| Tela (altura) | 25,2 | 59,7 | 2,37 | 30 (1,2x) | **14,9 (0,6x)** | 10 (0,4x) |
| Corrida por segundo | 15,7 | 38 | 2,44 | 19 | **9,5** | 6,3 |
| Pulo | 5,8 | 11,56 | 1,99 | 5,8 (1,0x) | **2,9 (0,5x)** | 1,9 |
| Pulo duplo | 10,3 | 21,8 | 2,12 | 10,9 | **5,45** | 3,6 |
| Vão de pulo | ~17 | 36,5 | 2,17 | 18,3 | **9,1** | 6,1 |
| **Gancho** | 11,9 | 40 | **3,37** | 20 (1,7x) | **10 (0,84x)** | 6,7 |
| Corpo (largura) | 0,875 | 2 | 2,29 | 1 | **0,5** | 0,33 |
| **Corpo (altura)** | 0,875 | 5,5 | **6,29** | 2,75 (3,1x) | **1,4** | 0,92 |
| Furo mínimo em pé (poço) | 1 | 4 (`corridor_width_min`) | 4 | 2 | **1** | 1 |
| Furo mínimo deitado (porta) | 1 | 8 (`ceiling_walk_min`) | 8 | 4 | **2** | 2 (1 se 6 bastar) |

Leitura:

- **Tela, corrida, pulo, pulo duplo e vão pedem ~2,2–2,4 studs por tile** (média geométrica 2,24). A nossa física
  está bem casada com a do DDNet **em relação à tela**: lá a tela tem 2,6 vãos de pulo de largura e 4,3 pulos de
  altura; aqui, 2,9 e 5,2.
- **O gancho pede 3,4**: o nosso é ~1,5x mais longo que o do DDNet, comparado com pulo e tela (40 contra os 27 que
  "deveria" ter). Por isso o `hook_target_up` (32) limita pela tela, não pelo alcance.
- **A altura do corpo pede 6,3**: o boneco do DDNet é redondo e cabe em 1 tile; o nosso é 2 × 5,5.

## 3. A escolha e o trade-off

| Bloco | Ganha | Perde |
|---|---|---|
| **2** (= célula) | pulo, vão e tela 1 para 1 com o vídeo | furo de 1 bloco não passa o corpo (2 = largura exata); porta deitada vira 4 blocos; corpo com 2,75 blocos de altura; gancho 1,7x; não sobra diferença entre bloco e célula |
| 3 | perto do ideal da corrida | não é múltiplo da célula de 2 (o MapBuilder pinta de 2 em 2): descartado |
| **4** | furo de 1 bloco passa o corpo (como o furo de 1 tile); gancho 0,84x; já é a grade padrão do MapBuilder e a unidade das regras do `metrics.json` | pulo e tela pela metade em blocos (tela 26,5 × 15, mais "graúda" que os 45 × 25 do vídeo); só ~3 blocos de pulo, então degraus finos usam células |
| 6 | altura do corpo (0,92) e porta de 1 bloco justa como no DDNet | grade grossa: pulo < 2 blocos, tela 18 × 10, furo em pé 3x a largura do corpo |
| 8 | — | ainda mais grossa |

**Recomendação: bloco de 4 studs, medindo distâncias em células.** O que o desenhista copia do vídeo como
"vocabulário de 1 tile" (furo, parede, tampa, bloco proibido isolado) vira **1 bloco**; o que é **distância de
movimento** (largura de sala, altura de degrau, vão, comprimento de trecho) vira **~1 célula por tile** (× 0,56 em
blocos); o que é **distância de gancho** (do jogador ao ponto, entre pontos seguidos, puxão) vira **× 0,84 em
blocos**, porque o nosso gancho é relativamente mais longo. Depois de converter, todo número passa pelas regras do
`metrics.json` e pelo validador; quando um padrão não cabe, vale a regra, não o vídeo.

### Regras de conversão para o gerador

1. Distância de movimento: `blocos = tiles × 0,56` (ou `células = tiles × 1,1`), arredondado e conferido nas
   regras `step_*`, `gap_*` e `ceiling_*`.
2. Distância de gancho: `blocos = tiles × 0,84`, limitado por `hook_target_distance` (9), `hook_target_up` (8),
   `hook_target_down` (5) e `hook_chain_spacing` (7).
3. Peças de 1 tile: furo em pé, parede, tampa = **1 bloco**; furo deitado (porta) = **2 blocos** de altura
   (versão difícil: 3 células = 6 studs, a testar no Studio); pele de freeze = **1 célula**.
4. Tudo tem de dar **sozinho** (ADR 0055): padrões do vídeo que dependem do parceiro ganham uma rota solo.

## 4. Dimensões por padrão (em blocos de 4 studs)

Para cada padrão da tabela "Como aplicar no nosso mapa" do [estudo do vídeo](referencia-video-2026-11-14.md), mais
dois que aparecem muito (chaminé e labirinto). "Confere" cita as regras do `metrics.json`.

| Padrão | No vídeo (tiles) | No nosso (blocos) | Confere | Adaptação |
|---|---|---|---|---|
| **Portas de parede** | sala 6 × 11; parede 1; furo 1 com tampa proibida de 1 acima e abaixo; base do furo a 3–7 do chão | sala **4 × 6–7**; parede **1**; furo **1 × 2** (espessura × altura) com tampa Unhookable de **1**; base do furo a **2–4** do chão | furo de 8 = `ceiling_walk_min`; base 8 = pulo, 12–16 = pulo duplo; base + furo + tampa ≤ altura da sala; teto 21–25 acima do root (`hook_target_up` 32) | furo de 2 blocos de altura porque o corpo é alto |
| **Sala de um ponto só** | ~28 × 16, um ponto bom no alto | **16 × 8**; 1 ponto (Gancho único ou Bloco) no teto; Freeze embaixo do ponto até **6** de raio | altura 8 deixa o ponto 29 acima do root (`hook_target_up`); sala inteira na tela (64 × 32); da borda do freeze, pular e prender no topo do pulo dá ~30 de distância (`hook_target_distance` 36) | no vídeo o parceiro martela; aqui o solo pula e prende, a dupla só encurta |
| **Torres geladas** | pilar 2–3 × 7–12; vão 8; topos diferindo 3–4; freeze de 1 no topo; teto a 19 | pilar **1–2 × 4–7**; vão **5**; topos diferindo **1–2**; freeze de **1 célula** no topo; teto a **10–11** do chão | vão 20 = `gap_jump_comfort`; degrau 8 = `step_jump_comfort`; teto 3–4 acima do pilar mais alto (`hang_clearance`); passo de pilar 6–7 = `hook_chain_spacing` | com freeze no topo, o solo atravessa pendurado no teto prendível; a dupla pode pousar e puxar |
| **Corredor de brasas** | altura livre 3–7; pele de freeze 1; ilhas de descongelar 4–6; puxão curto ~6 | altura **4–5**; pele **1 célula**; ilhas Unfreeze de **3**; entre ilhas **4–6** (difícil: **8**); puxão **5** | altura 5 = `ceiling_jump_free`; vão 16–24 = `gap_jump_comfort`, 32 = `gap_jump_max`; puxão 20 < 36 | o corredor de 3 tiles do vídeo não cabe o nosso pulo: vira 4–5 |
| **Furo que troca de lado** | salas 19 × 5; piso 1; furo 1 ladeado por proibido de 1; furo seguinte ~5 para o lado; 4–6 andares | salas **11 × 3**; piso **1**; furo **1** com Unhookable de **1** de cada lado; deslocamento **3–8**; **4–6** andares | chão a chão 16 = `step_double_jump_comfort`; furo de 4 = `corridor_width_min` (é a precisão); teto da sala de cima 25 acima do root | no fim exige mira certa pelo furo, não o parceiro |
| **Dica negativa** | um proibido de 1 × 1 a 3 × 1 | **1–2 × 1** Unhookable isolado | fica onde o gancho "óbvio" prenderia | — |
| **Trecho solo avisado** | faixa de 1; poço solo de 3 | faixa de **1** cobrindo a passagem (≥ **2** de altura); poço solo de **2** | poço 8 = `shaft_width_hook` | placas com os ícones antes de `SoloStart` e de `SoloEnd` |
| **Rede de segurança** | — | poço sem saída com fundo ≤ **5**; ≤ 15 s até checkpoint ou Unfreeze | 20 = `step_double_jump_max` | mais fundo que 5: parede prendível ou Mão única lateral |
| **Checkpoint com parcial** | trecho de 30–90 s e 25–90 tiles; checkpoint a cada ~1–2 min | trecho de **30–90 s** e **15–50 blocos** (0,6–2 telas); checkpoint por trecho | ~8 min no total (ADR 0055) = 5 a 8 checkpoints | — |
| Chaminé | 3–4 de largura, parede 1 | **2** de largura, parede **1** | 8 = `shaft_width_hook`; 1 bloco (4) só como aperto de propósito | — |
| Labirinto | corredores de 1, paredes de 1 | corredor em pé **1**, corredor deitado **2** de altura, parede **1** | 4 = `corridor_width_min`; 8 = `ceiling_walk_min` | corredores deitados têm o dobro da altura dos em pé |

## 5. Incertezas

- **Pulo duplo e vão de pulo:** o pulo simples foi medido limpo (5,8 tiles); o duplo só em duas sequências
  incompletas (7,6 e 9,2 tiles; uma acabou congelada) e o vão foi calculado (corrida × tempo no ar). Os dois batem
  com a física padrão do DDNet, mas não foram medidos num vão de verdade.
- **Gancho:** o alcance de 11,9 tiles é o valor padrão do DDNet; no vídeo só se vê corrente de até 9,3 tiles e uma
  linha de mira de ~11,2. O mapa pode ter ajustes locais (tune zones) que não aparecem na tela.
- **Medidas de sala** saíram de 1 a 3 frames por padrão (± 1 tile). Partes vistas no modo espectador
  ("visualização livre", `s_2816`, `s_3211`) usam o mesmo zoom (sala de 5 tiles = 174 px).
- **Comprimento de trecho:** medido em só dois trechos, seguindo o cenário quadro a quadro (a cada 6 quadros) com um
  script; o método erra ~10% para menos num teste com resposta conhecida e acumula erro em trechos com muita
  subida e descida. Vale como ordem de grandeza (dezenas de tiles, 1–2 telas), não como número exato.
- **Furo deitado de 3 células (6 studs)** para o corpo de 5,5: a caixa do simulador passa, mas o Humanoid do
  Roblox precisa ser testado no Studio antes de virar regra.
- A conversão é de **proporção**, não de dificuldade: o validador continua sendo o juiz (ADR 0052).
