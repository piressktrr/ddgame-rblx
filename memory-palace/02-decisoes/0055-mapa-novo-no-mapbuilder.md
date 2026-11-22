# 0055 — Mapa novo no MapBuilder, solo possível, checkpoints por trecho e ~8 min
- Status: Aceita (substitui 0034, 0050 e a meta de tempo do 0040; confirma 0004, 0020, 0023; detalha 0052)
- Data: 2026-11-22
## Decisão
- **O Map01 sai.** Um mapa novo é feito no **MapBuilder** (os elementos já estão separados), com ideias de design
  parecidas com as do [vídeo de referência](../04-game-design/estudos/referencia-video-2026-11-14.md) (só padrões,
  regra 1 do AGENTS.md).
- **Bloco padrão:** o tamanho mais adequado medido nos frames do vídeo (proporção bloco × personagem × tela).
- **Tudo dá para terminar sozinho;** a dupla só ajuda (atalhos, mais rápido). Nenhum trecho exige parceiro.
- **Checkpoints por trecho temático,** com **tempo parcial** na tela (no lugar de "um a cada 3 estágios").
- **Duração:** ~8 min para o jogador médio, como o validador estima.
- **Quem desenha:** o Claude gera propostas de trechos (com o validador) e o dono e a equipe aprovam.
- **Nível do gancho** no mapa só quando a evolução do gancho (Q23) existir.
## Consequências
- O validador simula um jogador só: é exatamente o critério "dá para terminar sozinho".
- `maps/map01`, `tools/map_layout.py` e afins viram histórico quando o mapa novo entrar.
