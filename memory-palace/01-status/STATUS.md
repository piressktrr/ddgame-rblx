# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos

- **Marco atual:** M0 ✅. Em andamento: **experimento 3D** (ADR 0031, falta o aval do outro membro
  da equipe) com o mapa em 6 estágios (ADR 0029).
- **Branch atual:** `main`, com tudo **sem commit** (o dono reescreveu o histórico e criou o remoto
  `origin`). Regra: não commitar na `main`; antes de commitar, combinar a branch com o dono.
- **Código existente:** Loader, Config, Types; `CameraController` e `CharacterController` (só agem
  com `Config.Camera.Mode = "SideView"`; hoje está `"ThirdPerson"`); `CheckpointService` (mínimo) e
  `Logic/Zones`.

## Em andamento: mapa 3D em estágios

Feito (não commitado):
- `tools/stages3d.py` gera `maps/map01-3d/` (`layout.json`, `build.luau`, `map01-3d.svg`): lobby +
  6 estágios de 96 studs (Aquecimento, Zigue-zague, Rampas, Serpentina, Labirinto, Torre final),
  cada um com um atalho azul. Só blocos do template padrão, sem tema.
- `tools/check_map.py` confere por cálculo cada salto das rotas (vão x subida contra o pulo padrão):
  **0 problemas** em 2026-11-15. É conta, não playtest.
- `CheckpointService` (RF-26): peça com tag `Checkpoint` + atributo `Order`; só vale o próximo da
  ordem; ao renascer o jogador volta para o último; `Players.RespawnTime = 1`. Há um checkpoint no
  fim dos estágios 1 a 5 e a tag `RaceFinish` no fim do 6.
- O mapa foi montado em `Workspace.Maps.Map01` pelo MCP (85 instâncias, 5 checkpoints com tag) e o
  playtest começou (câmera padrão ativa, personagem nasce no lobby).

Verificado em playtest pelo MCP (2026-11-15, robô de teste no cliente: anda pelos pontos da rota,
pula ao ver vão ou degrau e mira o meio da próxima peça no ar):
- Rota principal e atalho de **cada um dos 6 estágios**: todos concluídos sem cair.
- **Corrida completa** do lobby ao fim pela rota principal: 52 s, sem cair.
- Checkpoints 1 a 5 registrados em ordem (Output do servidor); ao cair no vazio no fim do mapa o
  jogador renasceu em cima do checkpoint 5, olhando para +X, 2,5 s depois.
- Tempos (principal / atalho): E1 5,4 / 5,9 s · E2 11,3 / 6,3 s · E3 6,0 s · E4 6,4 / 5,6 s ·
  E5 8,6 / 6,6 s · E6 10,3 s (atalho pula os 3 últimos degraus e o pilar).
- Pulo medido em jogo: ~8,8 studs no mesmo nível.
- Place salvo com o mapa 3D.

Achados do teste (para decidir com o dono):
- O mapa inteiro leva **menos de 1 minuto**. A meta era 10 a 15 min e checkpoint a cada ~3 min (Q27).
- Atalho do E2 (pinos): quem só segura "frente + pulo" cai no 3º salto (pousa na beirada); passa
  quem controla o personagem no ar. É o atalho mais arriscado do mapa.
- Atalho do E1 (viga) não é mais rápido que a rota principal; só evita os pulos.
- Não testado: jogador humano, 2 jogadores ao mesmo tempo, latência.

Pendente:
- Documentos ainda em 2.5D (não reescritos porque o 3D é experimento): REQUIREMENTS RF-01..03 e
  RF-10, IMPLEMENTATION_PLAN Fase 1, GAME_DESIGN §5.2.
- Dúvidas novas: Q27 a Q30 em `03-duvidas/OPEN_QUESTIONS.md`.
- Não começado: gancho, gelo, Bouncer, lâmina, timer, lobby com portal, atributo/rebirth, tema.
- O mapa 2.5D (`maps/map01`, `tools/mapgen.py`) continua no projeto, sem uso no modo 3D.
- Prefabs do Bouncer e da lâmina em `ServerStorage.Prefabs.Tools` (sessão paralela); estudo em
  `memory-palace/04-game-design/estudos/ferramentas-bouncer-lamina.md`.

## Verificação do M0

- `wally install`, `rojo build`, `selene src` (0 erros), `stylua --check src`: OK.
- Playtest pelo MCP: Output mostrou `[Server] Iniciado` e `[Client] Iniciado`.

## Diário de bordo

| Data | Agente | Resumo |
|---|---|---|
| 2026-11-11 | Claude Code | Toolchain (Rokit, Rojo, Wally, Selene, StyLua), docs iniciais, esqueleto M0 |
| 2026-11-12 | Claude Code | MCP do Studio conectado; M0 verificado em playtest |
| 2026-11-12 | Claude Code | Criado o palácio da memória (AGENTS.md, STATUS, decisions, OPEN_QUESTIONS, GLOSSARY) |
| 2026-11-12 | Claude Code | Decisões 0008–0010 (nome, PC, MVP 2 mapas labirinto); protótipo de câmera 3ª pessoa/2.5D testado em playtest |
| 2026-11-12 | Claude Code | Decisões 0011 (câmera 2.5D) e 0012 (várias rotas); nova dúvida Q10 (gancho sobre paredes) |
| 2026-11-12 | Claude Code | Design v0.2: ADRs 0013–0020 (sem Bond, gelo mata, cores, gancho, Bouncer, progresso por jogador, lâmina, mesmo mapa); GDD e arquitetura revisados |
| 2026-11-12 | Claude Code | Design v0.3: ADRs 0021–0025 (cores finais, MVP 1 mapa, solo primeiro, detalhes das ferramentas, monetização com vantagens) |
| 2026-11-12 | Claude Code | ADRs 0026–0028 (deuses romanos, sem pulo duplo, ranking separa boost) |
| 2026-11-12 | Claude Code | Requisitos do MVP (RF/RNF) e plano de implementação em 4 fases |
| 2026-11-12 | Claude Code | Fase 1 parcial: câmera 2.5D, trava no plano, mapa 01 greybox (layout.json + mapgen) |
| 2026-11-15 | Claude Code | Estudo de referências de mapa (padrões + jogos lineares do Roblox) em memory-palace/04-game-design/estudos/referencias-mapas.md |
| 2026-11-15 | Claude Code | ADRs 0029 (6 estágios, ordem fixa, atalhos) e 0030 (progressão de atributo); análise câmera 2.5D x 3D (Q25) |
| 2026-11-15 | Claude Code | Experimento 3D (ADR 0031): câmera padrão via Config.Camera.Mode; mapa 3D de 6 estágios gerado (tools/stages3d.py → maps/map01-3d). Não montado no Studio: Studio fechado. ADR 0032 (rebirth) como proposta |
| 2026-11-15 | Claude Code (fork) | Palácio da memória reorganizado: docs/ e images/ movidos para memory-palace/ (salas 01–07), links corrigidos (71 ok), imagens de terceiros fora do Git |
| 2026-11-15 | Claude Code | Mapa 3D: estágios revisados (zigue-zague, atalhos), CheckpointService mínimo, tools/check_map.py (0 problemas). Montado no Studio; playtest interrompido porque o Studio fechou. Q27–Q30 |
| 2026-11-15 | Claude Code | Playtest do mapa 3D pelo MCP: 6 estágios + atalhos e corrida completa (52 s) concluídos; checkpoints e renascimento verificados; place salvo |
| 2026-11-15 | Claude Code | Dono reprovou o greybox 3D (curto, estreito, fácil). ADRs 0033 (gancho no centro), 0034 (checkpoint a cada 3 estágios), 0035 (refazer mapa, 3D continua). Próximo: gancho e mapa novo, numa branch que o dono vai criar |
