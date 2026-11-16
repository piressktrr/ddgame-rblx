# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos

- **Marco atual:** M0 ✅. Jogo em **2.5D** (ADR 0038). Próximo passo: **Fase 1, gancho solo** (ADR 0036 e
  0039; plano em IMPLEMENTATION_PLAN) ou a reformulação do mapa pelo dono (Q31).
- **Branch atual:** `feature/implement-the-map` (último commit `b3779b4`; push não feito).
- **Código existente:** Loader, Config, Types; `CameraController` e `CharacterController` (2.5D, sempre
  ativos); `CheckpointService` (mínimo) e `Logic/Zones`.
- **Mapa:** greybox do rascunho v2 montado em `Workspace.Maps.Map01` (166 peças, Farol 1 = checkpoint 1,
  Farol 2 = fim) e salvo no place. Fonte: `tools/map_layout.py` → `tools/map2d.py` → `maps/map01/`.
  Ver `maps/README.md`. Ainda não jogado.
- **Gancho (Fase 1, protótipo):** `HookController` (+ SwingPhysics, AirBody, Reticle), `HookService`,
  `PlaneService`, `Net`, `Logic/Aim`, `Logic/HookRules`, `Util/HookSurface`. Lógica e física testadas em
  memória pelo MCP; **o código real não rodou em playtest porque o Studio não estava conectado ao Rojo**.
  Pista de teste `Workspace.Maps.TestHook` (X -704 a -400).

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
