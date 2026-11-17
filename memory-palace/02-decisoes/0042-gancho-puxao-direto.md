# 0042 — Gancho: puxão direto ao alvo (tipo A), segurar para ficar preso
- Status: Aceita (substitui o tipo B do ADR 0036; troca já prevista lá)
- Data: 2026-11-16
## Contexto
O primeiro playtest real do balanço (B) funcionou, mas o dono quer menos controle manual: sem W/S, um clique
e o personagem vai ao alvo.
## Decisão
- **Clique:** um clique no alvo prende o gancho e puxa o personagem em linha reta até o ponto, sozinho.
- **Segurar:** se o botão continuar apertado ao chegar, o personagem fica preso no ponto até soltar.
  Se já soltou, o gancho solta ao chegar e o personagem segue com parte do embalo.
- **Sem W/S:** recolher/soltar corda sai do gancho (as teclas ficam livres).
- **Velocidade:** um pouco menor que a do balanço testado (que chegava a ~78 studs/s).
- **Animação de voo:** pose fluida durante o puxão (sem asset novo).
- O que continua do 0036/0039: mira pelo cursor com esfera de ajuda, alcance 40, roxo e verde, uso no ar e em sequência,
  servidor valida.
## Consequências
`SwingPhysics` deixa de ser o modo padrão (fica no código como referência, `Config.Hook.Mode`). A interpretação
de "segurar" acima foi feita pelo agente e deve ser confirmada pelo dono no playtest.
