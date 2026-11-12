# Requisitos do MVP — Race and Escape

> Fonte: GAME_DESIGN v0.3 e ADRs 0001–0028. Cada requisito tem um ID estável (`RF-xx` funcional,
> `RNF-xx` não funcional) e um critério de aceite verificável. Ao implementar, cite o ID no commit.
> Valores numéricos são **padrões iniciais** em `Config` (ajustáveis em playtest e por boosts, ADR 0025).

## 1. Escopo

**Dentro do MVP:** lobby simples, um mapa labirinto 2.5D com várias rotas, câmera 2.5D, gancho,
gelo/descongelar, zona mortal, checkpoints, timer pessoal, Bouncer, lâmina, objetos mágicos
(sempre ativos), interação entre todos os jogadores.

**Fora do MVP:** Bond, salvar dados entre sessões, ranking persistente, loja, boosts, tutorial
guiado, celular/console.

## 2. Requisitos funcionais

### Personagem e câmera
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-01 | Câmera lateral 2.5D segue o personagem | Personagem sempre visível e centralizado com leve folga; sem tremor ao balançar |
| RF-02 | Personagem preso ao plano do mapa (eixo Z fixo) | Após 5 min de jogo, desvio em Z < 0,1 stud, mesmo sendo puxado/empurrado |
| RF-03 | Movimento base = padrão do Roblox (andar, pular). Sem pulo duplo (ADR 0027) | A/D anda, Espaço pula; W/S não tiram do plano |

### Gancho (ADR 0003, 0016)
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-10 | Mira com o mouse no plano 2.5D | O gancho sai na direção do cursor |
| RF-11 | **Segurar** o botão do mouse = preso; soltar = solta | Soltar a qualquer momento libera na hora |
| RF-12 | Gruda em qualquer superfície, exceto `NoHook` (roxo) | Acerto em `NoHook` não prende e mostra feedback visual |
| RF-13 | `HookOnce` (verde): 1 uso por jogador; volta ao morrer ou passar checkpoint | 2ª tentativa falha; após morrer/checkpoint funciona de novo |
| RF-14 | Alcance máximo e força de puxão configuráveis (`Config.Hook`) | Mudar o Config muda o comportamento sem tocar no código |
| RF-15 | Enganchar outro jogador puxa os dois | Ambos se aproximam; funciona com ping de 150 ms |
| RF-16 | Corda visível para todos os jogadores | Outros clientes veem a corda em até 200 ms |

### Gelo, morte e checkpoints (ADR 0014, 0018, 0021)
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-20 | `FreezeZone` (azul-gelo) congela por 15 s | Congelado não anda, não pula, não usa gancho/Bouncer/lâmina |
| RF-21 | Congelado ainda pode ser puxado e empurrado | Gancho/lâmina de outro jogador o movem |
| RF-22 | `UnfreezeZone` (laranja-brasa) descongela na hora | Ao entrar, volta ao normal |
| RF-23 | Lâmina descongela quem acerta | Acerto em congelado o descongela |
| RF-24 | Fim dos 15 s congelado = morte | Renasce no último checkpoint |
| RF-25 | `KillZone` (vermelho) mata na hora; é grudável | Toque = respawn no checkpoint |
| RF-26 | Checkpoints pessoais, na ordem | Pular checkpoint não conta; morte volta ao último válido |
| RF-27 | HUD mostra contagem regressiva do gelo | Número/barra visível enquanto congelado |

### Bouncer (ADR 0017, 0024)
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-30 | Pego em `BouncerPickup`, válido dentro de `BouncerZone` | Some ao sair da zona e ao morrer |
| RF-31 | Tiro impulsiona o atirador para o lado oposto da mira | Impulso imediato, sem atraso perceptível |
| RF-32 | Munição com recarga automática | HUD mostra cargas; sem cargas não atira |
| RF-33 | Tiro empurra um pouco outros jogadores atingidos | Empurrão visível e bem menor que o impulso próprio |

### Lâmina (ADR 0019, 0024)
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-40 | Golpe corpo a corpo com cooldown | Empurra quem estiver no alcance curto, na direção do golpe |
| RF-41 | Sem dano; descongela (ver RF-23) | — |

### Objetos mágicos (ADR 0004, 0023, 0026)
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-50 | Júpiter: ponto que puxa para cima com mais força | Enganchar nele eleva mais que superfície comum |
| RF-51 | Mercúrio: enganchado, arremessa na direção marcada | Trajetória repetível |
| RF-52 | Vulcano: atingido pelo gancho, descongela o jogador (alcance curto, funciona congelado) | Exceção controlada a RF-20 |
| RF-53 | Saturno: bloco arrastável pelo gancho que segura botões | Botão fica pressionado enquanto o bloco está nele |
| RF-54 | No MVP, objetos ativos para todos | — |

### Corrida e lobby
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-60 | Lobby simples: área de nascimento com portal para o mapa | Entrar no portal leva ao início do mapa |
| RF-61 | Timer pessoal começa no `RaceStart` e para no `RaceFinish` | Tempo exibido no HUD, precisão de 0,01 s |
| RF-62 | Ao terminar: tela com tempo e opção "de novo" / "voltar ao lobby" | — |
| RF-63 | Placar da sessão (melhor tempo de cada jogador no servidor) | Visível no lobby; zera quando o servidor fecha |

### Mapa
| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-70 | Um mapa labirinto 2.5D com várias rotas (ADR 0012, 0022) | Cada seção tem ≥ 1 rota segura e ≥ 1 rota rápida |
| RF-71 | Checkpoints a cada ~3 min para um jogador médio | Medido em playtest |
| RF-72 | Completável sozinho e em grupo | Playtest dos dois jeitos |
| RF-73 | Todas as mecânicas usadas, ensinadas antes de combinadas | Revisão de level design |

## 3. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Luau `--!strict` em todo arquivo; Selene e StyLua sem erros |
| RNF-02 | Servidor é autoridade de estado (gelo, checkpoint, timer, munição, uso do verde) (ADR 0006) |
| RNF-03 | Todo remote valida tipos, alcance e faz rate limit |
| RNF-04 | Lógica pura em `src/shared/Logic`, testável sem o Studio |
| RNF-05 | Comportamento do mapa só por tags do CollectionService; nenhum script dentro do mapa |
| RNF-06 | Nenhum número mágico: tudo em `Config` |
| RNF-07 | Regra "A pode afetar B?" só em `InteractionPolicy` |
| RNF-08 | 60 FPS em PC médio com 20 jogadores no servidor |
| RNF-09 | Sem vazamento: conexões limpas com Trove ao morrer/sair |
