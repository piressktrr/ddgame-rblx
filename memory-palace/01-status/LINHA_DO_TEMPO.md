# Linha do tempo do projeto

> Porta de entrada para quem chega agora. Mostra, em ordem, **tudo o que foi criado e decidido** desde o
> primeiro dia, com links para os documentos de cada momento. Nada aqui substitui os documentos: é só o índice
> cronológico deles.
>
> Ordem de leitura para quem é novo: [`AGENTS.md`](../../AGENTS.md) (regras) → [`README do palácio`](../README.md)
> (mapa das salas) → **esta linha do tempo** → [`STATUS`](STATUS.md) (onde paramos agora).

## Como os documentos se dividem

| Tipo | O que é | Arquivos |
|---|---|---|
| **Histórico** (não muda depois de escrito) | O que aconteceu e o que foi decidido, em ordem | Diários `diario/AAAA-MM-DD.md`, decisões `02-decisoes/NNNN-*.md` (o número é a ordem), commits |
| **Vivo** (sempre na versão atual) | Como o jogo é **hoje** | [GAME_DESIGN](../04-game-design/GAME_DESIGN.md), [REQUIREMENTS](../05-arquitetura/REQUIREMENTS.md), [IMPLEMENTATION_PLAN](../05-arquitetura/IMPLEMENTATION_PLAN.md), [ARCHITECTURE](../05-arquitetura/ARCHITECTURE.md), [OPEN_QUESTIONS](../03-duvidas/OPEN_QUESTIONS.md), [GLOSSARY](../06-glossario/GLOSSARY.md), [TOOLS](../07-toolchain/TOOLS.md) |
| **Estudos** (fotografia de um momento) | Pesquisas e rascunhos que levaram a decisões | [`04-game-design/estudos/`](../04-game-design/estudos/) |

Quando uma decisão muda, a antiga não é apagada: ganha o status "Substituída por NNNN". As trocas principais:
0002 → 0013 (Bond), 0010 → 0022 (MVP com um mapa), 0027 → 0043 (pulo duplo), 0031/0035 → 0038 (fim do experimento 3D),
0036 → 0042 (gancho de balanço vira puxão), 0029/0041 → 0047 (mapa de 8+ estágios com vários caminhos).

## Resumo por dia

| Dia | Fase | Em uma frase |
|---|---|---|
| [2026-11-11](#2026-11-11--início) | Início | Ferramentas, esqueleto do código e primeiras decisões (0001–0007) |
| [2026-11-12](#2026-11-12--fundação-e-design) | Fundação e design | Palácio da memória, design v0.3, decisões 0008–0028, requisitos, plano e o primeiro mapa |
| [2026-11-15](#2026-11-15--experimento-de-câmera-e-reorganização) | Experimento | Mapa em 6 estágios, experimento de câmera (reprovado), checkpoints, palácio reorganizado |
| [2026-11-16](#2026-11-16--25d-e-gancho) | 2.5D e gancho | Jogo fica 2.5D, mapa v2, gancho (balanço → puxão), corda para todos, pulo duplo e lobby |
| [2026-11-17](#2026-11-17--fase-3-zonas-corrida-tutorial) | Fase 3 | PR para a main, decisões 0045–0048, zonas, timer/HUD, tutorial e testes |

---

## 2026-11-11 — Início
Diário: [diario/2026-11-11.md](diario/2026-11-11.md)

- **Ferramentas:** Rokit, Rojo, Wally, Selene, StyLua → [TOOLS](../07-toolchain/TOOLS.md), [UNINSTALL](../07-toolchain/UNINSTALL.md).
- **Esqueleto do código (M0):** Loader, Config, Types em `src/`.
- **Documentos criados:** [GAME_DESIGN](../04-game-design/GAME_DESIGN.md) (v0.1), [ARCHITECTURE](../05-arquitetura/ARCHITECTURE.md).
- **Decisões:**
  [0001](../02-decisoes/0001-genero-e-originalidade.md) gênero e originalidade ·
  [0002](../02-decisoes/0002-servidores-abertos-e-bond.md) servidores abertos e Bond ·
  [0003](../02-decisoes/0003-gancho-puxa-os-dois.md) gancho puxa os dois ·
  [0004](../02-decisoes/0004-solo-com-objetos-magicos.md) solo com objetos mágicos ·
  [0005](../02-decisoes/0005-toolchain-rojo.md) Rojo ·
  [0006](../02-decisoes/0006-autoridade-servidor-cliente.md) servidor × cliente ·
  [0007](../02-decisoes/0007-loader-sem-framework.md) loader sem framework.

## 2026-11-12 — Fundação e design
Diário: [diario/2026-11-12.md](diario/2026-11-12.md) · Commits `8333334`, `f8e63aa`, `fcc8f76`, `ff51786`, `e6ede2c`

- **MCP do Studio conectado**, M0 testado em playtest.
- **Palácio da memória criado:** [AGENTS.md](../../AGENTS.md), [STATUS](STATUS.md), [OPEN_QUESTIONS](../03-duvidas/OPEN_QUESTIONS.md), [GLOSSARY](../06-glossario/GLOSSARY.md) (na época em `docs/`).
- **Design v0.2 e v0.3** no [GAME_DESIGN](../04-game-design/GAME_DESIGN.md).
- **Decisões:**
  [0008](../02-decisoes/0008-nome-race-and-escape.md) nome ·
  [0009](../02-decisoes/0009-foco-pc.md) foco no PC ·
  [0010](../02-decisoes/0010-mvp-mapas.md) MVP com 2 mapas ·
  [0011](../02-decisoes/0011-camera-2-5d.md) câmera 2.5D ·
  [0012](../02-decisoes/0012-varias-rotas.md) várias rotas ·
  [0013](../02-decisoes/0013-sem-bond-por-enquanto.md) sem Bond ·
  [0014](../02-decisoes/0014-gelo-mata.md) gelo mata ·
  [0015](../02-decisoes/0015-cores.md) cores ·
  [0016](../02-decisoes/0016-gancho-regras.md) regras do gancho ·
  [0017](../02-decisoes/0017-bouncer.md) Bouncer ·
  [0018](../02-decisoes/0018-progresso-por-jogador.md) progresso por jogador ·
  [0019](../02-decisoes/0019-lamina-magica.md) lâmina ·
  [0020](../02-decisoes/0020-mesmo-mapa-solo-e-grupo.md) mesmo mapa solo e grupo ·
  [0021](../02-decisoes/0021-cores-finais.md) cores finais ·
  [0022](../02-decisoes/0022-mvp-um-mapa.md) MVP com um mapa ·
  [0023](../02-decisoes/0023-solo-primeiro.md) solo primeiro ·
  [0024](../02-decisoes/0024-detalhes-ferramentas.md) detalhes das ferramentas ·
  [0025](../02-decisoes/0025-monetizacao-com-vantagens.md) monetização ·
  [0026](../02-decisoes/0026-objetos-deuses-romanos.md) deuses romanos ·
  [0027](../02-decisoes/0027-sem-pulo-duplo.md) sem pulo duplo ·
  [0028](../02-decisoes/0028-ranking-separa-boost.md) ranking separa boost.
- **Requisitos e plano:** [REQUIREMENTS](../05-arquitetura/REQUIREMENTS.md), [IMPLEMENTATION_PLAN](../05-arquitetura/IMPLEMENTATION_PLAN.md) (4 fases na época).
- **Estudos e referências:** [ferramentas-bouncer-lamina](../04-game-design/estudos/ferramentas-bouncer-lamina.md), [cores-descongelar.html](../04-game-design/referencias/cores-descongelar.html).
- **Código e mapa:** câmera 2.5D, trava no plano, primeiro greybox `maps/map01` (gerado por `tools/mapgen.py`, hoje obsoleto).

## 2026-11-15 — Experimento de câmera e reorganização
Diário: [diario/2026-11-15.md](diario/2026-11-15.md) · Commit `b3779b4` · PR #1 (merge na main)

- **Estudo:** [referencias-mapas](../04-game-design/estudos/referencias-mapas.md) (padrões do gênero e jogos lineares do Roblox).
- **Decisões:**
  [0029](../02-decisoes/0029-mapa-em-estagios.md) mapa em 6 estágios ·
  [0030](../02-decisoes/0030-progressao-de-atributo.md) progressão por atributo ·
  [0031](../02-decisoes/0031-experimento-de-camera.md) experimento de câmera ·
  [0032](../02-decisoes/0032-rebirth-proposta.md) rebirth (proposta) ·
  [0033](../02-decisoes/0033-gancho-no-centro.md) gancho no centro ·
  [0034](../02-decisoes/0034-checkpoint-a-cada-3-estagios.md) checkpoint a cada 3 estágios ·
  [0035](../02-decisoes/0035-mapa-do-experimento-reprovado.md) greybox do experimento reprovado.
- **Palácio reorganizado:** `docs/` e `images/` viraram as salas 01–07 de `memory-palace/`.
- **Código:** `CheckpointService` mínimo; mapa do experimento em 6 estágios (arquivos removidos no dia 16, continuam no commit `b3779b4`).
- **Resultado:** o dono reprovou o greybox (curto, estreito, fácil).

## 2026-11-16 — 2.5D e gancho
Diário: [diario/2026-11-16.md](diario/2026-11-16.md) · Commits `2fc7028`, `f9dd900`, `8de9cfd`

- **Estudo:** [gancho-o-que-precisa](../04-game-design/estudos/gancho-o-que-precisa.md).
- **Decisões:**
  [0036](../02-decisoes/0036-gancho-balanco-ropeconstraint.md) gancho de balanço ·
  [0037](../02-decisoes/0037-gancho-em-jogador.md) gancho em jogador ·
  [0038](../02-decisoes/0038-camera-2-5d-definitiva.md) o jogo é 2.5D ·
  [0039](../02-decisoes/0039-regras-do-plano-2-5d.md) regras do plano ·
  [0040](../02-decisoes/0040-checkpoint-mvp-e-ordem-das-fases.md) duração e ordem das fases ·
  [0041](../02-decisoes/0041-mapa-enrolado-e-tutorial.md) mapa enrolado e tutorial ·
  [0042](../02-decisoes/0042-gancho-puxao-direto.md) gancho de puxão ·
  [0043](../02-decisoes/0043-pulo-duplo-e-velocidade.md) pulo duplo e velocidade ·
  [0044](../02-decisoes/0044-lobby-greybox.md) lobby.
- **Rascunhos do mapa 2.5D:** [v0](../04-game-design/estudos/mapa-2-5d/rascunho-v0.png), [v1](../04-game-design/estudos/mapa-2-5d/rascunho-v1.png), [v2](../04-game-design/estudos/mapa-2-5d/rascunho-v2.png) (`tools/map_sketch.py`).
- **Mapa v2 no Studio:** `tools/map_layout.py` → `tools/map2d.py` → [`maps/map01`](../../maps/README.md).
- **Código:** protótipo do gancho (balanço), depois puxão direto com pose de voo; corda visível para todos (RF-16);
  pulo duplo e WalkSpeed 24 (`MovementController`); lobby (`LobbyService`, `maps/lobby`).

## 2026-11-17 — Fase 3: zonas, corrida, tutorial
Diário: [diario/2026-11-17.md](diario/2026-11-17.md) · Commit `7c05f55` · PR [#2](https://github.com/piressktrr/ddgame-rblx/pull/2) para a main

- **Pulo duplo depois do gancho** testado e ajustado (Q42).
- **Decisões:**
  [0045](../02-decisoes/0045-gelo-fica-15s.md) gelo em 15 s ·
  [0046](../02-decisoes/0046-movimento-pelo-gancho.md) percurso quase todo com o gancho ·
  [0047](../02-decisoes/0047-mapa-8-estagios-varios-caminhos.md) mapa de 8+ estágios com vários caminhos ·
  [0048](../02-decisoes/0048-nivel-do-gancho-salvo.md) nível do gancho salvo.
- **Código (ainda sem commit e sem playtest completo):** zonas (`ZoneService`, `FreezeController`), corrida e HUD
  (`RaceService`, `UIController`), tutorial do gancho ([`maps/tutorial`](../../maps/README.md)), testes com TestEZ (`tests/`).
  Revisado por leitura no mesmo dia, com correções na chegada, no "De novo" e na interface.
- **Estudo:** [mapa da Fase 2](../04-game-design/estudos/mapa-fase2.md) (9 estágios, 22 rotas) com
  [rascunho](../04-game-design/estudos/mapa-2-5d/rascunho-fase2.svg) gerado por `tools/map_sketch_fase2.py`.
  Dúvidas Q43–Q55, respondidas no mesmo dia:
  [0049](../02-decisoes/0049-killzone-aceita-gancho.md) zona mortal aceita o gancho ·
  [0050](../02-decisoes/0050-mapa-fase2-aprovado.md) mapa da Fase 2 aprovado ·
  [0051](../02-decisoes/0051-ad-no-embalo-fica.md) A/D no embalo fica.
- **Greybox do mapa novo** (9 estágios, substitui o Map01) e **lição 7 do tutorial** (salto de embalo), montados
  no Studio; sem playtest do mapa.
- **Hoje:** veja o [STATUS](STATUS.md) para o próximo passo.
