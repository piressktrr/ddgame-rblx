# Plano de implementação da base do MVP

> Como construir a base das partes principais (mapa, câmera, lobby, gancho, zonas, corrida).
> Requisitos citados por ID de [REQUIREMENTS.md](REQUIREMENTS.md). Cada fase = uma branch `feat/…`
> saída da `main`, com merge só após aprovação do dono (AGENTS.md §4).

## 1. Fundações transversais (entram na primeira fase que precisar)

| Peça | Onde | O que é |
|---|---|---|
| `Config` | `src/shared/Config.luau` | Todos os números e tags. Tags novas: `NoHook`, `HookOnce`, `FreezeZone`, `UnfreezeZone`, `KillZone`, `Checkpoint`, `RaceStart`, `RaceFinish`, `BouncerPickup`, `BouncerZone`, `Jupiter`, `Mercury`, `Vulcan`, `Saturn`, `PressButton`, `LobbyPortal`. Sai `Hookable`. |
| `Net` | `src/shared/Net.luau` | Lista única de RemoteEvents (criados pelo servidor, buscados pelo cliente). Blink/ByteNet só se o volume pedir (M3). |
| `Logic/*` | `src/shared/Logic/` | Funções puras: mira no plano, física do puxão, regras de checkpoint, `InteractionPolicy`. |
| `TagWatcher` | `src/shared/Util/TagWatcher.luau` | Ajuda a reagir a peças com tag que aparecem/somem (streaming), com Trove. |
| Jest-Lua | `tests/` | Testes das funções de `Logic`. Entra junto com a primeira lógica pura. |

## 2. Como o mapa vive no projeto

Código fica em `src/` (Rojo). **Mapas são construídos no Studio** (greybox pelo MCP ou à mão), e
precisam ir para o Git também. Proposta:

- O place é salvo como **`place/RaceAndEscape.rbxlx`** (formato XML, dá para ver diferenças no Git).
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

### Fase 1 — `feat/m1-movimento` (câmera + plano + gancho solo)
Requisitos: RF-01..03, RF-10..14, RNF-01..06.

1. `Config`: tags novas, `Config.Camera`, `Config.Hook` (alcance, força, amortecimento).
2. `CameraController` (a partir do protótipo, só 2.5D): `BindToRenderStep` após a câmera padrão,
   distância/altura/FOV no Config, leve suavização (lerp) e "olhar à frente" na direção do movimento.
3. `CharacterController`: trava Z (posição e velocidade) a cada frame; W/S desligados.
4. `Logic/Aim.luau`: converte a posição do mouse num ponto do plano Z=0 (raio da câmera ∩ plano).
5. `HookController`:
   - mouse pressionado → raycast do personagem até a mira, alcance `Config.Hook.Range`,
     ignorando o próprio personagem;
   - acertou peça sem `NoHook` (e `HookOnce` não usado) → cria `RopeConstraint`/`AlignPosition` ou
     aplica força por frame (testar as duas, escolher pelo *feel*);
   - mouse solto → solta.
6. `HookService` (servidor): conjunto de `HookOnce` usados por jogador; cliente pede, servidor
   confirma; reseta ao morrer/checkpoint (gancho para RF-13 fica pronto na Fase 2).
7. Pista de teste greybox `Maps/TestHook` via MCP: comum, roxo, verde.
8. Pronto quando: playtest mostra balanço fluido; selene/stylua ok; dono aprova o *feel*.

### Fase 2 — `feat/m2-zonas-corrida` (zonas, morte, checkpoints, timer, lobby)
Requisitos: RF-20..27, RF-60..63, RF-13 (reset).

1. `ZoneService`: a cada `Heartbeat` (ou 10 Hz), `GetPartBoundsInBox` em cada personagem com
   `OverlapParams` filtrando peças de zona. Tabela tag → efeito.
2. Estado do jogador em atributos do personagem: `FrozenUntil` (tempo do servidor), `Checkpoint`.
3. Gelo: seta `FrozenUntil = agora + 15`; cliente lê e trava controles + mostra HUD;
   servidor mata quando o tempo acaba.
4. `RaceService`: checkpoints por ordem (`Order`), respawn no último, timer pessoal com
   `workspace:GetServerTimeNow()`, tela de fim.
5. Lobby: spawn no `Lobby`, `LobbyPortal` teleporta para `RaceStart`; placar da sessão
   (`SessionLeaderboard` em memória).
6. `UIController` mínimo: timer, contador do gelo, tela de fim. (Roblox UI direto; React/Fusion
   só se a UI crescer.)

### Fase 3 — `feat/m3-ferramentas-interacao` (Bouncer, lâmina, gancho em jogador)
Requisitos: RF-15, RF-16, RF-30..33, RF-40..41, RNF-03, RNF-07.

1. `BouncerService` + `BouncerController`: pickup → servidor dá a arma e controla munição;
   impulso aplicado **localmente** (`ApplyImpulse` no próprio root); recarga no servidor.
2. Empurrão em outro jogador (Bouncer e lâmina): cliente pede → `InteractionService` valida
   (`InteractionPolicy`, alcance, cooldown) → manda o cliente da vítima aplicar o impulso em si mesmo.
3. Gancho em jogador: mesmo fluxo, com o puxão aplicado nos dois clientes.
4. Corda replicada: servidor retransmite início/fim do gancho; outros clientes desenham com `Beam`.
5. Teste com 2 clientes no Studio (Test → Clients) e latência simulada de 150 ms.

### Fase 4 — `feat/m4-objetos-mapa` (deuses + mapa do MVP)
Requisitos: RF-50..54, RF-70..73.

1. Objetos Júpiter, Mercúrio, Vulcano, Saturno como prefabs com tag; comportamento nos
   Controllers/Services existentes (são "superfícies especiais" do gancho).
2. `PressButton` + porta para o Saturno.
3. Mapa `Map01` seguindo GAME_DESIGN §5.1: papel → greybox → playtest → iterar.
   Seções sugeridas: (1) gancho básico, (2) roxo/verde, (3) gelo + descongelar, (4) Bouncer,
   (5) combinação com rotas, (6) final.

### Depois do MVP
Dados (ProfileStore), ranking persistente separado por boost (ADR 0028), Bond (ADR 0023),
boosts (ADR 0025), arte e iluminação.

## 4. Riscos e como reduzir

| Risco | Mitigação |
|---|---|
| *Feel* do gancho ruim | Fase 1 só cuida disso; testar duas implementações de física |
| Puxar/empurrar outro jogador com lag | Prototipar cedo na Fase 3, com latência simulada |
| Personagem escapa do plano 2.5D | Trava no cliente + correção do servidor se Z sair do limite |
| Mapa no `.rbxlx` com conflito no Git | Só um agente edita o place por vez; registrar no STATUS |
| Morte com checkpoints longos frustra | Playtest medindo desistências por seção |
