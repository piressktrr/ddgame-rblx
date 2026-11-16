# 0038 — O jogo é 2.5D (decisão da equipe)
- Status: Aceita (restaura 0011; substitui 0031 e 0035)
- Data: 2026-11-16
## Contexto
A equipe decidiu o formato do jogo: câmera lateral 2.5D. O experimento de câmera anterior (0031) foi
descartado e o mapa feito nele (0035) deixa de ser usado.
## Decisão
- Câmera lateral 2.5D (ADR 0011) é a definitiva. Todo o jogo acontece num plano (Z = 0).
- `Config.Camera.Mode` foi removido: `CameraController` e `CharacterController` sempre rodam.
- O mapa de referência é `maps/map01` (gerado por `tools/mapgen.py`).
- O gancho mira com o mouse no plano (ADR 0036 ajustado).
## Consequências
- Os arquivos do experimento foram removidos do projeto (ficam no histórico do Git, commit `b3779b4`).
- O `place/RaceAndEscape.rbxl` ainda contém o mapa do experimento; precisa ser refeito a partir de `maps/map01` no Studio.
- Dúvidas novas do 2.5D: ver Q33 a Q39 em `03-duvidas/OPEN_QUESTIONS.md`.
