# Race and Escape

> Jogo original para o Roblox (nome definido no [ADR 0008](memory-palace/02-decisoes/0008-nome-race-and-escape.md)).
> Gênero de corrida cooperativa, sem nada copiado de outros jogos. Foco no PC.

## Que jogo é esse?

Um jogo de plataforma em **2.5D** (visto de lado), passado num **mundo de fantasia**: ruínas flutuantes,
florestas mágicas, cavernas de cristal, torres de magos. O objetivo é simples de explicar: **sair do começo
do mapa e chegar ao fim** o mais rápido possível, passando por abismos, paredes e armadilhas.

O que deixa o jogo diferente de um obby comum é **como você se move**. O percurso é feito quase todo com um
**gancho mágico**: você mira com o mouse, **clica** e é puxado direto até o ponto. **Segurando** o botão, fica
preso lá. Dá para trocar de alvo no meio do voo e encadear um gancho no outro. Andar e o **pulo duplo** servem
para os ajustes finos e os pousos.

## Todo mundo no mesmo mapa

O servidor é aberto: **todos interagem com todos**. Dá para salvar alguém no último segundo ou atrapalhar de
brincadeira. Jogar junto ajuda, mas o mapa sempre dá para terminar **sozinho**: quem está só conta com
**objetos mágicos** (com nomes de deuses romanos) que fazem o papel do colega. Tempo, checkpoint e ranking são
sempre **pessoais**.

## Os perigos

- **Gelo mágico:** encostou, fica **congelado por 15 s**, sem andar nem usar o gancho. Se chegar a uma zona de
  **descongelar** (laranja-brasa), volta ao normal. Se o tempo acabar, **morre** e volta ao último checkpoint.
  Outro jogador pode te salvar.
- **Zona mortal** (vermelha): mata na hora.
- **Superfícies com regra:** **roxo** não prende o gancho; **verde** prende só uma vez (volta ao morrer ou ao
  passar de checkpoint).

## Como uma partida funciona

1. Você nasce no **lobby**. Ao lado dele fica a sala de **tutorial do gancho** (opcional).
2. Entrou no **portal**, começa a corrida e o **cronômetro** dispara.
3. O mapa tem **pelo menos 8 estágios**, dificuldade média e **vários caminhos** até o fim, com um checkpoint a
   cada 3 estágios. Uma corrida completa leva de 10 a 15 minutos.
4. Na chegada aparecem o seu tempo e o seu recorde, com as opções "De novo" e "Voltar ao lobby". O placar do
   lobby mostra o melhor tempo de cada jogador do servidor.

## Por que voltar a jogar?

- **Bater o próprio recorde.**
- **Evoluir o gancho:** o nível do gancho sobe jogando e **fica salvo** entre as sessões. Como ele evolui ainda
  está em aberto (direção atual: alcance e força).

---

## Em que pé está

O jogo está em desenvolvimento, no **MVP**. Hoje já existem, em greybox: o gancho de puxão, o pulo duplo, o
lobby, o mapa de teste (6 estágios), o tutorial e, ainda sem teste em jogo, as zonas (gelo e morte), o
cronômetro e as telas da corrida. Bouncer, lâmina, objetos mágicos e o nível do gancho vêm nas próximas fases.

- **Onde paramos agora:** [STATUS](memory-palace/01-status/STATUS.md)
- **Tudo o que foi feito, dia a dia, desde o início:** [linha do tempo](memory-palace/01-status/LINHA_DO_TEMPO.md)

## Para quem vai desenvolver

**Comece por [`AGENTS.md`](AGENTS.md)**, que vale para pessoas e para IAs: regras, ordem de leitura, Git e
ambiente. Depois leia a [linha do tempo](memory-palace/01-status/LINHA_DO_TEMPO.md) e o
[STATUS](memory-palace/01-status/STATUS.md).

Toda a documentação fica no [palácio da memória](memory-palace/README.md):

| Documento | Para quê |
|---|---|
| [Linha do tempo](memory-palace/01-status/LINHA_DO_TEMPO.md) | O que foi criado e decidido em cada dia, com links |
| [Decisões (ADRs)](memory-palace/02-decisoes/README.md) | Cada decisão numerada; o número é a ordem em que foram tomadas |
| [Dúvidas em aberto](memory-palace/03-duvidas/OPEN_QUESTIONS.md) | O que ainda não foi decidido (não decida sozinho) |
| [Game Design](memory-palace/04-game-design/GAME_DESIGN.md) | Mecânicas, regras, mapa, progressão |
| [Requisitos](memory-palace/05-arquitetura/REQUIREMENTS.md) e [plano](memory-palace/05-arquitetura/IMPLEMENTATION_PLAN.md) | O que o MVP precisa ter e em que ordem construir |
| [Arquitetura](memory-palace/05-arquitetura/ARCHITECTURE.md) | Estrutura do código e padrões de Luau |
| [Ferramentas](memory-palace/07-toolchain/TOOLS.md) e [desinstalação](memory-palace/07-toolchain/UNINSTALL.md) | Cada ferramenta, versão, para que serve e como remover |

### Como rodar

Ferramentas pelo [Rokit](https://github.com/rojo-rbx/rokit) (`rokit.toml`): Rojo, Wally, Selene, StyLua.

```bash
rokit install
```

```bash
wally install
```

```bash
rojo serve
```

Com o `rojo serve` rodando, abra `place/RaceAndEscape.rbxl` no Roblox Studio e conecte o plugin do Rojo.
Antes de dar algo por pronto:

```bash
selene src tests
```

```bash
stylua --check src tests
```

Os testes da lógica (TestEZ) rodam no Studio, em modo Edit: `require(game.ServerStorage.Tests.Runner)()`.

### Pastas

| Pasta | O que tem |
|---|---|
| `src/shared` | Config, rede (`Net`) e lógica pura (`Logic/`) → ReplicatedStorage.Shared |
| `src/server` | Serviços do servidor (gancho, lobby, checkpoints, zonas, corrida) → ServerScriptService.Server |
| `src/client` | Controllers do jogador (câmera, gancho, movimento, interface) → StarterPlayerScripts.Client |
| `tests/` | Testes TestEZ da lógica pura → ServerStorage.Tests |
| `maps/` | Dados dos mapas (map01, lobby, tutorial); ver [`maps/README.md`](maps/README.md) |
| `tools/` | Scripts Python que geram o mapa e os rascunhos |
| `place/` | O place do Studio |
| `memory-palace/` | Toda a documentação |

O código vive só em arquivos (o Rojo sincroniza). Nunca edite scripts dentro do Studio. Branches e commits
seguem o [`AGENTS.md`](AGENTS.md) §4: nada vai direto para a `main`.
