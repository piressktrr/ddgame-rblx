# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos

- **Marco atual:** M0 ✅. Design v0.3 fechado (ADRs até 0025). Próximo: **M1**.
- **Branch atual:** `design/refinamento-ideias`.
- **Código existente:** esqueleto (Loader, Config, Types) + `CameraPrototypeController` (3ª pessoa/2.5D).

## Em andamento: Fase 1 — `feat/m1-movimento`

Feito (não commitado, aguardando o dono):
- `CameraController` (2.5D definitivo) e `CharacterController` (trava no plano Z, W/S desligados).
  O protótipo de câmera foi removido. `Config` atualizado (Camera, Plane, tags novas, gelo 15 s).
- Mapa 01 greybox: `maps/map01/layout.json` → `tools/mapgen.py` → `map01.svg` + `build.luau`.
  Montado em `Workspace.Maps.Map01` e salvo em `place/RaceAndEscape.rbxl` (o dono salvou como
  `.rbxl` binário, não `.rbxlx`).
- Baseplate e pista de teste antiga removidos do place.

Pendente:
- **Playtest manual do mapa** pelo dono. Verificado pelo MCP: câmera 2.5D ativa (Scriptable, a 46
  studs no eixo Z), personagem nasce no início. O teste automático de cada pulo não foi conclusivo
  (scripts do MCP rodam lentos e brigam com o controle do jogador); as medidas seguem as regras de
  `maps/README.md` (vão <= 5, subida <= 4), que são mais fáceis que pulos que passaram no 1º teste.
- Rojo travou uma vez ("cannot destroy the root instance of a WeakDom") e foi reiniciado.
- Gancho (RF-10..14) ainda não implementado. Checkpoint e fim são só marcadores visuais.
- Sessão paralela criou prefabs do Bouncer e da lâmina em `ServerStorage.Prefabs.Tools` e
  `docs/design/ferramentas-bouncer-lamina.md`.

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
