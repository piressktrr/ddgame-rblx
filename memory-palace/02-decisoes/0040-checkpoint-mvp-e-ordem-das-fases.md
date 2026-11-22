# 0040 — Meta de duração, nível do gancho no MVP e nova ordem das fases
- Status: Aceita (refina 0018, 0030, 0033; responde Q40 A, C e D); meta de tempo substituída por 0055 (~8 min)
- Data: 2026-11-16
## Decisão
- **Checkpoint (A):** vale o ADR 0034 (a cada 3 estágios). A **duração de uma corrida completa é uma
  meta separada: 10 a 15 minutos** para um jogador médio. O "~3 min entre checkpoints" do ADR 0018 deixa de valer.
- **Estrutura do mapa (B):** o dono vai reformular o mapa por conta própria; nada do documento sobre a
  estrutura dele é alterado por enquanto (Q31).
- **Progressão no MVP (C):** entra um sistema simples de **nível do gancho** (alcance e raio da esfera de
  ajuda), ganho jogando. Rebirth, boosts e loja ficam fora do MVP, mas a **monetização é essencial
  depois** e o desenho da progressão deve deixá-la possível (ADR 0025 e 0028).
- **Ordem das fases (D):** 1) gancho solo, 2) mapa novo com o gancho (aprovação do dono), 3) zonas,
  gelo, checkpoints, timer e lobby, 4) gancho em jogador, Bouncer e lâmina, 5) objetos mágicos, nível do
  gancho e acabamento.
## Consequências
- GAME_DESIGN v0.4, REQUIREMENTS e IMPLEMENTATION_PLAN foram atualizados com isto.
- ~~Sem salvar dados no MVP, o nível do gancho não persiste entre sessões (Q41).~~ Mudou no 0048: o nível fica salvo.
