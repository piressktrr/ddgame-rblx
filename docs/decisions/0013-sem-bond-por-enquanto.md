# 0013 — Sem Bond por enquanto: todos interagem com todos
- Status: Aceita (substitui 0002 durante os testes)
- Data: 2026-11-12
## Contexto
Puxar jogadores aleatórios, para atrapalhar ou salvar, é parte da diversão.
## Decisão
Nos testes e no MVP não há Bond. Qualquer jogador pode enganchar, empurrar e salvar qualquer outro.
"Grupo" é só jogadores que combinam de se ajudar, sem sistema no jogo.
## Consequências
- Progresso, checkpoint e tempo são **por jogador** (ADR 0018).
- Risco de troll aceito por enquanto. O código mantém um ponto único de "pode interagir?"
  (`InteractionPolicy`) para religar alguma proteção depois sem reescrever nada.
