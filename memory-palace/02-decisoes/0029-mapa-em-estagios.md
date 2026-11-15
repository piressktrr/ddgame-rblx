# 0029 — Mapa em 6 estágios, ordem fixa, atalhos dentro de cada estágio
- Status: Aceita (refina 0012 e 0022)
- Data: 2026-11-15
## Contexto
Estudo em memory-palace/04-game-design/estudos/referencias-mapas.md (padrões do gênero + jogos lineares do Roblox).
## Decisão
- O primeiro mapa tem **6 estágios** numerados, sempre na **mesma ordem**.
- "Várias rotas" = **atalhos menores dentro de cada estágio**, não grandes bifurcações.
- Cada estágio é um prefab com entrada e saída padrão (facilita montar e reordenar mapas novos).
