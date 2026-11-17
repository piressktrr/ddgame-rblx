# 0051 — A/D continua empurrando no embalo
- Status: Aceita (responde Q56)
- Data: 2026-11-17
## Contexto
No teste da lição 7 do tutorial apareceu que, no embalo depois de soltar o gancho, o `AirBody` aplica A/D a
50 studs/s² sem freio de ar. O salto de embalo vai bem além dos ~48 studs da conta do estudo da Fase 2.
## Decisão
- **Fica assim:** A/D continua valendo no embalo, sem redução.
## Consequências
- Vãos de embalo que devem exigir o pulo duplo põem o alvo seguinte mais alto (~12 studs), como na lição 7 e nas
  saídas do E7.
- Vãos "no mesmo nível" de até ~45 passam só com embalo + A/D; isso vale para medir o mapa e para a rota que
  exige nível (ADR 0050), que só barra quando o gancho ler `RequiresHookLevel` (Q23).
