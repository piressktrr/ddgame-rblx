# 0044 — Lobby antes do mapa
- Status: Aceita
- Data: 2026-11-16
## Decisão (pedido do dono)
- Todo jogador nasce num **Lobby** separado do mapa (`Workspace.Lobby`), em greybox.
- Um **portal** (`LobbyPortal`) leva ao início da corrida (`RaceStart`). Entrar no portal começa a corrida do jogador.
- Morrer durante a corrida volta ao último checkpoint (ou ao `RaceStart`), não ao lobby.
- Placar da sessão, escolha de modo e arte do lobby ficam para depois.
## Consequências
Adianta a parte "lobby" da Fase 3 (IMPLEMENTATION_PLAN). O `SpawnLocation` do mapa deixa de ser o
nascimento inicial: o nascimento do jogo passa a ser o do lobby.
