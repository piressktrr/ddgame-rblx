# 0039 — Regras do plano 2.5D (colisão, gancho, mira, teclas, tela, estágios)
- Status: Aceita (responde Q33 a Q39; detalha 0038 e 0036)
- Data: 2026-11-16
## Decisão
- **Colisão (Q33):** jogadores **colidem** entre si no plano (dá para empilhar e bloquear o caminho).
- **Alcance do gancho (Q34):** só prende em peças que estão na **profundidade do plano de jogo**. Cenário
  de fundo ou de frente não é grudável.
- **Mira (Q35, valor padrão definido por mim, a ajustar em playtest):** esfera de ajuda com raio de
  **3 studs** (`Config.Hook.AimAssistRadius`); o alcance conta a partir do `HumanoidRootPart`; cursor
  além do alcance é limitado ao alcance, na mesma direção; mira em 360° no plano.
- ~~**Corda (Q36):**~~ (removido pelo ADR 0042: sem W/S no gancho) **W recolhe** e **S solta** corda enquanto preso (ficam livres porque a profundidade
  é bloqueada no 2.5D). Roda do mouse fica como alternativa para testar.
- **Tela (Q37):** o que se fixa é a **altura visível**. O campo de visão do Roblox é vertical, então
  a câmera atual já faz isso; telas mais largas veem mais mundo nas laterais.
- **Estágios (Q38):** podem ter **subidas verticais**, não só avançar para a direita.
- **Saída do plano (Q39):** o desvio de Z é corrigido no cliente **e também no servidor**.
## Consequências
- O `CharacterController` ganha, depois, a correção no servidor (ADR 0037 depende disso).
- Colisão entre jogadores precisa ser conferida junto da trava de Z: um empurrão não pode tirar
  ninguém do plano.
- O mapa precisa ter todas as peças grudáveis com a mesma profundidade.
