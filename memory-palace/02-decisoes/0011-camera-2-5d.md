# 0011 — Câmera 2.5D lateral
- Status: Substituída provisoriamente por 0031 (experimento 3D)
- Data: 2026-11-12
## Contexto
Comparados protótipos de 3ª pessoa e 2.5D (CameraPrototypeController, tecla C). Também foi
considerado um labirinto 3D em 3ª pessoa e descartado.
## Decisão
Câmera **2.5D lateral**: o personagem se move num plano (esquerda/direita + pulo), com cenário
em profundidade para dar volume.
## Consequências
- Mapas são desenhados de lado; profundidade é só visual (plataformas finas no eixo Z).
- O gancho mira no plano 2D (mouse na tela → ponto no plano do jogo).
- O protótipo vira o `CameraController` definitivo no M1 (sem o modo 3ª pessoa).
