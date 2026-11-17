# 0037 — Gancho em outro jogador: caminho A; caminho C anotado como plano B
- Status: Aceita (responde parte da Q32; detalha 0003)
- Data: 2026-11-16
## Decisão
- **Caminho A:** o servidor valida e manda aos dois clientes "puxe-se em direção ao outro"; cada cliente move o próprio personagem.
- **Só depois de aprovarmos o mapa:** o gancho em jogador não entra no primeiro protótipo (que é solo).
## Plano B (registrado para caso o A dê errado)
- **Caminho C:** dar ao atacante a posse da física do jogador puxado durante o puxão. É rápido, mas abre
  porta para trapaça (jogar o outro longe), então exigiria validação forte no servidor.
- Só trocar para o C se o teste com 2 clientes e latência simulada mostrar que o A fica ruim. O caminho B
  (servidor assume a física) foi descartado por travar o controle de quem é puxado.
