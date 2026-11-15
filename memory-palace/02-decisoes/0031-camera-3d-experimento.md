# 0031 — Câmera 3D em 3ª pessoa ("3D sobre trilhos") — experimento
- Status: Aceita **provisoriamente** pelo dono; falta aprovação do outro membro da equipe.
  Substitui 0011 enquanto durar o experimento.
- Data: 2026-11-15
## Contexto
Meta de alcance e monetização; análise em [estudos/camera-2-5d-vs-3d.md](../04-game-design/estudos/camera-2-5d-vs-3d.md).
## Decisão
- Câmera padrão do Roblox em 3ª pessoa. Cada estágio é uma pista larga que avança sempre para frente.
- Sem visual: só o template padrão do Roblox (blocos cinza), para mudar fácil se a decisão voltar atrás.
- O código 2.5D fica no projeto, desligado por `Config.Camera.Mode` ("ThirdPerson" | "SideView").
## Consequências
Mira do gancho em 3D precisa de ajuda de mira. Diferencial do jogo: gancho que puxa os dois, Bouncer e caos.
