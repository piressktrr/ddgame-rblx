# Plano de implementação da base do MVP

> Como construir a base das partes principais (mapa, câmera, lobby, gancho, zonas, corrida).
> Requisitos citados por ID de [REQUIREMENTS.md](REQUIREMENTS.md). Cada fase = uma branch `feat/…`
> saída da `main`, com merge só após aprovação do dono (AGENTS.md §4).

## 1. Fundações transversais (entram na primeira fase que precisar)

| Peça | Onde | O que é |
|---|---|---|
| `Config` | `src/shared/Config.luau` | Todos os números e tags. Tags novas: `NoHook`, `HookOnce`, `FreezeZone`, `UnfreezeZone`, `KillZone`, `Checkpoint`, `RaceStart`, `RaceFinish`, `BouncerPickup`, `BouncerZone`, `Jupiter`, `Mercury`, `Vulcan`, `Saturn`, `PressButton`, `LobbyPortal`. Sai `Hookable`. |
| `Net` | `src/shared/Net.luau` | Lista única de RemoteEvents (criados pelo servidor, buscados pelo cliente). Blink/ByteNet só se o volume pedir (M4). |
| `Logic/*` | `src/shared/Logic/` | Funções puras: mira no plano, física do puxão, regras de checkpoint, `InteractionPolicy`. |
| `TagWatcher` | `src/shared/Util/TagWatcher.luau` | Ajuda a reagir a peças com tag que aparecem/somem (streaming), com Trove. |
| Jest-Lua | `tests/` | Testes das funções de `Logic`. Entra junto com a primeira lógica pura. |

## 2. Como o mapa vive no projeto

Código fica em `src/` (Rojo). **Mapas são construídos no Studio** (greybox pelo MCP ou à mão), e
precisam ir para o Git também. Proposta:

- O place é salvo em **`place/RaceAndEscape.rbxl`** (binário: o Git não mostra as diferenças).
- Estrutura no Workspace:
  ```
  Workspace/
    Lobby/           spawn, portal (LobbyPortal), placar da sessão
    Maps/
      Map01/         seções, cada uma com seus checkpoints e zonas por tag
  ```
- Peças só recebem **tags e atributos** (ex.: atributo `Order` no checkpoint, `Direction` no Mercúrio).
  Nenhum script dentro do mapa (RNF-05).
- Prefabs (portal, checkpoint, objetos mágicos) em `ServerStorage/Prefabs`, também no place.
- Plano Z do mapa: todo o percurso jogável em **Z = 0**. Cenário de fundo em Z negativo.

## 3. Fases

Ordem definida no ADR 0040: gancho solo → mapa novo com o gancho → zonas e corrida → interação entre
jogadores e ferramentas → objetos mágicos e progressão.

### Fase 1 — `feat/m1-gancho` (plano + gancho solo)
Requisitos: RF-01..05, RF-10..14, RF-17..19, RNF-01..06. Decisões: ADR 0036 e 0039.

1. `Config`: `Config.Hook` (alcance 40, recarga, `AimAssistRadius` 3, limites de velocidade e de corda).
2. Câmera e plano (já existem): conferir em playtest com a altura visível fixa; adicionar correção de Z
   **no servidor** (`PlaneService`) e colisão entre jogadores (RF-04).
3. `Logic/Aim.luau`: cursor → ponto do plano Z = 0; limita ao alcance; acha o alvo com raio e, se falhar,
   com `Spherecast` (esfera de ajuda). Só peças na profundidade do plano.
4. `HookController` (cliente, só `RopeConstraint` + `VectorForce`, sem testar outras físicas antes):
   botão esquerdo preso = gancho; W recolhe e S solta (mudança gradual do `Length`); funciona no ar e em
   sequência; limite de velocidade; Humanoid em estado compatível enquanto preso.
5. Corda visível local (`Beam`) e cursor em três estados (sem alvo, válido, proibido).
6. `HookService` (servidor): valida alcance e tag; guarda `HookOnce` usado por jogador (zera ao
   morrer/checkpoint); repassa início/fim da corda aos outros clientes.
7. Pista de teste greybox `Maps/TestHook` via MCP: comum, roxo, verde, vãos de 20/30/40 studs, paredes e teto.
8. Pronto quando: balanço fluido no playtest, selene/stylua ok, dono aprova o *feel*. Se o balanço
   ficar difícil de jogar, trocar para puxão (ADR 0036).

### Fase 2 — `feat/m2-mapa` (mapa novo com o gancho)
Requisitos: RF-70, RF-71, RF-73, RF-74. A estrutura do mapa é definida pelo dono (Q31).

1. Refazer o `Workspace.Maps.Map01` do place a partir do que o dono definir, com checkpoints e trechos de gancho.
2. Greybox → playtest → iterar (GAME_DESIGN §5.1). O dono aprova o mapa antes da Fase 4.

### Fase 3 — `feat/m3-zonas-corrida` (zonas, morte, checkpoints, timer, lobby)
Requisitos: RF-20..27, RF-60..63, RF-13 (reset).

1. `ZoneService`: a cada `Heartbeat` (ou 10 Hz), `GetPartBoundsInBox` em cada personagem com
   `OverlapParams` filtrando peças de zona. Tabela tag → efeito.
2. Estado do jogador em atributos do personagem: `FrozenUntil` (tempo do servidor), `Checkpoint`.
3. Gelo: seta `FrozenUntil = agora + 15`; cliente lê e trava controles + mostra HUD;
   servidor mata quando o tempo acaba.
4. `RaceService`: checkpoints por ordem (`Order`; um a cada 3 estágios, ADR 0034), respawn no último,
   timer pessoal com `workspace:GetServerTimeNow()`, tela de fim. (Parte já existe em `CheckpointService`.)
5. Lobby: spawn no `Lobby`, `LobbyPortal` teleporta para `RaceStart`; placar da sessão
   (`SessionLeaderboard` em memória).
6. `UIController` mínimo: timer, contador do gelo, tela de fim. (Roblox UI direto; React/Fusion
   só se a UI crescer.)

### Fase 4 — `feat/m4-interacao` (gancho em jogador, Bouncer, lâmina)
Requisitos: RF-15, RF-16, RF-30..33, RF-40..41, RNF-03, RNF-07. Só começa com o mapa aprovado (ADR 0037).

1. Gancho em jogador, caminho A: o servidor valida (`InteractionPolicy`, alcance, linha de visão) e
   manda aos dois clientes "puxe-se em direção ao outro". Teste com 2 clientes (Test → Clients) e
   latência de 150 ms. Plano B: caminho C (ADR 0037).
2. `BouncerService` + `BouncerController`: pickup → servidor dá a arma e controla munição;
   impulso aplicado **localmente** (`ApplyImpulse` no próprio root); recarga no servidor.
3. Empurrão em outro jogador (Bouncer e lâmina): cliente pede → `InteractionService` valida
   → manda o cliente da vítima aplicar o impulso em si mesmo. Conferir a correção de Z no servidor.
4. Corda replicada para os outros clientes com `Beam`.

### Fase 5 — `feat/m5-objetos-progressao` (deuses, nível do gancho, acabamento)
Requisitos: RF-50..54, RF-80..81.

1. Objetos Júpiter, Mercúrio, Vulcano, Saturno como prefabs com tag; comportamento nos
   Controllers/Services existentes (são "superfícies especiais" do gancho). `PressButton` + porta para o Saturno.
2. Nível do gancho (RF-80/81): regra de ganho (Q23) e persistência (Q41); modificadores em `Config` por nível.
3. Revisão final do mapa com todas as mecânicas (ensinar → testar → torcer).

### Depois do MVP
Dados (ProfileStore), ranking persistente separado por boost (ADR 0028), Bond (ADR 0023),
rebirth (ADR 0032), boosts e loja (ADR 0025; a monetização é essencial), arte e iluminação.

## 4. Riscos e como reduzir

| Risco | Mitigação |
|---|---|
| *Feel* do gancho ruim | Fase 1 só cuida disso; começa com `RopeConstraint` e, se falhar, troca para puxão ou física própria |
| Balanço da corda brigando com a trava de Z e a colisão entre jogadores | Testar na Fase 1 e na Fase 4, com correção de Z também no servidor |
| Puxar/empurrar outro jogador com lag | Prototipar na Fase 4 com latência simulada; plano B é o caminho C (ADR 0037) |
| Personagem escapa do plano 2.5D | Trava no cliente + correção no servidor se Z sair do limite (ADR 0039) |
| Mapa no `.rbxlx` com conflito no Git | Só um agente edita o place por vez; registrar no STATUS |
| Morte com checkpoints longos frustra | Playtest medindo desistências por estágio |
