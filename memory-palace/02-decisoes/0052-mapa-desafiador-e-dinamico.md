# 0052 — Mapa desafiador, com trechos fáceis, dinâmico e com bifurcações; criação automatizada
- Status: Aceita (direção do dono; detalha o 0047 e o 0050)
- Data: 2026-11-21
## Contexto
O dono olhou o mapa atual e achou: simples demais e fácil de passar só com o gancho, quase sem bifurcação nem
desafio real, alturas muito desniveladas e pontos que o gancho não alcança. O mapa da Fase 2 (ADR 0050) foi medido
com o movimento antigo (andar 24, gravidade 196,2); a física nova, inspirada no DDNet, mudou as medidas.
O vídeo de 2026-11-14 ([estudo](../04-game-design/estudos/referencia-video-2026-11-14.md)) serve de base de
padrões (só padrões, regra 1 do AGENTS.md).
## Decisão
- **Desafiador, com trechos fáceis:** a dificuldade alterna (apertado → amplo → gargalo → respiro), não só sobe.
- **Mais dinâmico:** mecânicas combinadas (gancho, pulo duplo, martelo, gancho em jogador, gelo, mão única), não
  "só gancho".
- **Bifurcações de verdade:** caminhos diferentes, com trocas claras (rápido e arriscado × lento e seguro).
- **Alturas bem definidas** pelas medidas do movimento atual, e **todo alvo do gancho ao alcance** e na tela.
- **Criação automatizada em etapas:** (1) tabela de medidas tirada do `Config`; (2) mapa como dados (grade de
  blocos do MapBuilder) com exportar/importar; (3) validador que simula o movimento e confere o mapa;
  (4) biblioteca de trechos e montador; (5) ajuste com dados de jogo.
- **Ainda não mexer no mapa:** as etapas 1–3 só medem e relatam; o mapa só muda depois, com o dono.
## Consequências
- Toda medida de mapa (pulo, vão, alcance, tela) sai do `Config`; mudar a física muda as regras do mapa junto.
- O validador vira o "porteiro" de qualquer mapa, feito à mão no MapBuilder ou montado por script.
