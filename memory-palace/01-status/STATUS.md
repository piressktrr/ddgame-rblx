# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos (2026-11-17)

- **Branch:** `feature/implement-the-map`. PR [#2](https://github.com/piressktrr/ddgame-rblx/pull/2) com merge na
  `main` (`bd7a03c`); o trabalho abaixo vai num PR novo.
- **Fase 1 (gancho solo):** puxão (ADR 0042), corda para todos (RF-16), pulo duplo e WalkSpeed 24 (ADR 0043). Falta o
  dono aprovar o *feel* com mouse e teclado.
- **Fase 3 (adiantada, código pronto, sem playtest):** `ZoneService` + `FreezeController` (KillZone, gelo 15 s,
  descongelar, gancho/pulo negados congelado); `RaceService` + `UIController` (timer 0,01 s, tela de fim com
  "De novo"/"Voltar ao lobby", botão Lobby, contagem do gelo, placar da sessão no lobby).
- **Tutorial do gancho:** `Workspace.Tutorial` (X -1500..-1100), 6 lições, entrada pela parede oeste do lobby,
  portal no fim. Montado e salvo no place; lição 1 e portal testados, lições 2–6 não.
- **Testes:** TestEZ 0.4.1 (Jest-Lua precisa de FFlag do Studio), 90 casos em `tests/`; ainda não rodados.
- **Bloqueio:** o plugin do Rojo no Studio está desconectado (o `rojo serve` travou e foi reiniciado). Ao voltar:
  reconectar, rodar `require(game.ServerStorage.Tests.Runner)()` e o playtest de zonas, corrida e tutorial.
- **Revisão da Fase 3 (2026-11-17):** feita só lendo o código. Corrigido: a chegada exige o checkpoint
  anterior e personagem vivo e é conferida a cada frame; "De novo" só vale em corrida; checkpoint não conta no
  intervalo do "De novo"; o contador do gelo some ao morrer; o painel de fim só some quando o servidor aceita;
  quem sai some do placar. Novos testes de `Zones.pickEffect`/`isFrozen`. Ficou para o playtest: a caixa do
  corpo no ZoneService é fixa para o avatar padrão (avatares maiores podem não tocar gelo/laranja). Q43 nova
  (KillZone aceita o gancho?).
- **Mapa da Fase 2 (greybox montado, sem playtest):** dono aprovou o [estudo](../04-game-design/estudos/mapa-fase2.md)
  (ADR 0050). `tools/map_layout.py` v3 importa `tools/map_sketch_fase2.py` e soma os ajustes do greybox (portas
  abertas, gelo tirado de pontos de parada, saltos de embalo do E7 com alvo ~12 mais alto); `tools/map2d.py` gera
  `maps/map01` (525 peças, caixa 1.920 × 1.180). Montado no Studio no lugar do Map01 antigo; conferência por
  script ok (tags, Order 1–3, `Kill` sólida pelo ADR 0049, ar livre, sem encostar no lobby/tutorial). O rascunho
  SVG do estudo mostra o desenho de antes dos ajustes. Rota "corrente alta" no E3 com `RequiresHookLevel = 2`.
- **Tutorial:** lição 7 (salto de embalo) montada; sala vai até X -1608, portal novo em (-1592, 191). Testada por
  script com o código antigo do Studio: só passa soltando o gancho + pulo duplo.
- **Próximo passo:** com o Rojo conectado, rodar os testes e jogar o mapa novo inteiro (pousos, mira, embalo,
  tempo real da corrida). A/D no embalo fica como está (ADR 0051).

## Revisão para o 2.5D (2026-11-16)

- Removidos os arquivos do experimento de câmera anterior (mapa, gerador e conferidor de saltos) e
  `Config.Camera.Mode`; ficam no histórico do Git (commit `b3779b4`).
- Documentos limpos; ADR 0038 registra a decisão. Q33 a Q39 respondidas (ADR 0039); Q40 respondida (ADR 0040).

Pendente por causa da revisão:
- `place/RaceAndEscape.rbxl` ainda tem o mapa do experimento em `Workspace.Maps.Map01`: refazer a
  partir de `maps/map01/build.luau` no Studio (o conferidor de saltos por cálculo foi removido; se
  fizer falta, reescrever para o `layout.json` 2.5D).
- `maps/map01` foi gerado antes dos ADRs 0029 a 0037: não segue os 6 estágios, não tem checkpoints
  com tag/atributo `Order` (o `CheckpointService` precisa deles) nem trechos de gancho.
- GAME_DESIGN v0.4, REQUIREMENTS, IMPLEMENTATION_PLAN e ARCHITECTURE (roadmap M1–M7) atualizados
  com os ADRs 0029 a 0040. A estrutura do mapa não foi tocada: o dono vai reformulá-la (Q31).
- Não começado: gancho, gelo, Bouncer, lâmina, timer, lobby com portal, atributos/rebirth, tema.
- Prefabs do Bouncer e da lâmina em `ServerStorage.Prefabs.Tools`; estudo em
  `memory-palace/04-game-design/estudos/ferramentas-bouncer-lamina.md`.
- Medido em jogo: pulo padrão ~8,8 studs no mesmo nível (JumpHeight 7,2, WalkSpeed 16).

## Verificação do M0

- `wally install`, `rojo build`, `selene src` (0 erros), `stylua --check src`: OK.
- Playtest pelo MCP: Output mostrou `[Server] Iniciado` e `[Client] Iniciado`.

## Diário de bordo

| Data | Agente | Resumo |
|---|---|---|
| 2026-11-11 | Claude Code | Toolchain (Rokit, Rojo, Wally, Selene, StyLua), docs iniciais, esqueleto M0 |
| 2026-11-12 | Claude Code | MCP do Studio conectado; M0 verificado em playtest |
| 2026-11-12 | Claude Code | Criado o palácio da memória (AGENTS.md, STATUS, decisions, OPEN_QUESTIONS, GLOSSARY) |
| 2026-11-12 | Claude Code | Decisões 0008–0010 (nome, PC, MVP 2 mapas labirinto); dois protótipos de câmera testados em playtest |
| 2026-11-12 | Claude Code | Decisões 0011 (câmera 2.5D) e 0012 (várias rotas); nova dúvida Q10 (gancho sobre paredes) |
| 2026-11-12 | Claude Code | Design v0.2: ADRs 0013–0020 (sem Bond, gelo mata, cores, gancho, Bouncer, progresso por jogador, lâmina, mesmo mapa); GDD e arquitetura revisados |
| 2026-11-12 | Claude Code | Design v0.3: ADRs 0021–0025 (cores finais, MVP 1 mapa, solo primeiro, detalhes das ferramentas, monetização com vantagens) |
| 2026-11-12 | Claude Code | ADRs 0026–0028 (deuses romanos, sem pulo duplo, ranking separa boost) |
| 2026-11-12 | Claude Code | Requisitos do MVP (RF/RNF) e plano de implementação em 4 fases |
| 2026-11-12 | Claude Code | Fase 1 parcial: câmera 2.5D, trava no plano, mapa 01 greybox (layout.json + mapgen) |
| 2026-11-15 | Claude Code | Estudo de referências de mapa (padrões + jogos lineares do Roblox) em memory-palace/04-game-design/estudos/referencias-mapas.md |
| 2026-11-15 | Claude Code | ADRs 0029 (6 estágios, ordem fixa, atalhos) e 0030 (progressão de atributo); análise de câmera (Q25) |
| 2026-11-15 | Claude Code | Experimento de câmera (ADR 0031) e mapa em 6 estágios gerado por script. ADR 0032 (rebirth) como proposta |
| 2026-11-15 | Claude Code (fork) | Palácio da memória reorganizado: docs/ e images/ movidos para memory-palace/ (salas 01–07), links corrigidos (71 ok), imagens de terceiros fora do Git |
| 2026-11-15 | Claude Code | Estágios revisados, CheckpointService mínimo, conferidor de saltos. Montado no Studio. Q27–Q30 |
| 2026-11-15 | Claude Code | Playtest do mapa do experimento pelo MCP (6 estágios, corrida de 52 s, checkpoints e renascimento); place salvo |
| 2026-11-15 | Claude Code | Dono reprovou o greybox (curto, estreito, fácil). ADRs 0033 (gancho no centro), 0034 (checkpoint a cada 3 estágios), 0035 (refazer o mapa) |
| 2026-11-16 | Claude Code | Estudo do gancho (peças, física, mira, rede, evolução, ordem) em 04-game-design/estudos/gancho-o-que-precisa.md; Q32 |
| 2026-11-16 | Claude Code | Dono respondeu o estudo do gancho: ADR 0036 (balanço B, RopeConstraint, esfera, recolher corda) e 0037 (em jogador: caminho A, C plano B). Log do dia em 01-status/diario/2026-11-16.md. Sem código |
| 2026-11-16 | Claude Code | Equipe decidiu 2.5D (ADR 0038). Removidos mapa, gerador e conferidor do experimento e `Config.Camera.Mode`; docs limpos; ADRs 0031/0035 viram registros curtos; Q25 e Q29 resolvidas; Q33–Q40 novas. selene e stylua ok |
| 2026-11-16 | Claude Code | Dono respondeu Q33–Q39: ADR 0039 (colisão entre jogadores, gancho só no plano, esfera de 3 studs, W/S na corda, altura visível, estágios verticais, correção de Z no servidor) |
| 2026-11-16 | Claude Code | Q40 respondida: ADR 0040 (10–15 min por corrida, nível do gancho no MVP, nova ordem das fases). GAME_DESIGN v0.4, REQUIREMENTS (RF-04/05, 10b, 17–19, 74, 80–81), IMPLEMENTATION_PLAN (5 fases) e roadmap M1–M7 atualizados. Q41 nova |
| 2026-11-16 | Claude Code | Rascunhos do mapa 2.5D (v0 reta, v1 enrolado) em 04-game-design/estudos/mapa-2-5d/ via tools/map_sketch.py; ADR 0041 (mapa enrolado, tutorial do gancho no MVP, queda = checkpoint) |
| 2026-11-16 | Claude Code (2 subagentes) | Greybox do mapa v2 no Studio (tools/map_layout.py, tools/map2d.py, maps/map01) e protótipo do gancho solo em src/ (balanço com RopeConstraint, W/S, esfera de ajuda, roxo/verde, HookService, PlaneService). selene/stylua/rojo build ok. Falta playtest com o Rojo conectado. tools/mapgen.py ficou obsoleto |
| 2026-11-16 | Claude Code | Primeiro playtest real do gancho (Rojo conectado): balanço, W/S, roxo recusado e verde 1 vez funcionam; Z fica a menos de 0,03 do plano. Pendências: A/D no chão não move, spawn sai 3 studs do plano, faixas mortais ainda não matam (Fase 3) |
| 2026-11-16 | Claude Code + 2 subagentes | ADR 0042: gancho vira puxão direto (clique vai ao alvo, segurar fica preso, sem W/S, 58 studs/s). PullPhysics/HookPhysics novos, pose de voo procedural (HookPose, juntas AnimationConstraint), deslize no pouso, câmera 64, teto roxo E2, spawn no plano. Playtest integrado ok por script; falta o dono testar com mouse |
| 2026-11-16 | Claude Code | Docs alinhados ao ADR 0042: RF-01/11/17/18, GAME_DESIGN §3.3, IMPLEMENTATION_PLAN Fase 1, roadmap M1, ADR 0036 (substituída em parte) e 0039 (sem W/S), estudo do gancho e nota do tutorial no rascunho |
| 2026-11-16 | Claude Code | RF-16 em código: remote HookRope, HookService repassa prender/soltar aos outros (e manda as cordas presas a quem entra), RopeReplicaController desenha o Beam. selene/stylua ok. Não testado: o Rojo desconectou no Studio |
| 2026-11-16 | Dono | Teste com 2 clientes: corda dos outros (RF-16) funcionando |
| 2026-11-16 | Claude Code + 2 subagentes | ADR 0043 (pulo duplo, WalkSpeed 24; substitui 0027) e 0044 (lobby). MovementController + Logic/DoubleJump; LobbyService, Workspace.Lobby (maps/lobby/build.luau), E1_Spawn1 desligado, CheckpointService só em corrida. Teste integrado: nasce no lobby, anda até o portal e chega ao RaceStart. Q42 aberta. Place salvo |
| 2026-11-16 | Claude Code | Q42 respondida (sim): pulo duplo vale no embalo depois do gancho e encerra o embalo (HookController.isInMomentum/endMomentum, MovementController). Lint e build ok; não testado em jogo (Studio fechado) |
| 2026-11-17 | Claude Code | Q42 testada no Studio: pulo duplo no embalo funciona (vy 50, 3º pulo negado, negado com a corda presa). Ajuste: o pulo não encerra mais o embalo, para não perder o X. Lint ok |
| 2026-11-17 | Claude Code + 4 subagentes | Q19/Q30/Q31/Q41 respondidas (ADR 0045–0048), Q22/24/26 adiadas, Q23 com direção. PR #2 aberto. Fase 3: ZoneService/FreezeController, RaceService/UIController; tutorial do gancho montado e salvo; TestEZ com 83 casos. Lint e rojo build ok; playtest pendente (Rojo desconectado, dono fora) |
| 2026-11-17 | Claude Code | Docs organizados para quem chega: LINHA_DO_TEMPO.md (dia a dia, com links), diários reconstruídos de 11-11, 11-12 e 11-15 a partir deste Diário de bordo e do Git; AGENTS.md e README do palácio apontam para ela. Nenhum texto antigo alterado; 226 links ok |
| 2026-11-17 | Claude Code | README da raiz reescrito para o estado atual (nome, 2.5D, gancho de puxão, servidor aberto, gelo que mata, lobby/tutorial, como rodar, pastas, links para a linha do tempo e o STATUS) |
| 2026-11-17 | Claude Code + 2 subagentes | Revisão da Fase 3 (8 correções em RaceService, CheckpointService, UIController; testes de pickEffect/isFrozen) e estudo + rascunho do mapa da Fase 2 (9 estágios, 22 rotas; tools/map_sketch_fase2.py). Q43–Q55 novas. selene/stylua/rojo build ok; nada testado em jogo |
| 2026-11-17 | Claude Code + 2 subagentes | Dono respondeu Q43–Q55 (ADR 0049 KillZone grudável e sólida; 0050 mapa da Fase 2 aprovado, substitui o Map01). Greybox do mapa novo montado no Studio (525 peças, conferência ok) e lição 7 do tutorial (salto de embalo, testada por script). Q56 nova (A/D no embalo). Place salvo; sem playtest do mapa |
| 2026-11-21 | Claude Code + 4 subagentes | FFmpeg 9.1 em D:\Ferramentas\ffmpeg; 214.900 frames do vídeo de 2026-11-14 (+1 fps e folhas de contato) em referencias/imagens/video-2026-11-14 (fora do Git); estudo de padrões para o mapa em 04-game-design/estudos/referencia-video-2026-11-14.md |
