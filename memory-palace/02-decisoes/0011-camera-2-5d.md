# 0011 — Câmera 2.5D lateral
- Status: Aceita (confirmada por 0038)
- Data: 2026-11-12
## Contexto
Comparados dois protótipos de câmera (CameraPrototypeController, tecla C); a lateral venceu.
## Decisão
Câmera **2.5D lateral**: o personagem se move num plano (esquerda/direita + pulo), com cenário
em profundidade para dar volume.
## Consequências
- Mapas são desenhados de lado; profundidade é só visual (plataformas finas no eixo Z).
- O gancho mira no plano 2D (mouse na tela → ponto no plano do jogo).
- O protótipo virou o `CameraController` definitivo.
