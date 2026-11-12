# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos

- **Marco atual:** M0 ✅. Design v0.3 fechado (ADRs até 0025). Próximo: **M1**.
- **Branch atual:** `design/refinamento-ideias`.
- **Código existente:** esqueleto (Loader, Config, Types) + `CameraPrototypeController` (3ª pessoa/2.5D).

## Próximo passo: M1 — movimento solo (câmera 2.5D + gancho)

Criar a branch `feat/m1-movimento` a partir da `main` (depois do merge desta branch, se o dono aprovar).

Requisitos do M1:
1. `CameraController` definitivo, só 2.5D (vem do protótipo).
2. `CharacterController`: trava o personagem no plano Z.
3. `HookController`: mira com o mouse no plano; segurar botão = preso, soltar = solta; gruda em
   tudo menos `NoHook`; `HookOnce` uma vez por jogador; alcance/força em `Config.Hook`.
4. `HookService`: guarda o uso do `HookOnce` por jogador.
5. `Config.Tags`: trocar `Hookable` por `NoHook` e `HookOnce`.
6. Pista de teste greybox com superfícies comum, `NoHook` e `HookOnce`.
7. Verde volta ao morrer/passar checkpoint (ADR 0024); vermelho é grudável (ADR 0021).
8. Sem pulo duplo (ADR 0027).

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
