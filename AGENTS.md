# AGENTS.md — porta de entrada para qualquer IA

Qualquer agente (Claude Code, Codex, Antigravity/Gemini, Cursor etc.) deve ler este arquivo **antes de
qualquer ação**. Toda a memória do projeto (status, decisões, dúvidas, game design, arquitetura,
glossário, ferramentas) fica numa única pasta: **[`memory-palace/`](memory-palace/README.md)**.

## 1. Ordem de leitura

1. Este arquivo (regras).
2. [`memory-palace/README.md`](memory-palace/README.md): o mapa do palácio, sala por sala.
3. [`memory-palace/01-status/STATUS.md`](memory-palace/01-status/STATUS.md): onde paramos e o próximo passo.
4. As outras salas conforme a tarefa (o mapa diz quando ler cada uma).

## 2. Regras invioláveis

1. **Jogo original.** Gênero de corrida cooperativa (como DDRace), mas nenhum nome, arte, mapa ou
   som copiado de jogos existentes. Referências externas viram só padrões de design.
2. **Nunca fazer commit ou push** sem o dono pedir explicitamente.
3. **Código só em arquivos `src/`**, sincronizados pelo Rojo. Nunca editar scripts dentro do
   Studio (nem via MCP): o Rojo sobrescreve.
4. **MCP do Roblox Studio** serve só para mapas, testes (playtest) e inspeção.
5. **Sem screenshots** a menos que o dono peça. Reporte em texto (linhas do Output).
6. **Não decida o que está em `memory-palace/03-duvidas/`.** Proponha, mas pergunte ao dono.
7. Toda ferramenta/biblioteca nova → atualizar `memory-palace/07-toolchain/TOOLS.md` **e** `UNINSTALL.md`.
8. Luau com `--!strict` em todo arquivo. Rodar `selene src` e `stylua --check src` antes de
   declarar algo pronto.
9. Documentação e conversa com o dono em **português (BR)**; identificadores de código em inglês.
10. **Documento novo de memória vai para a sala certa de `memory-palace/`**, nunca solto na raiz ou
    em outra pasta. Se nenhuma sala servir, pergunte antes de criar uma.

## 3. Protocolo de trabalho (toda sessão)

1. Leia o STATUS → pegue o "Próximo passo".
2. Se a tarefa contrariar uma decisão em `memory-palace/02-decisoes/`, **pare e pergunte**.
3. Faça o trabalho em passos pequenos e verificáveis.
4. Ao terminar (ou ao parar no meio), **atualize o STATUS**:
   - o que mudou, o que foi verificado e como, o que ficou pendente;
   - adicione uma linha no "Diário de bordo" com data, agente e resumo.
5. Decisão nova tomada com o dono → novo arquivo em `memory-palace/02-decisoes/` (próximo número) e
   uma linha no índice dessa pasta.
6. Dúvida nova → entra em `memory-palace/03-duvidas/OPEN_QUESTIONS.md`.
7. Mais de uma sessão de IA no mesmo checkout: combine antes quem mexe em quais pastas.

## 4. Git e branches

- `main`: só recebe trabalho revisado e aprovado pelo dono (merge). Nunca commitar direto nela.
- Branches de trabalho saem da `main`, com prefixo pelo tipo:
  - `design/…`: refinamento de ideias e documentação;
  - `feat/…`: nova funcionalidade (ex.: `feat/m1-movimento`);
  - `fix/…`: correção; `chore/…`: ferramentas e configs.
- Mensagens de commit em português, no formato `tipo: resumo` (ex.: `docs: registra decisão 0011`).
- Commit só quando o dono pedir. Push e merge também só com o dono mandando.

## 5. Ambiente

- Windows 11, projeto em `D:\Projetos\dddrace-roblox`. Remoto no GitHub (`origin`).
- Ferramentas via Rokit (`rokit.toml`): Rojo 7.7.1, Wally 0.3.2, Selene 0.32.0, StyLua 2.6.0.
- Comandos: `wally install`, `rojo serve`, `rojo build -o build/jogo.rbxl`, `selene src`, `stylua src`.
- Mapa de pastas do código: `src/shared` → ReplicatedStorage.Shared · `src/server` →
  ServerScriptService.Server · `src/client` → StarterPlayerScripts.Client · `Packages` →
  ReplicatedStorage.Packages.
- Outras pastas: `maps/` (dados dos mapas, ver `maps/README.md`), `tools/` (scripts do projeto),
  `place/` (arquivo do place do Studio).
