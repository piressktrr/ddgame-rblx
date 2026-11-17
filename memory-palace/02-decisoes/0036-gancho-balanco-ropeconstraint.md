# 0036 — Gancho: balanço (B) com RopeConstraint, mira com esfera e corda recolhível
- Status: Substituída em parte por 0042 (tipo e corda); mira, alcance e uso continuam. (Responde Q32; refina 0016 e 0033; mira ajustada ao 2.5D por 0038)
- Data: 2026-11-16
## Decisão
- **Tipo:** B, balanço (pêndulo). Se ficar difícil de jogar, muda para A (puxão). Esta troca já está aprovada de antemão.
- **Física:** começar com `RopeConstraint` + força extra (`VectorForce`) no cliente, para ter um protótipo funcional rápido. Se a sensação não servir, migrar para força calculada por nós a cada quadro.
- **Mira (2.5D):** o gancho sai na direção do cursor, no plano do jogo; se o raio não acertar nada, uma esfera lançada (`Spherecast`) no mesmo caminho pega o alvo "quase na mira".
- **Corda:** enquanto preso, o jogador pode recolher e soltar corda.
- **Uso:** funciona no ar e em sequência (soltar e prender de novo sem tocar o chão).
- **Alcance inicial:** 40 studs (`Config.Hook.Range`) como ponto de partida.
- **Botão:** mouse esquerdo segura o gancho (segurar = preso, ADR 0016).
## Consequências
O protótipo segue a ordem do estudo `04-game-design/estudos/gancho-o-que-precisa.md` §7. O tipo C (misto)
fica como evolução possível do B (recolher corda já é parte dele).
