# 0049 — A zona mortal aceita o gancho
- Status: Aceita (responde Q43)
- Data: 2026-11-17
## Contexto
O RF-25 e o mapa diziam que a KillZone (vermelha) é grudável, mas as peças eram montadas sem colisão e o raycast
do gancho ignora peças sem colisão: mirar no vermelho atravessava a peça. Achado na revisão da Fase 3.
## Decisão
- **Sim:** o gancho prende na zona mortal, como no RF-25.
- Como fazer (escolha técnica): a peça `Kill` passa a ser **sólida** (`CanCollide = true`) nos mapas. Assim o
  raycast do gancho e a esfera de ajuda da mira a enxergam sem exceção no código. A morte continua vindo do
  `ZoneService` (consulta por caixa), que não depende de colisão.
## Consequências
- Prender no vermelho é seguro enquanto se está pendurado longe dele; encostar continua matando.
- Quem morre sobre uma faixa vermelha fica deitado nela até renascer (antes atravessava).
- Os geradores de mapa (`maps/*/build.luau`) montam `Kill` com colisão.
