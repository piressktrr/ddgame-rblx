# Arquitetura técnica (rascunho v0.1)

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
    Types.luau               tipos exportados (TeamId, RaceState...)
    Net/                     definição única de todos os remotes
    Logic/                   lógica PURA e testável (física do gancho, regras de timer)
  server/                  -> ServerScriptService.Server
    init.server.luau         bootstrap: carrega e inicia os Services
    Services/
      PlayerDataService      persistência (ProfileStore)
      TeamService            Bond / equipes / CollisionGroups
      RaceService            timer, checkpoints, conclusão, validação
      ZoneService            gelo/descongelamento/kill via tags
      HookService            valida e retransmite ganchos entre jogadores
      LeaderboardService     OrderedDataStore + cache
  client/                  -> StarterPlayer.StarterPlayerScripts.Client
    init.client.luau         bootstrap dos Controllers
    Controllers/
      InputController        teclado/gamepad/touch -> ações abstratas
      HookController         simulação local do gancho (responsivo)
      CharacterController    estado de congelado, travas de movimento
      CameraController
      UIController           HUD, timer, menus
  ui/                      componentes de UI
tests/
```

## 3. Princípios de arquitetura

1. **Servidor é autoridade de estado; cliente é autoridade de *sensação*.**
   No Roblox o personagem tem *network ownership* do próprio cliente: movimento e gancho são
   simulados localmente (senão fica com lag). O servidor guarda o estado que importa
   (congelado, checkpoint, timer, equipe) e **valida** o que o cliente reporta.
2. **Gancho em outro jogador passa pelo servidor.** Um cliente não pode aplicar força no
   personagem de outro cliente. Fluxo: A dispara → servidor valida (mesma equipe, alcance, linha
   de visão) → servidor manda para o cliente de B aplicar o puxão em si mesmo. Isso precisa ser
   testado cedo, porque a latência afeta direto o *game feel*.
3. **Zonas por tags, não por scripts no mapa.** Level designers só marcam partes com tags
   (`FreezeZone`, `Checkpoint`...) via CollectionService. Um único `ZoneService` trata todas.
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
| M0 | Toolchain + scaffold + CI | `rojo serve` sincroniza; lint/format/testes passam no CI |
| M1 | Gancho solo | Balançar e se puxar é gostoso no PC e no celular |
| M2 | Zonas + checkpoints + timer | Mapa greybox jogável do início ao fim solo |
| M3 | Bond + gancho em parceiro | Dupla completa um trecho de "resgate" com ping de 150 ms |
| M4 | Tutorial + 2 mapas | Playtest com 5+ duplas, tempos dentro da meta |
| M5 | Dados + rankings | Recordes persistem; nenhum dado perdido em teste de troca de servidor |
| M6 | Polimento + mobile + lançamento | Retenção D1 medida no Analytics do Roblox |
