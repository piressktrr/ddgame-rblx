# 0043 — Pulo duplo e velocidade maior no movimento base
- Status: Aceita (substitui 0027)
- Data: 2026-11-16
## Decisão (pedido do dono)
- **Pulo duplo:** um segundo pulo no ar, uma vez até tocar o chão (ou até prender o gancho, que devolve o pulo).
- **Velocidade:** andar mais rápido que o padrão do Roblox (16). Valor inicial 24 em `Config.Movement`.
- **Depois do gancho (Q42, dono: sim):** no embalo, com a corda já solta, o pulo duplo vale e o embalo horizontal continua (encerrar devolvia o corpo ao Humanoid, que freava o X no ar). Com a corda presa, não.
- Sem pulo de parede (continua como no 0027).
## Consequências
O 0027 dizia que toda a mobilidade avançada vinha do gancho e do Bouncer. Agora o movimento base também ajuda;
os vãos do mapa podem precisar de ajuste depois do playtest. Números em `Config.Movement`.
