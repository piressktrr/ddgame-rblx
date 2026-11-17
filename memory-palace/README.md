# Palácio da memória — Race and Escape

Tudo o que foi decidido, estudado e planejado sobre o jogo fica aqui, em salas numeradas. A ordem dos
números é a ordem de leitura sugerida. Regras gerais e protocolo de trabalho: [`../AGENTS.md`](../AGENTS.md).

| Sala | Conteúdo | Quando ler |
|---|---|---|
| [01-status](01-status/STATUS.md) | Onde paramos, próximo passo, diário de bordo | **Sempre**, no início e no fim de cada sessão |
| ↳ [diario/](01-status/diario/) | Um log por dia de trabalho (`AAAA-MM-DD.md`) | Para ver o que aconteceu num dia |
| [02-decisoes](02-decisoes/README.md) | Decisões numeradas (ADRs) e o índice delas | Antes de mudar algo estrutural |
| [03-duvidas](03-duvidas/OPEN_QUESTIONS.md) | O que ainda não foi decidido | Antes de assumir qualquer coisa |
| [04-game-design](04-game-design/GAME_DESIGN.md) | Documento de game design | Ao mexer em mecânica, mapa ou progressão |
| ↳ [estudos/](04-game-design/estudos/) | Análises e rascunhos: referências de mapa, Bouncer e lâmina, gancho | Quando o assunto da tarefa tiver um estudo |
| ↳ [referencias/](04-game-design/referencias/) | Material de apoio: paleta de cores, imagens de referência (só local) | Quando o estudo citar |
| [05-arquitetura](05-arquitetura/ARCHITECTURE.md) | Arquitetura técnica | Ao escrever código |
| ↳ [REQUIREMENTS](05-arquitetura/REQUIREMENTS.md) | Requisitos com IDs (RF/RNF) | Antes de implementar |
| ↳ [IMPLEMENTATION_PLAN](05-arquitetura/IMPLEMENTATION_PLAN.md) | Fases, branches e ordem da obra | Para saber o que vem agora |
| [06-glossario](06-glossario/GLOSSARY.md) | Significado dos termos do projeto | Quando um termo não for claro |
| [07-toolchain](07-toolchain/TOOLS.md) | Ferramentas e bibliotecas ([TOOLS](07-toolchain/TOOLS.md)) e como desinstalar ([UNINSTALL](07-toolchain/UNINSTALL.md)) | Ao instalar ou remover algo |

## Onde guardar cada coisa nova

| Tipo de conteúdo | Sala |
|---|---|
| Log detalhado do dia | `01-status/diario/AAAA-MM-DD.md` |
| Decisão tomada com o dono | `02-decisoes/NNNN-titulo.md` + linha no índice |
| Pergunta sem resposta | `03-duvidas/OPEN_QUESTIONS.md` |
| Regra de mecânica, mapa, progressão, monetização | `04-game-design/GAME_DESIGN.md` |
| Análise, comparação, pesquisa, rascunho de design | `04-game-design/estudos/` |
| Imagem, paleta, arquivo de apoio | `04-game-design/referencias/` |
| Estrutura de código, padrões, requisitos, fases | `05-arquitetura/` |
| Termo novo | `06-glossario/GLOSSARY.md` |
| Ferramenta, extensão, biblioteca | `07-toolchain/` |
| Progresso da sessão | `01-status/STATUS.md` (diário de bordo) |

Os dados dos mapas (layout, build) **não** ficam aqui: são conteúdo do jogo e vivem em `../maps/`.
