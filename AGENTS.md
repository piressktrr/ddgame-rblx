# AGENTS.md — porta de entrada para qualquer IA

Este arquivo é a **entrada do palácio da memória** do projeto. Qualquer agente (Claude Code,
Codex, Antigravity/Gemini, Cursor etc.) deve ler este arquivo **antes de qualquer ação**.

## 1. Ordem de leitura (os "cômodos" do palácio)

| # | Cômodo | Arquivo | Quando ler |
|---|---|---|---|
| 1 | Hall de entrada | `AGENTS.md` (este) | Sempre, primeiro |
| 2 | Quadro de status | [`docs/STATUS.md`](docs/STATUS.md) | Sempre: diz onde paramos e o próximo passo |
| 3 | Sala das decisões | [`docs/decisions/`](docs/decisions/README.md) | Antes de mudar algo estrutural |
| 4 | Sala das dúvidas | [`docs/OPEN_QUESTIONS.md`](docs/OPEN_QUESTIONS.md) | Antes de assumir algo não decidido |
| 5 | Biblioteca de design | [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) | Ao mexer em mecânica ou mapa |
| 6 | Oficina técnica | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Ao escrever código |
| 7 | Dicionário | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) | Quando um termo não for claro |
| 8 | Almoxarifado | [`docs/TOOLS.md`](docs/TOOLS.md), [`docs/UNINSTALL.md`](docs/UNINSTALL.md) | Ao instalar/remover ferramenta ou biblioteca |
| 9 | Vitrine pública | [`README.md`](README.md) | Visão simples para pessoas comuns |

## 2. Regras invioláveis

1. **Jogo original.** Gênero de corrida cooperativa (como DDRace), mas nenhum nome, arte, mapa ou
   som copiado de jogos existentes.
2. **Nunca fazer commit ou push** sem o dono pedir explicitamente.
3. **Código só em arquivos `src/`**, sincronizados pelo Rojo. Nunca editar scripts dentro do
   Studio (nem via MCP): o Rojo sobrescreve.
4. **MCP do Roblox Studio** serve só para mapas, testes (playtest) e inspeção.
5. **Sem screenshots** a menos que o dono peça. Reporte em texto (linhas do Output).
6. **Não decida o que está em `docs/OPEN_QUESTIONS.md`.** Proponha, mas pergunte ao dono.
7. Toda ferramenta/biblioteca nova → atualizar `docs/TOOLS.md` **e** `docs/UNINSTALL.md`.
8. Luau com `--!strict` em todo arquivo. Rodar `selene src` e `stylua --check src` antes de
   declarar algo pronto.
9. Documentação e conversa com o dono em **português (BR)**; identificadores de código em inglês.

## 3. Protocolo de trabalho (toda sessão)

1. Leia `docs/STATUS.md` → pegue o "Próximo passo".
2. Se a tarefa contrariar uma decisão em `docs/decisions/`, **pare e pergunte**.
3. Faça o trabalho em passos pequenos e verificáveis.
4. Ao terminar (ou ao parar no meio), **atualize `docs/STATUS.md`**:
   - o que mudou, o que foi verificado e como, o que ficou pendente;
   - adicione uma linha no "Diário de bordo" com data, agente e resumo.
5. Decisão nova tomada com o dono → novo arquivo em `docs/decisions/` (próximo número).
6. Dúvida nova → entra em `docs/OPEN_QUESTIONS.md`.

## 4. Git e branches

- `main`: só recebe trabalho revisado e aprovado pelo dono (merge). Nunca commitar direto nela.
- Branches de trabalho saem da `main`, com prefixo pelo tipo:
  - `design/…`: refinamento de ideias e documentação (atual: `design/refinamento-ideias`);
  - `feat/…`: nova funcionalidade (ex.: `feat/m1-gancho-solo`);
  - `fix/…`: correção; `chore/…`: ferramentas e configs.
- Mensagens de commit em português, no formato `tipo: resumo` (ex.: `docs: registra decisão 0011`).
- Commit só quando o dono pedir. Push e merge também só com o dono mandando.

## 5. Ambiente

- Windows 11, projeto em `D:\Projetos\dddrace-roblox`. Repositório Git local (sem remoto ainda).
- Ferramentas via Rokit (`rokit.toml`): Rojo 7.7.1, Wally 0.3.2, Selene 0.32.0, StyLua 2.6.0.
- Comandos: `wally install`, `rojo serve`, `rojo build -o build/jogo.rbxl`, `selene src`, `stylua src`.
- Mapa de pastas: `src/shared` → ReplicatedStorage.Shared · `src/server` → ServerScriptService.Server ·
  `src/client` → StarterPlayerScripts.Client · `Packages` → ReplicatedStorage.Packages.
