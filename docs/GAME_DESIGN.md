# Game Design Document (rascunho v0.1)

> Codinome: **dddrace-roblox** (nome final a definir; vamos criar uma identidade própria,
> inspirada no gênero "race cooperativo", sem copiar arte, nomes ou mapas de outros jogos).
> Visão geral em linguagem simples: [README](../README.md).

## 1. Pitch

Plataforma de **fantasia** em servidor aberto. Os jogadores usam um **gancho mágico** para se
balançar e puxar uns aos outros, desviam de **gelo mágico** e atravessam mapas que podem ser
feitos **sozinho ou em equipe**. Falhar não mata: congela. Em equipe, seu parceiro te salva.

**Tema:** fantasia (ruínas flutuantes, florestas mágicas, cavernas de cristal, torres de magos).

**Pilares (toda decisão de design deve servir a pelo menos um):**

1. **Cooperação recompensada, solo sempre possível**: todo mapa pode ser terminado sozinho;
   jogar em equipe abre jeitos diferentes (e mais divertidos) de passar pelos obstáculos.
2. **Movimento com skill**: o gancho tem um teto de habilidade alto (balanço, momentum, timing).
3. **Falha barata**: congelar custa segundos, não progresso. Sem frustração de "voltar tudo".
4. **Legibilidade**: qualquer jogador entende o que uma superfície faz só pela cor e textura.

## 2. Core loop

```
Hub → escolhe mapa (por dificuldade) → joga solo OU forma equipe (Bond) → corre seções entre checkpoints
   → termina → tempo no ranking + moedas/XP → desbloqueia cosméticos e mapas → volta ao Hub
```

Sessão-alvo: 10–25 min. Um mapa fácil leva de 3 a 6 min; um difícil, 15 min ou mais.

## 3. Mecânicas

| Mecânica | Descrição | Notas de design |
|---|---|---|
| **Gancho** | Dispara na direção da mira; prende em superfície *enganchável* e puxa o jogador. Se acertar um parceiro, **puxa os dois um em direção ao outro** (decidido). | Alcance fixo (~40 studs), cooldown curto. Mobile: botão dedicado + mira automática assistida. |
| **Empurrão** | Ataque de curto alcance que empurra parceiro e descongela. | Principal ferramenta para "lançar" o parceiro. |
| **Congelamento** | Ao tocar zona de gelo, o jogador congela: não anda nem usa gancho, mas **pode ser enganchado e empurrado**. | Descongela sozinho após X s **ou** ao entrar em zona de descongelamento. |
| **Descongelamento** | Zona que tira o congelamento imediatamente. | Normalmente fica do "outro lado" de um obstáculo: o parceiro te leva até lá. |
| **Superfícies** | Enganchável / não enganchável / mortal (teleporta pro checkpoint). | Linguagem visual fixa (ver §6). |
| **Checkpoints** | Salvam o progresso **da dupla**. | Um a cada 30–90 s de jogo para um jogador médio. |
| **Botões/portas** | Um jogador segura e o outro passa. | Clássico de coop, barato de construir. |

### 3.1 Bond (como o coop funciona em servidor aberto)

Servidor aberto tem um problema conhecido do gênero: um estranho pode te enganchar e jogar no
gelo (griefing). Solução proposta:

- Jogadores **sem Bond** não colidem nem interagem com outros (CollisionGroup "Ghost").
- No início do mapa há um **Portal de Bond**: 2–4 jogadores entram juntos e viram uma equipe.
- Só membros da mesma equipe podem enganchar/empurrar uns aos outros e compartilham checkpoints e timer.
- Botão "Procurar parceiro" no Hub para quem chega sozinho (matchmaking leve dentro do servidor).
- Sair da equipe é imediato. Ficar AFK por um tempo dissolve a equipe.
- O Portal de Bond é opcional: quem passa direto joga **solo** (equipe de 1).

### 3.2 Jogo solo

Requisito: muita gente não tem com quem jogar, então **todo mapa precisa ser concluível sozinho**.
O desafio de design é não tornar os obstáculos de coop inúteis no solo.

**Decisão: objetos mágicos que substituem o parceiro.** No modo solo, aparecem objetos que fazem o
papel do colega. O mesmo mapa serve para os dois modos. Uma rota paralela só entra como exceção,
quando nenhum objeto resolve bem o obstáculo.

Regras:

- O modo é definido ao passar (ou não) pelo Portal de Bond. Os objetos são ativados por tags:
  `SoloOnly` aparece só para quem está sozinho, `TeamOnly` só para equipes.
- Os objetos existem **só para o jogador solo** (renderizados no cliente dele, validados no
  servidor). Assim dois jogadores solo no mesmo trecho não atrapalham um ao outro.
- Cada padrão de coop da §5 precisa ter um objeto equivalente:

| Padrão de coop | Objeto mágico (nomes provisórios) | Como funciona |
|---|---|---|
| Elevador | **Pedra-âncora** | Ponto enganchável que puxa o jogador para cima com mais força. |
| Lançamento | **Orbe de impulso** | Ao ser enganchado, arremessa o jogador na direção marcada. |
| Resgate | **Cristal de degelo** | Atingido pelo gancho, descongela o jogador. Funciona até congelado, então tem alcance curto. |
| Ponte (botão) | **Totem de peso** | Bloco que o jogador arrasta com o gancho até o botão. |
| Revezamento | Combinação dos acima | Cada obstáculo usa um objeto diferente. |

- Objetos são **prefabs reutilizáveis**: o level designer só posiciona e marca a tag.
- Balanceamento: o solo deve ser **um pouco mais lento** que a equipe, nunca mais rápido.
  Rankings separados para solo e equipe.

## 4. Estrutura de mundo

- **Hub**: área social com portais por dificuldade, leaderboards físicos (placas 3D), loja de cosméticos.
- **Tutorial** (obrigatório na primeira vez, ~2 min): ensina gancho → gelo → parceiro, nessa ordem.
- **Mapas** por tiers (nomes próprios a definir): Iniciante, Intermediário, Avançado, Extremo.
- Cada mapa: 5–12 **seções** entre checkpoints, cada seção com uma ideia central.

## 5. Princípios de design de fases

Práticas que os obbies e jogos de plataforma mais bem-sucedidos do Roblox (e fora dele) usam:

1. **Ensinar → Testar → Torcer.** Cada mecânica aparece primeiro num lugar seguro, depois sob
   pressão e depois combinada com outra. Nunca introduza duas ideias novas na mesma seção.
2. **Os primeiros 60 segundos decidem a retenção.** O jogador precisa enganchar algo nos primeiros
   10 s e sentir uma pequena vitória antes de 1 min. Nada de texto longo.
3. **Ritmo de tensão e alívio.** Depois de um trecho difícil vem uma área calma (checkpoint, vista
   bonita, coletável). Dificuldade sobe em "dentes de serra", não em linha reta.
4. **Coop por design de espaço.** Padrões reutilizáveis:
   - *Elevador*: um jogador sobe e engancha o outro para cima.
   - *Ponte*: um segura um botão ou fica de "âncora" para o outro balançar.
   - *Resgate*: passagem obrigatória por gelo; o parceiro te puxa até o descongelamento.
   - *Lançamento*: empurrão + gancho para cruzar um vão impossível sozinho.
   - *Revezamento*: os jogadores trocam de papel a cada obstáculo.
5. **Linhas de condução.** Iluminação, cor e geometria apontam o caminho; o jogador nunca deve
   procurar "para onde eu vou?". Use marcos visuais altos visíveis de longe.
6. **Falha visível e justa.** Hitboxes do tamanho do visual, sem gelo "escondido". Se o jogador
   morrer, ele deve saber por quê.
7. **Rotas para níveis de skill diferentes.** Atalhos opcionais para jogadores avançados
   (speedrun) e coletáveis fora da rota principal; o caminho padrão continua acessível.
8. **Mobile-first.** Boa parte do público do Roblox joga no celular: vãos e timings precisam ser
   jogáveis no touch, e a câmera não pode ficar presa em paredes.
9. **Orçamento de tamanho.** Seções compactas (streaming eficiente, menos partes); prefira
   reaproveitar *prefabs* de obstáculos a modelar tudo do zero.

### 5.1 Processo de produção de um mapa

1. **Papel**: lista de seções (ideia central de cada uma + papel de cada jogador).
2. **Greybox** no Studio só com blocos e as cores da §6, sem arte.
3. **Playtest em dupla**: medir tempo por seção e onde as pessoas congelam/desistem.
4. **Iterar** até o tempo médio por seção bater a meta do tier.
5. **Arte/iluminação** só depois do layout aprovado.

## 5.2 Câmera: 2.5D lateral (decidido, ADR 0011)

Visão lateral com profundidade só visual: o personagem anda num plano (esquerda/direita + pulo).
Cada mapa é um labirinto 2.5D com **várias rotas até o final** (ADR 0012): rotas se dividem e se
juntam, com pelo menos uma segura e uma rápida/arriscada.

Comparação que levou à decisão:

| | 2.5D lateral | 3ª pessoa livre |
|---|---|---|
| Mira do gancho | Simples (plano 2D), ótima no celular | Precisa de mira 3D/assistida |
| Design de fases | Mais controlado e legível | Mais liberdade, mais difícil de balancear |
| Exploração | Limitada ao plano | Ampla |
| Identidade | Diferencia o jogo no Roblox | Padrão de obbies |

## 6. Linguagem visual (fixa em todos os mapas)

Cores fixas, com materiais de fantasia (pedra rúnica, cristal, musgo luminoso) aplicados por cima.

| Elemento | Cor / material | Tag (CollectionService) |
|---|---|---|
| Enganchável | Cinza claro, textura de grade | `Hookable` |
| Não enganchável | Escuro, liso | (padrão) |
| Congelamento | Azul gelo, translúcido, partículas | `FreezeZone` |
| Descongelamento | Verde, brilho | `UnfreezeZone` |
| Mortal | Vermelho pulsante | `KillZone` |
| Checkpoint | Faixa dourada no chão | `Checkpoint` |
| Início / Fim | Arcos com placa | `RaceStart` / `RaceFinish` |

## 7. Progressão e monetização (ética)

- **XP e moedas** por mapa concluído; bônus por primeira conclusão e por recorde pessoal.
- **Cosméticos**: trilhas, skin do gancho, efeito de congelamento, títulos. Nada que dê vantagem.
- **Game Passes**: cosméticos e, no máximo, conveniências (ex.: salvar replay). Sem "pular fase".
- **Rankings**: por mapa (melhor tempo da equipe), diário/semanal/global.

## 8. Escopo do MVP

Somente o que valida a diversão: gancho, gelo/descongelamento, modo solo, Bond em dupla,
checkpoints, timer, 1 tutorial + 2 mapas (Iniciante e Intermediário), salvamento de recordes.
Fora do MVP: loja, replays, editor de mapas, trios/quartetos.

## 9. Decisões

| Tema | Decisão |
|---|---|
| Tema visual | Fantasia |
| Gancho em parceiro | Puxa os dois |
| Solo | Todo mapa concluível sozinho |
| Solo nas seções de coop | Objetos mágicos substituem o parceiro (§3.2) |

## 10. Perguntas em aberto

- Nome do jogo.
- Câmera: 2.5D lateral (ver §5.2).
- Nomes e visual finais dos objetos mágicos do modo solo.
- Tamanho máximo de equipe (2, 3 ou 4). O código vai suportar N jogadores; o limite é só configuração.
