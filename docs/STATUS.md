# Quadro de status

> Atualize este arquivo ao fim de toda sessão de trabalho (qualquer agente).

## Onde estamos

- **Marco atual:** M0 (fundação) ✅ concluído e verificado em 2026-11-12.
- **Fase atual:** fechar decisões de design/arquitetura antes de escrever gameplay.
- **Código existente:** só o esqueleto (Loader, Config, Types, scripts de entrada). Pastas
  `src/server/Services` e `src/client/Controllers` vazias.

## Próximo passo

1. Câmera decidida: 2.5D (ADR 0011). No M1, `CameraPrototypeController.luau` vira `CameraController`
   definitivo, sem o modo 3ª pessoa. Pista de teste `Workspace.CameraTestCourse` (place não salvo).
2. Resolver as demais dúvidas de [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) com o dono.
3. Registrar cada resposta como decisão em [`decisions/`](decisions/README.md).
4. Escrever requisitos detalhados do M1 (gancho solo) antes de codar.

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
