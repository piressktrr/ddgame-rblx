# 0048 — O nível do gancho fica salvo entre sessões
- Status: Aceita (responde Q41; altera a consequência "sem salvar dados no MVP" do 0040)
- Data: 2026-11-17
## Decisão
O nível do gancho **persiste** entre sessões: é essencial para o jogador. Salvar dados entra no MVP, ao
menos para o progresso do gancho.
## Direção ainda aberta (Q23)
O dono indicou que evoluem **alcance e força**, ganhos **por estágio e com moedas**, mas nada está fechado.
## Consequências
- Entra no MVP uma camada de dados (DataStore; ProfileStore é a candidata, ferramenta nova → TOOLS.md/UNINSTALL.md).
- A implementação espera a Q23 fechar o que se salva.
