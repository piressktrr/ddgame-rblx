# 0014 — Gelo: 15 s congelado e depois morte
- Status: Aceita
- Data: 2026-11-12
## Contexto
Esperar ser salvo deixa o jogo lento para o padrão do Roblox.
## Decisão
- Tocar no gelo congela por **15 s**. Congelado não anda nem usa gancho/Bouncer/lâmina.
- Se chegar a uma **zona de descongelar** antes do fim (puxado ou empurrado por outro jogador), volta ao normal.
- Se o tempo acabar, **morre** e renasce no último checkpoint.
## Consequências
Substitui "falhar não mata, congela" (pilar 3 do GDD v0.1). O gelo vira relógio de tensão: dá para ser salvo.
