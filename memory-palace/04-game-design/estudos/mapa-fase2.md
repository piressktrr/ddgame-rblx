# Estudo e rascunho do mapa da Fase 2

> Estudo de 2026-11-17 (Claude Code, subagente). **Aprovado pelo dono no mesmo dia:** as dúvidas da §final
> viraram o [ADR 0050](../../02-decisoes/0050-mapa-fase2-aprovado.md) (todas "sim"; o mapa substitui o Map01).
> Rascunho visual: [`mapa-2-5d/rascunho-fase2.svg`](mapa-2-5d/rascunho-fase2.svg) (vista lateral, em studs).
> Base: ADR 0029, 0033, 0034, 0041, 0042, 0043, 0045, 0046 e 0047; GAME_DESIGN §3, §5 e §6; IMPLEMENTATION_PLAN
> (Fase 2); RF-70 a RF-74; `src/shared/Config.luau`; padrões de [referencias-mapas.md](referencias-mapas.md)
> (só padrões, nenhum layout copiado; ADR 0001).

## 1. Objetivo

Desenhar no papel o mapa novo da Fase 2 antes do greybox (GAME_DESIGN §5.1, passo 1), com:

- pelo menos 8 estágios (proposta: **9**), dificuldade média, comprimento e altura de sobra (ADR 0047);
- vários caminhos e várias formas de chegar ao fim, com a rota rápida/arriscada e a lenta/segura em quase
  todo estágio (GAME_DESIGN §5.4);
- movimento quase todo pelo gancho (ADR 0046): vãos e subidas principais fora do alcance do pulo duplo;
- checkpoint a cada 3 estágios, sempre onde os caminhos se juntam (ADR 0034, 0047);
- corrida de 10 a 15 min para um jogador médio (ADR 0040, RF-74);
- perigos atuais (gelo 15 s, laranja-brasa, vermelho, roxo, verde) e só **pontos reservados** para Bouncer,
  lâmina e os objetos dos deuses romanos (fases 4 e 5).

## 2. Regras de alcance (contas com os números do Config)

Gravidade padrão do Roblox: 196,2 studs/s². Números de `Config.Movement` e `Config.Hook`.

| Regra | Conta | Valor usado no desenho |
|---|---|---|
| Pulo simples | JumpHeight 7,2 → v₀ = √(2·196,2·7,2) ≈ 53 studs/s; tempo no ar 2·53/196,2 ≈ 0,54 s; a 24 studs/s (`WalkSpeed`) | sobe **7**, alcança **~13** no mesmo nível |
| Pulo duplo | `DoubleJumpVelocity` 50 → +50²/(2·196,2) ≈ 6,4 de altura além do 1º pulo; no ar ~0,9 s (prático) a 1,05 s (no último instante) | sobe **~13,5**, alcança **~22** (teórico 25) |
| "Sem gancho não passa" | acima do pulo duplo, com folga (igual ao tutorial) | vão **≥ 30**, degrau **≥ 20** |
| Respiro | pulo simples confortável | vão **≤ 10**, degrau **≤ 5** |
| Alcance do gancho | `Range` 40 contado do `HumanoidRootPart` (~3 acima dos pés); a esfera de ajuda (3) não aumenta o alcance; a folga de 10 do servidor é só para atraso de rede | nunca passar de **38** entre pontos de chegada |
| Espaçamento por rota | folga para mirar com o cursor | segura **≤ 35** · média **≤ 36** · rápida **≤ 38** |
| Tempo de um puxão | `PullSpeed` 58, `PullAccel` 180: chega a 58 em 0,32 s (9,3 studs); 30 studs ≈ 0,68 s; 40 ≈ 0,85 s; `Cooldown` 0,25 | puxão é rápido; o tempo real é mirar e pousar |
| Embalo | `ReleaseMomentumFraction` 0,45 × 58 ≈ **26 studs/s** ao chegar sem segurar; com pulo duplo (vale no embalo, ADR 0043/Q42) fica ~0,5 s no ar → **+13 na horizontal e +6 de altura** antes do próximo gancho | "salto de embalo": âncoras a até **~48–50** (precisa de playtest) |
| O que aparece na tela | câmera a 64 com FOV 50 → altura visível 2·64·tan 25° ≈ 60; centro 6 acima do personagem → vê **~36 acima** e **~24 abaixo** do root; largura 16:9 ≈ 106 (±53) | alvo para cima **≤ 34** acima do root; queda maior que 24 é "às cegas": sempre com chão ou sinal visível |

### Regra nova que saiu do código: onde pôr o gelo

Lendo o `FreezeController` e o `HookController`: congelar **solta a corda, acaba o embalo** e trava andar,
pular e gancho, mas a física continua (não ancora). Na prática:

- congelou **no ar** → cai quase reto (o Humanoid volta a controlar o corpo, sem A/D);
- congelou **em pé num chão** → fica parado até morrer em 15 s, porque sozinho ninguém o tira de lá
  (resgate por outro jogador, lâmina e cristal de degelo são das fases 4 e 5; humanoide parado não escorrega).

Proposta para a Fase 2 (solo primeiro, ADR 0023): **gelo só onde se encosta voando** (estalactites, lascas,
pingentes, tampas de borda) e **laranja logo embaixo**, na linha da queda. Errar o gelo vira "perder tempo"
ou "cair para a rota lenta", e não morte certa. Gelo de chão fica para quando houver resgate (dúvida 4).

## 3. Visão geral

```
           E9 Torre do Mago ↑ (fim no topo)
           ↑   E8 Coração da Montanha ← (3 andares)  ←  E7 Galeria dos Cristais ←  ✦Farol 2  ← E6 Pontes Quebradas ←
           |                                                                                             ↑
           |                                                                                  E5 Torre Partida ↑
           |                                                                                  E4 Escombros Flutuantes ↗
 Início → E1 Clareira dos Troncos → E2 Copa e Raízes → E3 Garganta Gelada → ✦Farol 1 ↗
```

- **Tamanho:** caixa de ~1.900 × 1.160 studs (o v2 tinha ~1.000 × 400). O mapa se enrola (ADR 0041): a
  Região A vai para a direita por baixo, a Região B sobe pela coluna da direita e volta para a esquerda, a
  Região C vem por cima para a esquerda, desce na montanha e termina subindo a torre.
- **3 regiões × 3 estágios = 9 estágios.** Checkpoints ("faróis", nome de trabalho) no fim do E3 e do E6;
  o fim (`RaceFinish`, também último checkpoint) no topo do E9. Com 9 estágios a regra "um a cada 3"
  fecha certinho; com 8, a última região teria só 2 estágios (dúvida 1).
- **Caminhos:** 22 rotas desenhadas nos 9 estágios (2 ou 3 por estágio), mais trocas de rota no meio
  (poços, janelas e escadas verdes). Duas bifurcações são grandes: **E2–E3** (copa x raízes, em andares
  diferentes) e **E8 → E9** (três andares que entram na torre em três alturas: quem vai pelo alto pula metade
  da torre).
- **Respiro** de 40 studs entre estágios, sem desafio (ADR 0041), com a placa do número do estágio.
- **Temas e nomes** são de trabalho, só para conversar: o visual de cada estágio é a Q24, que o dono adiou.

## 4. Os 9 estágios

Coordenadas em studs (X horizontal, Y altura), como em `maps/README.md`. "Ganchos" = quantos puxões a rota
pede. Tempo limpo = sem morrer, ritmo de jogador médio (seção 7).

### Região A — Bosque Antigo (E1–E3, para a direita)

**E1 · Clareira dos Troncos** (X 0–420, Y 0–140). Ensina: puxar de borda a borda e encadear no teto;
primeiro gelo e primeiro laranja, sem risco de morte. Já começa difícil (ADR 0041): chão mortal desde o início.
- *Segura, troncos:* 8 troncos com vão de 30 (sem gancho não passa), alturas de 70 a 90. 9 ganchos.
- *Rápida, nós do teto:* teto roxo com nós cinza a 36; no meio, uma **estalactite de gelo** obriga a descer
  num galho logo abaixo dela (6 studs de folga). Encostou → congela, cai reto numa **ilha laranja** no chão
  mortal, descongela e sai pela lateral do tronco 7 (perde ~6 s, não morre). 12 ganchos.
- Reservado: **V** (cristal de degelo) perto da ilha.

**E2 · Copa e Raízes** (X 460–880, Y 0–280). Ensina: escolher andar; roxo como "isca" no meio da fileira.
- *Rápida, copa:* sobe pelo átrio (4 ganchos na parede), depois folhas a 35 sobre a faixa mortal, com cipós
  vermelhos pendurados entre elas. Cair = morte. 16 ganchos, mas sempre no ar.
- *Segura, raízes:* túnel de 40 de altura, dentes no teto a 28; 2 dentes são roxos (desce, anda e engancha
  o próximo de baixo); 2 poços mortais no chão. 11 ganchos e bastante chão para recomeçar.
- *Média, troca:* das raízes, **poço 1** sobe para a copa no meio do estágio; o **poço 2** tem um verde no
  topo (sobe uma vez só por vida/checkpoint).

**E3 · Garganta Gelada** (X 920–1320, Y 0–320). Ensina: gelo sob pressão; teto roxo; subida vertical.
- *Rápida, cascata:* blocos a 34 no alto; duas **lascas de gelo** logo acima da linha. Congelou → cai na
  laje do meio, que é mortal **menos** os dois quadrados laranja bem embaixo das lascas; de lá, uma escadinha
  de 5 âncoras devolve à cascata. 10 ganchos.
- *Segura, salão + chaminé:* salão baixo com barriga roxa e estalactites a 30 sobre chão mortal, depois uma
  chaminé de 28 de largura com degraus alternados a 26 (9 degraus). 19 ganchos.
- As duas rotas terminam no **Farol 1** (checkpoint 1, X 1250–1310, Y 270).

### Região B — Ruínas Flutuantes (E4–E6, sobe pela direita e volta)

**E4 · Escombros Flutuantes** (X 1360–1900, Y 240–466). Ensina: verde como chave de atalho; salto de embalo.
- *Segura, blocos:* 15 blocos a 32 subindo devagar sobre o abismo mortal; 5 blocos roxos de isca. 16 ganchos.
- *Rápida, arco verde:* arco mais alto com **3 verdes** seguidos e 4 trechos de ~49 que só passam com
  embalo + pulo duplo. 12 ganchos. Quem erra no arco ainda pode se salvar nos blocos de baixo.

**E5 · Torre Partida** (X 1680–1900, Y 470–820). Ensina: subir em poço vertical segurando o gancho.
- *Rápida, poço:* poço de 24 de largura com paredes roxas e 13 degraus alternados a 26 (2 verdes, 2 lascas
  de gelo). Cair ou congelar → laranja no fundo, não morte. Mas os verdes não voltam até morrer ou passar
  de checkpoint: quem gastou e caiu fica sem os degraus 6 e 10 e tem de ir pela serpentina. 14 ganchos.
- *Segura, serpentina:* 5 andares em zigue-zague (abertura alternada, ponta roxa do outro lado). Cada andar
  sobe com uma consola na parede e a quina do andar de cima; dois andares têm faixa mortal atravessada por
  um bloco; uma lasca de gelo com laranja embaixo. 16 ganchos, ~73 s: é a rota mais lenta do mapa.
- *Média:* sobe 2 andares pela serpentina e entra no poço por uma **janela com verde**. 14 ganchos.
- Reservado: **J** (pedra-âncora de Júpiter) no fundo do poço, como 4º caminho no futuro.

**E6 · Pontes Quebradas** (X 1300–1900, Y 820–910, para a esquerda). Combina tudo: chão mortal, iscas roxas,
gelo pendurado.
- *Rápida, vigas do teto:* vigas cinza a 36, com vigas roxas de isca entre elas e 2 pingentes de gelo.
  16 ganchos.
- *Segura, pontes:* 10 pedaços de ponte com vão 30; um pingente sobre a ponte com laranja embaixo. 11 ganchos.
- Reservado: **B** (Bouncer): pega no começo, trecho no meio (3ª rota da Fase 4).
- Termina no **Farol 2** (checkpoint 2, X 1302–1338, Y 860).

### Região C — Caverna de Cristal e Torre do Mago (E7–E9)

**E7 · Galeria dos Cristais** (X 800–1260, Y 830–960, para a esquerda). Ensina: salto de embalo de verdade.
- *Rápida, embalo no teto:* âncoras no teto com **3 vãos de ~48** que só passam soltando o gancho com
  embalo e dando o pulo duplo antes de prender de novo. Errou = chão mortal. 12 ganchos.
- *Segura, cristais:* 14 cristais a 30, perto do chão; 2 lascas de gelo com laranja embaixo. 15 ganchos.
- Reservado: **M** (orbe de impulso de Mercúrio) no vão do meio.

**E8 · Coração da Montanha** (X 200–800, Y 440–830, para a esquerda, 3 andares). Um salão de descida na
entrada leva a três patamares:
- *Rápida, fio de prata* (alto): 15 âncoras soltas a 37 com iscas roxas; embaixo, laje mortal. 15 ganchos.
  **Entra na torre na altura 760** (pula metade do E9).
- *Média, gruta gelada* (meio): teto a 30, 3 lascas de gelo; chão mortal com laranja embaixo de cada lasca.
  19 ganchos. Entra na torre na altura 560.
- *Segura, túnel das raízes* (baixo): teto a 27, chão firme com 3 poços mortais. 21 ganchos. Entra na base.
- Trocas: um poço com verde do túnel para a gruta e dois verdes da gruta para o fio.
- Reservado: **L** (lâmina, resgate no gelo), **V** (cristal de degelo), **B** (trecho do Bouncer).

**E9 · Torre do Mago** (X 0–200, Y 440–1160, sobe). Fim no topo (`RaceFinish`, Y 1060).
- *Rápida, por fora:* canal entre a parede do mapa e a casca roxa da torre; bordas a 30 em linha reta,
  duas com tampa de gelo (passar do ponto = congela e cai no fosso mortal). 22 ganchos.
- *Segura, por dentro:* 6 lances; cada lance tem 3 degraus alternados a 26 e um patamar com buraco do lado
  oposto. Cair leva ao patamar de baixo, não à morte. 2 lascas de gelo com laranja. 24 ganchos.
- *Média, escada verde:* do patamar 760 (onde chega o fio de prata), 9 verdes a 30 passando por alçapões
  até o chão do fim.
- Reservado: **S** (totem de peso de Saturno + botão), que no futuro abriria um elevador.

## 5. Checkpoints, perigos e pontos reservados

| Item | Onde |
|---|---|
| Início (`RaceStart`) | E1, X 6–34, Y 70 (o portal do lobby leva para cá, ADR 0044) |
| Checkpoint 1 (`Order` 1) | fim do E3, onde cascata e chaminé se juntam |
| Checkpoint 2 (`Order` 2) | fim do E6, onde vigas e pontes se juntam |
| Fim (`RaceFinish` + `Checkpoint`, `Order` 3) | topo do E9; as 3 rotas da torre chegam nele |
| Vermelho (mortal) | chão de E1, copa do E2, salão do E3, abismo do E4, chão de E6/E7, lajes do E8, fosso do E9 |
| Gelo + laranja | E1 (estalactite/ilha), E3 (2 lascas/laje), E5 (poço e serpentina), E6 (pingentes), E7 (2), E8 (3), E9 (fora e dentro) |
| Roxo | tetos de E1/E2/E3/E6/E7/E8, dentes e blocos de isca, paredes do poço do E5, casca da torre |
| Verde | poço 2 do E2, arco do E4, poço e janela do E5, trocas do E8, escada do E9 |
| Reservados (sem efeito agora) | B Bouncer (E6, E8) · L lâmina (E8) · J Júpiter (E5) · M Mercúrio (E7) · V Vulcano (E1, E8) · S Saturno (E9) |

Nenhuma rota depende de ponto reservado: tudo é completável na Fase 2 só com gancho e pulo duplo.

## 6. Ensinar → testar → torcer (RF-73)

| Mecânica | Já vem do tutorial? | Ensina (seguro) | Testa (sob pressão) | Torce (combinada) |
|---|---|---|---|---|
| Puxão, segurar, encadear | sim | E1 | E2 | E5 poço, E9 |
| Roxo | sim | E1 (teto) | E2 (dentes) | E6 (iscas), E8 |
| Verde | sim | E2 (poço 2) | E4 (arco) | E5 (poço sem volta), E9 |
| Gelo + laranja | não | E1 (ilha) | E3 (cascata) | E6, E8, E9 |
| Vermelho | não | E1 (chão) | E2 (copa) | E8 (fio) |
| Embalo + pulo duplo | lição 6, em parte | E4 (blocos embaixo salvam) | E7 (teto) | — |

## 7. Tempo estimado (meta 10–15 min)

**Modelo** (para conferir no playtest): cada gancho custa, com mirar e pousar, 2,4 s na rota segura, 1,9 s na
média e 1,4 s na rápida; salto de embalo 1,6 s; andar a 24 studs/s; +15 % de erros que não matam. Cada
morte custa 1 s de renascer + 80 % do tempo dos estágios já feitos na região + metade do estágio atual.

| Estágio | Rápida (limpo) | Segura (limpo, +15 %) | Mortes esperadas (médio) | Esperado, médio na rota segura |
|---|---|---|---|---|
| E1 | 19 s | 34 s | 0,5 | 42 s |
| E2 | 23 s | 38 s | 0,75 | 73 s |
| E3 | 17 s | 57 s | 0,75 | 122 s |
| E4 | 22 s | 47 s | 0,5 | 59 s |
| E5 | 21 s | 84 s | 0,5 | 124 s |
| E6 | 24 s | 45 s | 0,75 | 141 s |
| E7 | 20 s | 44 s | 0,5 | 56 s |
| E8 | 24 s | 62 s | 0,75 | 113 s |
| E9 | 41 s | 100 s | 0,4 | 154 s |
| **Total** | **~3,5 min** limpo | **~8,5 min** limpo (7,4 sem os 15 %) | ~5,4 mortes | **~14,8 min** |

- **Jogador médio:** ~14,8 min só pelas rotas seguras; **~13,5 min** misturando as médias (E2, E5, E8, E9).
  Fica dentro da meta, perto do teto.
- **Jogador bom** (rápidas, 40 % das mortes): ~5 min. **Iniciante** (seguras, 2× mortes, +30 %): ~25 min.
- O que mais pesa: E9 (torre longa, morte volta ao Farol 2) e a serpentina do E5. São as primeiras a encurtar
  se o playtest passar de 15 min.

## 8. Como o rascunho foi feito e conferido

- O SVG foi gerado por um script Python provisório (fora do projeto, na pasta temporária da sessão; **não**
  mexi em `tools/`). Ele guarda as peças e as rotas como pontos de chegada, confere cada puxão contra o
  limite da rota (35/36/38), cada alvo contra a altura visível (≤ 34 acima), pulos e quedas, e soma o tempo.
  Resultado final: **0 problemas** em 22 rotas.
- O que a conta **não** garante: pousos em quinas, o embalo real (vãos de ~48 do E4/E7), a mira com o cursor
  em alvos pequenos, colisão do corpo com o gelo perto da linha. Isso é do greybox e do playtest.
- Próximo passo, se o dono aprovar: passar este layout para `tools/map_layout.py` (v3) e gerar
  `layout.json`/`build.luau` com `tools/map2d.py` (dúvida 12).

## 9. Dúvidas para o dono

Só propostas; nenhuma foi decidida. A Q23 (evolução do gancho) e a Q24 (tema visual) continuam abertas em
`03-duvidas/`, e o desenho não depende da resposta delas.

1. **8 ou 9 estágios?** Proposta: 9 (3 regiões × 3; checkpoint a cada 3 fecha certinho). Com 8, junto o E8 e o E9.
2. **Tamanho ~1.900 × 1.160 studs** (quase o dobro do v2 em largura e quase 3× em altura). Pode?
3. **Nomes e temas** dos estágios e regiões são só de trabalho (Q24 adiada). Posso usá-los nas placas do greybox?
4. **Gelo só onde se encosta voando** (com laranja na linha da queda), sem gelo de chão até haver resgate
   (fases 4/5)? Hoje, congelar em pé sozinho = morte certa em 15 s.
5. **Queda:** nas rotas seguras, cair leva a um chão que não mata (perde tempo); nas rápidas, cair mata e
   volta ao checkpoint. Isso afrouxa o "queda = checkpoint quase sempre" do ADR 0041. Pode?
6. **Nível do gancho:** o mapa foi medido com o alcance inicial (40). Com mais alcance (Q23), as rotas rápidas
   ficam mais fáceis. Tudo bem, ou alguma rota deve exigir nível?
7. **Verde no poço do E5:** gastou os verdes e caiu (sem morrer), o poço fecha até morrer ou passar de
   checkpoint, e sobra a serpentina. Pode ser assim?
8. **Salto de embalo** (vãos de ~48 no E4 e no E7, só com embalo + pulo duplo) entra no mapa? Se sim, vale uma
   lição a mais no tutorial?
9. **Tempo:** médio estimado em 13,5–14,8 min, perto do teto. Mantém, ou já encurto o E9 e a serpentina do E5?
10. **Entradas da torre em 3 alturas** (quem vai pelo fio de prata no E8 pula metade do E9). Pode haver esse
    "atalho grande" no fim?
11. **Respiros de 40 studs** com placa de número do estágio entre todos os estágios. Ok?
12. **Map02 ou Map01:** o mapa novo substitui o `Workspace.Maps.Map01` do place ou vira `Map02` ao lado (com o
    v2 guardado para teste)?
