# Arquitetura técnica (v0.2)

## 1. Toolchain

| Ferramenta | Para quê |
|---|---|
| **Rokit** | Gerencia as versões das ferramentas abaixo (substituto do Aftman/Foreman). |
| **Rojo** | Sincroniza `src/` com o Studio; o código vive no Git, não no `.rbxl`. |
| **Wally** | Gerenciador de pacotes Luau. |
| **luau-lsp** (extensão do VS Code) | Autocomplete, tipos, definições da API do Roblox. |
| **Selene** | Linter. |
| **StyLua** | Formatter (roda no CI e ao salvar). |
| **Jest-Lua** | Testes unitários da lógica pura (substitui o TestEZ). |
| **Git + GitHub** | Versionamento; CI com lint, format e testes em cada PR. |

**Regra:** mapas e assets 3D ficam no place (Studio). **Código fica 100% em `src/`.**
Nenhum `Script` escrito à mão dentro do Studio.

## 2. Estrutura de pastas

```
src/
  shared/                  -> ReplicatedStorage.Shared
    Config/                  constantes de gameplay (alcance do gancho, tempos de gelo...)
    Types.luau               tipos exportados (RaceState...)
    Net/                     definição única de todos os remotes
    Logic/                   lógica PURA e testável (física do gancho, regras de timer,
                             InteractionPolicy: "A pode afetar B?" — hoje sempre sim, ADR 0013)
  server/                  -> ServerScriptService.Server
    init.server.luau         bootstrap: carrega e inicia os Services
    Services/
      PlayerDataService      persistência (ProfileStore)
      RaceService            timer e checkpoint POR JOGADOR, morte/respawn, conclusão
      ZoneService            gelo (15 s → morte), descongelar, zona mortal, via tags
      HookService            uso do verde (HookOnce) por jogador; retransmite gancho em jogador
      InteractionService     empurrões da lâmina e do Bouncer em outros jogadores
      BouncerService         coleta, munição e recarga do Bouncer (autoridade)
      LeaderboardService     OrderedDataStore + cache
  client/                  -> StarterPlayer.StarterPlayerScripts.Client
    init.client.luau         bootstrap dos Controllers
    Controllers/
      InputController        teclado/gamepad/touch -> ações abstratas
      HookController         simulação local do gancho (segurar = preso)
      BouncerController      mira e impulso local do Bouncer
      BladeController        golpe corpo a corpo
      CharacterController    plano 2.5D (trava Z), estado de congelado, travas
      CameraController       câmera lateral 2.5D (ADR 0011)
      SoloObjectsController  objetos mágicos renderizados só para o jogador solo
      UIController           HUD, timer, menus
  ui/                      componentes de UI
tests/
```

## 3. Princípios de arquitetura

1. **Servidor é autoridade de estado; cliente é autoridade de *sensação*.**
   No Roblox o personagem tem *network ownership* do próprio cliente: movimento e gancho são
   simulados localmente (senão fica com lag). O servidor guarda o estado que importa
   (congelado, checkpoint, timer, munição, uso do verde) e **valida** o que o cliente reporta.
2. **Gancho em outro jogador passa pelo servidor.** Um cliente não pode aplicar força no
   personagem de outro cliente. Fluxo: A dispara → servidor valida (`InteractionPolicy`, alcance, linha
   de visão) → servidor manda para o cliente de B aplicar o puxão em si mesmo. Isso precisa ser
   testado cedo, porque a latência afeta direto o *game feel*.
3. **Zonas por tags, não por scripts no mapa.** Level designers só marcam partes com tags
   (`FreezeZone`, `NoHook`, `HookOnce`, `Checkpoint`...) via CollectionService. Um único `ZoneService` trata todas.
   Prefira consultas espaciais (`GetPartBoundsInBox`, `GetPartsInPart`) com `OverlapParams`
   em vez de `.Touched`, que é inconsistente com personagens rápidos.
4. **Lógica pura separada de efeitos.** Cálculos (trajetória do gancho, regras de timer,
   validação) ficam em módulos sem acesso a `game`, assim são testáveis com Jest-Lua.
5. **Anti-cheat por validação, não por confiança:** checkpoints só valem na ordem; tempo mínimo
   por seção; checagem de velocidade/teleporte; todo remote valida tipos e faz rate limit.
6. **Sem framework pesado.** Um loader simples de Services/Controllers (`Init` → `Start`) é
   suficiente e fácil de entender. Evitamos Knit (sem manutenção ativa).
7. **Ciclo de vida explícito:** toda conexão criada é limpa (Trove). Nada de vazamento ao
   resetar o personagem ou sair da equipe.

## 4. Padrões de Luau

- `--!strict` em todos os arquivos; tipos exportados em `Types.luau`.
- `task.wait/task.spawn/task.defer` (nunca `wait`, `spawn`, `delay`).
- `game:GetService(...)` no topo do módulo; nunca `game.Workspace` direto.
- Sem variáveis globais; cada módulo retorna uma tabela ou um tipo.
- Constantes em `Config`, nunca números mágicos espalhados.
- Atributos (`SetAttribute`) para estado replicado simples (ex.: `Frozen`), remotes para eventos.
- Nomes: `PascalCase` para módulos/tipos, `camelCase` para variáveis/funções locais.

## 5. Bibliotecas (via Wally)

| Pacote | Uso |
|---|---|
| ProfileStore (loleris) | Dados do jogador com session locking |
| Trove (sleitnick) | Limpeza de conexões/instâncias |
| Signal (sleitnick) | Eventos internos tipados |
| Promise (evaera) | Fluxos assíncronos (DataStore, teleporte) |
| Blink ou ByteNet | Rede tipada e compacta (gancho envia muitos pacotes) |
| React-lua (jsdotlua) ou Fusion | UI declarativa |
| Jest-Lua (jsdotlua) | Testes |

As versões exatas são fixadas no `wally.toml` quando fizermos o scaffold.

## 6. Roadmap técnico

| Marco | Entrega | Critério de pronto |
|---|---|---|
| M0 | Toolchain + scaffold | ✅ `rojo serve` sincroniza; lint/format passam |
| M1 | Movimento solo: câmera 2.5D + gancho | Balançar e se puxar é gostoso no PC; `NoHook`/`HookOnce` funcionam |
| M2 | Zonas + checkpoints + timer + Bouncer | Greybox jogável do início ao fim sozinho, com gelo/morte/respawn |
| M3 | Interação entre jogadores | Gancho em jogador puxa os dois, lâmina e Bouncer empurram, resgate do gelo com ping de 150 ms |
| M4 | Objetos mágicos solo + mapa(s) do MVP | Playtest sozinho e em grupo, tempos medidos |
| M5 | Dados + rankings | Recordes persistem |
| M6 | Polimento + lançamento | Retenção D1 medida no Analytics |

## 7. Checagem de viabilidade (v0.2, 2026-11-12)

As decisões 0013–0020 cabem na arquitetura sem mudar os princípios:

- **Sem Bond** simplifica: some o `TeamService`. O único cuidado é concentrar a regra em
  `InteractionPolicy` para religar proteção depois.
- **Gancho gruda em tudo** simplifica: raycast no plano 2.5D e só exclui `NoHook`. `HookOnce` precisa
  de um conjunto "já usado" por jogador, guardado no servidor e espelhado no cliente.
- **Gelo 15 s → morte**: atributo `FrozenUntil` no personagem (servidor); o cliente só mostra.
- **Bouncer**: impulso no próprio personagem é local (sem lag); empurrão em outros passa pelo
  servidor, como o gancho em jogador. Munição é autoridade do servidor.
- **Maior risco técnico:** puxar/empurrar **outro** jogador com boa sensação, porque depende da
  latência. Por isso o M3 tem critério com ping de 150 ms e deve ser prototipado cedo.
- **Plano 2.5D:** cada cliente trava o Z do próprio personagem; o servidor corrige se alguém sair do plano.
