# Estudo — vídeo de referência de 2026-11-14 (padrões para o mapa)

> Estudo de 2026-11-21 (Claude Code + 4 subagentes, um por faixa de 15 min). **Só padrões de design**: o vídeo
> mostra uma partida de um mapa de terceiros do DDNet; nada de layout, nome, arte ou som vai para o nosso jogo
> (regra 1 do AGENTS.md, ADR 0001). Áudio não analisado.

## Material

| O quê | Onde (fora do Git) | Quantidade |
|---|---|---|
| Vídeo original | `D:\Videos\2026-11-14 22-08-44.mp4` | 59:42, 1536×864, 60 fps |
| Todos os frames (JPG, qualidade alta) | `referencias/imagens/video-2026-11-14/todos/f_NNNNNN.jpg` | 214.900 (frame N = segundo N/60) |
| 1 frame por segundo | `referencias/imagens/video-2026-11-14/1fps/s_NNNN.jpg` | 3.582 (`s_NNNN` = segundo NNNN−1) |
| Folhas de contato (12 quadros/minuto, com hora) | `referencias/imagens/video-2026-11-14/folhas/min_NN.jpg` | 60 (`min_01` = 0:00–0:59) |

Extraído com o FFmpeg (ver [TOOLS](../../07-toolchain/TOOLS.md)); temporários em `D:\Temp`. Para refazer:
`D:\Ferramentas\ffmpeg\bin\ffmpeg -i <video> -an -q:v 3 todos\f_%06d.jpg`.

Trechos a ignorar: 0:00–0:28, 20:00–20:30 e 46:30–46:45 (OBS/tela preta), 21:38–26:00, 38:10–41:05 e boa parte de
45–59 (modo espectador), votações de ban.

## O que se vê

- A dupla (o dono e um parceiro) faz a corrida em ~46 min na melhor volta; outro time termina em ~14 min. Às vezes
  grupos de 5–7 jogadores de times diferentes se misturam e se ajudam (servidor aberto).
- **Linguagem de cor** (deduzida pela mira, que fica clara/verde quando prende e vermelha quando não prende):
  oliva = sólido onde o gancho prende; contorno verde e quadrados cinza-escuro = gancho não prende; azul-claro
  translúcido = freeze (o boneco fica cinza, com flocos e barra de tempo); quadrados com sol = descongela;
  rosa = trecho solo (mensagem "solo part"). Hipótese: os subagentes divergiram em detalhes do cinza e do rosa.
- **Escala:** 1 tile ≈ 32–34 px no frame; o boneco cabe em ~1 tile.
- **Checkpoints com tempo parcial** a cada ~1–2 min de jogo, sempre na troca de trecho.

### Linha do tempo resumida

| Faixa | Trechos principais | Frames úteis (`1fps/`) |
|---|---|---|
| 0–15 min | lobby; teto prendível sobre pilares proibidos com covas de freeze; salas com "portas" de freeze de 1–2 tiles entre blocos proibidos (1ª parte em dupla); pilares altos com cortinas de freeze; labirinto sem colisão; **sala do martelo** (caixa toda proibida com 1 ponto bom no alto, gargalo de 2,5 min); chaminés; trecho de lança-granadas; corredor longo de freeze onde a dupla travou e teve de se matar | s_0116, s_0182, s_0236, s_0276, s_0291, s_0464, s_0581, s_0701 |
| 15–30 min | corredor de pilares com "janelas" de freeze; pilares com freeze no topo (um sobe, o outro puxa); labirinto solo com faixa de entrada/saída; poço vertical; voo com granada; degraus sobre vãos de freeze | s_0906, s_0921, s_0981, s_1006, s_1021, s_1066, s_1561, s_1661 |
| 30–45 min | poço estreito sem interação entre jogadores; labirinto de pilares em T; campo de ilhas flutuantes com freeze embaixo; prateleiras com barras proibidas; corredor de freeze com ilhas de descongelar; torre onde se puxa de cima; **gargalo** num poço fundo (só saiu com ajuda de outro grupo) | s_1813, s_2001, s_2016, s_2131, s_2151, s_2251, s_2566, s_2666 |
| 45–60 min | salas empilhadas com furo de 1 tile entre blocos proibidos (o furo troca de lado); bolsões de freeze com borda de resgate; um bloco proibido isolado como "dica negativa"; parede com ícones avisando o trecho solo; labirinto solo final com poço central; chegada destacada | s_2816, s_3046, s_3211, s_3362, s_3382, s_3392, s_3572, s_3577 |

## Padrões de design

1. **A cor diz a regra.** Poucas cores, sempre com o mesmo significado; o jogador lê a rota antes de tentar.
2. **Ensinar → cobrar → torcer.** Cada mecânica aparece isolada e fácil, depois repetida, depois combinada com
   outra (ex.: freeze raso → porta de freeze em dupla → corredor inteiro de freeze).
3. **Freeze como "chão falso" e "pele".** Fica onde o jogador naturalmente pousa ou erra (fundo de vão, topo de
   pilar, borda de teto). Errar não mata: deixa o jogador dependendo do parceiro.
4. **Resgate é a mecânica central da dupla.** Quase sempre há um apoio seguro ao lado do freeze para quem resgata
   (borda de 2–4 tiles, degrau no meio do corredor). A dificuldade cresce: puxão curto horizontal → puxar de cima →
   poço fundo vertical.
5. **Bloco proibido como moldura de precisão.** Ladeia furos de 1 tile, cobre topos de plataforma, isola um único
   ponto bom numa sala inteira proibida.
6. **Ilhas de descanso dentro do perigo** (descongelar no meio do freeze) dão ritmo de "respira e salta".
7. **Zonas com regra de interação própria.** Trechos solo e poços sem colisão/gancho entre jogadores, avisados por
   uma faixa/parede com ícones na entrada e na saída e por mensagem na tela.
8. **Ferramenta temporária em área fechada.** A arma entra por um item e sai por uma barreira no fim do trecho.
9. **Ritmo alternado:** trechos de 30–90 s, apertado → amplo → gargalo → salão de reagrupar → checkpoint.
10. **Pontos fracos a evitar:** corredor de freeze sem saída (a dupla teve de se matar e refazer ~10 min) e poço
    que só se vence com ajuda de fora (5 min travado). Sempre deixar uma rede de segurança perto.

## Como aplicar no nosso mapa (ideias originais, com os nossos elementos)

| Padrão | Ideia para o Race and Escape | Elementos |
|---|---|---|
| Portas de parede | salas separadas por furos de 1 tile com Freeze; depois um furo com Unfreeze do outro lado; por último um que só abre em Mão única | Bloco, Freeze, Unfreeze, Mão única |
| Sala de um ponto só | caixa toda de Unhookable com um único Gancho único no alto: o parceiro martela, quem sobe puxa o outro | Unhookable, Gancho único, martelo, gancho em jogador |
| Torres geladas | pilares de Unhookable com Freeze no topo: um sobe, o outro o puxa | Unhookable, Freeze, gancho em jogador |
| Corredor de brasas | faixa de Freeze com ilhas de Unfreeze de 4–5 tiles; ensina o puxão horizontal curto | Freeze, Unfreeze |
| Furo que troca de lado | 4–6 andares com vão de 1 tile ladeado por Unhookable; começa com teto prendível, termina exigindo o parceiro | Unhookable, Bloco |
| Dica negativa | um único Unhookable isolado numa sala toda prendível força outra rota | Unhookable |
| Trecho solo avisado | faixa/parede com os ícones (gancho, colisão, martelo) riscados antes da linha `SoloStart`, e outra no `SoloEnd` | linhas solo, placas |
| Rede de segurança | nenhum ponto onde a dupla possa ficar congelada junta a mais de ~15 s de um checkpoint ou Unfreeze; nos poços fundos, uma Mão única lateral de volta | Unfreeze, Mão única, KillZone |
| Checkpoint com parcial | checkpoint a cada bloco temático (~90 s) com o tempo parcial na tela | Checkpoint, UI |

## Ligações com o que está decidido

- No vídeo o freeze **não mata**: segura até alguém resgatar ou o jogador desistir. O código atual (gelo que solta
  1 s depois de sair, KillZone que volta ao checkpoint) já segue isso, mas os ADRs 0014/0045 ainda dizem "15 s e
  morre". Precisa de decisão do dono para alinhar os documentos.
- O ADR 0050 (mapa da Fase 2 com 9 estágios) foi medido com o movimento antigo; estes padrões servem para refazer os
  estágios com a física nova (DDNet) e o MapBuilder.
