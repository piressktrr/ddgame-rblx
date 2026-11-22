# Biblioteca de trechos — conferência

Gerado por `python -I -X utf8 tools/mapkit/chunks.py` (ADR 0052, etapa 4). Cada trecho foi jogado SOZINHO pelo validador, da entrada até a saída, com almofadas em volta (ver `maps/trechos/README.md`). Tempos incluem ~0,5 s dos corredores de teste.

| Trecho | Tema | Ritmo | Mecânicas exigidas | Rota solo | Rápida | Jogador médio | Menor janela (segura) | Dificuldade alvo / medida | Caminhos | Faixas |
|---|---|---|---|---|---|---|---|---|---|---|
| p-s1-cortinas | vale | amplo | jump, double | sim | 10,7 s | 14,4 s | 0,24 s | 3 / 3 | 1 | — |
| p-s1-escadaria | vale | respiro | jump | sim | 8,1 s | 9,2 s | 0,42 s | 2 / 2 | 1 | — |
| p-s1-fosso-duplo | vale | amplo | double | sim | 7,2 s | 8,7 s | 0,21 s | 3 / 3 | 2 | alto ok 7,7 s, janela 0,65 s; fosso ok 7,2 s, janela 0,3 s |
| p-s1-primeiro-gancho | vale | gargalo | hook | sim | 6,3 s | 8,9 s | 0,28 s | 3 / 3 | 1 | — |
| p-s2-brasas | torres | apertado | jump | sim | 13 s | 29,1 s | 0,15 s | 4 / 5 | 1 | — |
| p-s2-galeria | torres | respiro | jump | sim | 7,6 s | 8,9 s | 0,55 s | 2 / 2 | 1 | — |
| p-s2-patamar | torres | amplo | jump | sim | 7,8 s | 9,3 s | 0,37 s | 3 / 3 | 2 | ponte ok 7,8 s, janela 0,4 s; chao ok 8,5 s, janela 0,4 s |
| p-s2-teto-de-gelo | torres | apertado | jump | sim | 10,7 s | 21,4 s | 0,11 s | 4 / 4 | 1 | — |
| p-s2-torres | torres | apertado | — | sim | 5,5 s | 10,4 s | 0,21 s | 4 / 3 | 2 | — |
| p-s3-balanco | ventania | amplo | — | sim | 8,4 s | 10,3 s | 0,34 s | 3 / 3 | 2 | balanco ok 7,7 s, janela 0,5 s; baixo ok 8,8 s, janela 0,4 s |
| p-s3-planicie | ventania | respiro | jump | sim | 6,9 s | 8,1 s | 0,5 s | 2 / 2 | 1 | — |
| p-s3-rajada | ventania | apertado | hook, momentum | sim | 7,8 s | 14 s | 0,05 s | 4 / 5 | 1 | — |
| p-s3-verde | ventania | gargalo | hookonce, hook | sim | 6,1 s | 21,5 s | 0,05 s | 4 / 5 | 1 | — |
| p-s4-dica | portas | gargalo | hook, momentum | sim | 6,3 s | 9 s | 0,17 s | 4 / 4 | 1 | — |
| p-s4-portas | portas | apertado | jump, double | sim | 12,4 s | 17 s | 0,17 s | 4 / 4 | 1 | — |
| p-s4-saguao | portas | respiro | walk, jump | sim | 7,3 s | 8,6 s | 0,5 s | 2 / 2 | 1 | — |
| p-s4-sala-um-ponto | portas | gargalo | hook | sim | 8,4 s | 10,5 s | 0,18 s | 4 / 4 | 1 | — |
| p-s4-valvulas | portas | amplo | — | sim | 6,8 s | 9,6 s | 0,26 s | 3 / 3 | 4 | cima ok 6,8 s, janela 0,45 s; baixo ok 7,6 s, janela 0,5 s |
| p-s5-chamine | poco | apertado | — | sim | 8,9 s | 13,4 s | 0,18 s | 4 / 5 | 2 | gancho ok 7,9 s, janela 0,2 s; degraus ok 10,7 s, janela 0,4 s |
| p-s5-descida | poco | respiro | walk | sim | 8 s | 9,5 s | 0,66 s | 2 / 2 | 1 | — |
| p-s5-furo | poco | gargalo | double | sim | 21,7 s | 27,9 s | 0,21 s | 3 / 3 | 1 | — |
| p-s5-ilhas | poco | amplo | jump | sim | 6,3 s | 7,4 s | 0,37 s | 3 / 3 | 3 | ganchos ok 5,6 s, janela 0,4 s; ilhas ok 7,4 s, janela 0,4 s |
| p-s6-gaiola | cume | apertado | hook, hookthrough | sim | 8,1 s | 22,6 s | 0,05 s | 4 / 5 | 1 | — |
| p-s6-mirante | cume | respiro | jump | sim | 7,3 s | 8,4 s | 0,55 s | 2 / 2 | 1 | — |
| p-s6-ponte | cume | gargalo | hook, solo | sim | 6,4 s | 21 s | 0,05 s | 5 / 5 | 1 | — |
| p-s6-reta | cume | amplo | jump | sim | 7,1 s | 8 s | 0,37 s | 3 / 3 | 4 | embalo ok 6,8 s, janela 0,2 s; chao ok 9,3 s, janela 0,5 s |

## p-s1-cortinas — Cortinas de gelo

- tema vale · padrão freeze como chão falso + rede de segurança (vídeo, padrões 3, 6 e 10) · 92 × 14 células de 4 studs · portas: in (entrada, esquerda, pos 4, largura 5), out (saída, direita, pos 8, largura 5) · fecha trecho temático (checkpoint depois)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 10,7 s (17,2 s esperado), menor janela 0,13 s, manobras: double ×5, jump ×2
- rota jogador médio: 11,5 s (14,4 s esperado), menor janela 0,24 s, manobras: double ×6, jump ×2
- rota mais segura: 12,9 s (16,1 s esperado), menor janela 0,24 s, manobras: double ×6, jump ×3
- prévia: [p-s1-cortinas.svg](./p-s1-cortinas.svg)
- problemas: nenhum

## p-s1-escadaria — Escadaria de boas-vindas

- tema vale · padrão original: degraus de pulo · 72 × 12 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 8,1 s (9,6 s esperado), menor janela 0,42 s, manobras: double ×1, jump ×4, walk ×1
- rota jogador médio: 8,5 s (9,2 s esperado), menor janela 0,34 s, manobras: double ×2, jump ×1
- rota mais segura: 8,1 s (9,6 s esperado), menor janela 0,42 s, manobras: double ×1, jump ×4, walk ×1
- prévia: [p-s1-escadaria.svg](./p-s1-escadaria.svg)
- problemas: nenhum

## p-s1-fosso-duplo — Fosso do pulo duplo

- tema vale · padrão ensinar→cobrar (vídeo, padrão 2) · 66 × 14 células de 4 studs · portas: in (entrada, esquerda, pos 6, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 7,2 s (9,7 s esperado), menor janela 0,21 s, manobras: double ×1, jump ×4, walk ×2
- rota jogador médio: 7,9 s (8,7 s esperado), menor janela 0,37 s, manobras: double ×3
- rota mais segura: 9 s (11,2 s esperado), menor janela 0,21 s, manobras: double ×2, jump ×3, walk ×2
- prévia: [p-s1-fosso-duplo.svg](./p-s1-fosso-duplo.svg)
- problemas:
  - aviso: a faixa rápida alto não é mais rápida que a segura fosso (7.70 s × 7.21 s)

## p-s1-primeiro-gancho — O primeiro gancho

- tema vale · padrão sala de um ponto só (vídeo), versão de ensino · 72 × 20 células de 4 studs · portas: in (entrada, esquerda, pos 6, largura 5), out (saída, direita, pos 14, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, andar
- rota mais rápida: 6,3 s (13,2 s esperado), menor janela 0,1 s, manobras: hook+double ×2, hook+momentum ×1
- rota jogador médio: 7,6 s (8,9 s esperado), menor janela 0,28 s, manobras: hook ×1, hook+double ×3
- rota mais segura: 10,4 s (11,8 s esperado), menor janela 0,28 s, manobras: hook ×1, hook+double ×3, jump ×1
- prévia: [p-s1-primeiro-gancho.svg](./p-s1-primeiro-gancho.svg)
- problemas: nenhum

## p-s2-brasas — Corredor de brasas

- tema torres · padrão corredor de freeze com ilhas (vídeo), em pulos · 116 × 11 células de 4 studs · portas: in (entrada, esquerda, pos 5, largura 5), out (saída, direita, pos 5, largura 5) · fecha trecho temático (checkpoint depois)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 13 s (67,2 s esperado), menor janela 0,05 s, manobras: double ×1, jump ×11
- rota jogador médio: 14,7 s (29,1 s esperado), menor janela 0,15 s, manobras: double ×6, jump ×5
- rota mais segura: 16,1 s (30,7 s esperado), menor janela 0,15 s, manobras: double ×7, jump ×5
- prévia: [p-s2-brasas.svg](./p-s2-brasas.svg)
- problemas: nenhum

## p-s2-galeria — Galeria das cortinas

- tema torres · padrão original: respiro com o tema do gelo · 70 × 14 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 7,6 s (9,1 s esperado), menor janela 0,55 s, manobras: double ×1, jump ×4, walk ×1
- rota jogador médio: 8,2 s (8,9 s esperado), menor janela 0,34 s, manobras: double ×2, jump ×1
- rota mais segura: 7,6 s (9,1 s esperado), menor janela 0,55 s, manobras: double ×1, jump ×4, walk ×1
- prévia: [p-s2-galeria.svg](./p-s2-galeria.svg)
- problemas: nenhum

## p-s2-patamar — Patamar das pontes

- tema torres · padrão original: duas pistas paralelas · 72 × 16 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 5, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 7,8 s (9,6 s esperado), menor janela 0,37 s, manobras: double ×1, jump ×6
- rota jogador médio: 8,1 s (9,3 s esperado), menor janela 0,37 s, manobras: double ×2, jump ×3
- rota mais segura: 8,4 s (9,9 s esperado), menor janela 0,37 s, manobras: double ×2, jump ×4
- prévia: [p-s2-patamar.svg](./p-s2-patamar.svg)
- problemas: nenhum

## p-s2-teto-de-gelo — Escada sob o gelo

- tema torres · padrão original: teto de freeze que proíbe o pulo duplo · 89 × 26 células de 4 studs · portas: in (entrada, esquerda, pos 3, largura 5), out (saída, direita, pos 19, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 10,7 s (24,2 s esperado), menor janela 0,11 s, manobras: double ×1, jump ×8
- rota jogador médio: 11,3 s (21,4 s esperado), menor janela 0,11 s, manobras: jump ×8
- rota mais segura: 11,3 s (21,6 s esperado), menor janela 0,11 s, manobras: jump ×9
- prévia: [p-s2-teto-de-gelo.svg](./p-s2-teto-de-gelo.svg)
- problemas: nenhum

## p-s2-torres — Torres geladas

- tema torres · padrão torres geladas (vídeo), sem gelo no topo · 70 × 15 células de 4 studs · portas: in (entrada, esquerda, pos 6, largura 5), out (saída, direita, pos 8, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, degelo, andar
- rota mais rápida: 5,5 s (38,9 s esperado), menor janela 0,03 s, manobras: hook+double ×2, hook+momentum ×1
- rota jogador médio: 7 s (10,4 s esperado), menor janela 0,16 s, manobras: double ×2, hook+double ×1
- rota mais segura: 17,1 s (20,5 s esperado), menor janela 0,21 s, manobras: hook ×5, hook+double ×2, hook+momentum ×1, jump ×1, jump+hook ×1, walk ×1
- prévia: [p-s2-torres.svg](./p-s2-torres.svg)
- problemas: nenhum

## p-s3-balanco — Balanço do vale

- tema ventania · padrão original: vão de embalo sobre rota baixa · 90 × 20 células de 4 studs · portas: in (entrada, esquerda, pos 10, largura 5), out (saída, direita, pos 10, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, andar
- rota mais rápida: 8,4 s (11 s esperado), menor janela 0,18 s, manobras: double ×1, hook+double ×2, jump ×1
- rota jogador médio: 9,1 s (10,3 s esperado), menor janela 0,26 s, manobras: double ×2, hook+momentum ×2
- rota mais segura: 11,9 s (13,4 s esperado), menor janela 0,34 s, manobras: double ×3, hook+double ×1, hook+momentum ×1, walk ×1
- prévia: [p-s3-balanco.svg](./p-s3-balanco.svg)
- problemas: nenhum

## p-s3-planicie — Planície do vento

- tema ventania · padrão original: colinas de respiro · 72 × 16 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 6,9 s (8,2 s esperado), menor janela 0,5 s, manobras: double ×1, hook+double ×1, jump ×3
- rota jogador médio: 7,1 s (8,1 s esperado), menor janela 0,52 s, manobras: double ×1, hook+double ×1, jump ×2
- rota mais segura: 6,9 s (8,2 s esperado), menor janela 0,5 s, manobras: double ×1, hook+double ×1, jump ×3
- prévia: [p-s3-planicie.svg](./p-s3-planicie.svg)
- problemas: nenhum

## p-s3-rajada — Rajada

- tema ventania · padrão original: balanço e pouso de precisão · 86 × 18 células de 4 studs · portas: in (entrada, esquerda, pos 7, largura 5), out (saída, direita, pos 7, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 7,8 s (16,8 s esperado), menor janela 0,08 s, manobras: double ×1, hook+double ×2
- rota jogador médio: 9,8 s (14 s esperado), menor janela 0,13 s, manobras: double ×1, hook ×1, hook+double ×2
- rota mais segura: 18,6 s (38,3 s esperado), menor janela 0,05 s, manobras: double ×2, hook ×2, hook+double ×3, jump+hook ×1
- prévia: [p-s3-rajada.svg](./p-s3-rajada.svg)
- problemas:
  - aviso: mecânica exigida 'momentum' não foi usada por nenhuma rota do validador (dá para passar sem ela)

## p-s3-verde — Ponte dos verdes

- tema ventania · padrão original: corrente de gancho único sobre o vermelho · 72 × 18 células de 4 studs · portas: in (entrada, esquerda, pos 7, largura 5), out (saída, direita, pos 7, largura 5) · fecha trecho temático (checkpoint depois)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, gancho único (verde), pulo, embalo do gancho, andar
- rota mais rápida: 6,1 s (28,4 s esperado), menor janela 0,05 s, manobras: hook+double ×2, jump ×1
- rota jogador médio: 7,8 s (21,5 s esperado), menor janela 0,05 s, manobras: hook+double ×1, hook+momentum ×1
- rota mais segura: 7,7 s (21,7 s esperado), menor janela 0,05 s, manobras: hook+double ×1, hook+momentum ×1, jump ×1
- prévia: [p-s3-verde.svg](./p-s3-verde.svg)
- problemas: nenhum

## p-s4-dica — Galeria do teto falso

- tema portas · padrão dica negativa (vídeo) sobre o vermelho · 80 × 15 células de 4 studs · portas: in (entrada, esquerda, pos 6, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, andar
- rota mais rápida: 6,3 s (13,7 s esperado), menor janela 0,08 s, manobras: hook+double ×3
- rota jogador médio: 6,7 s (9 s esperado), menor janela 0,17 s, manobras: hook+double ×3
- rota mais segura: 13,6 s (16,4 s esperado), menor janela 0,17 s, manobras: hook ×2, hook+double ×2, hook+momentum ×1, jump ×1
- prévia: [p-s4-dica.svg](./p-s4-dica.svg)
- problemas: nenhum

## p-s4-portas — Casa das portas

- tema portas · padrão portas de parede (vídeo) · 90 × 16 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 3, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 12,4 s (18,6 s esperado), menor janela 0,13 s, manobras: double ×7, walk ×2
- rota jogador médio: 12,7 s (17 s esperado), menor janela 0,17 s, manobras: double ×7, walk ×3
- rota mais segura: 15,3 s (20 s esperado), menor janela 0,17 s, manobras: double ×7, jump ×2, walk ×4
- prévia: [p-s4-portas.svg](./p-s4-portas.svg)
- problemas: nenhum

## p-s4-saguao — Saguão das portas

- tema portas · padrão portas de parede (vídeo), versão andando · 68 × 14 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 5, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 7,3 s (8,8 s esperado), menor janela 0,5 s, manobras: jump ×5, walk ×1
- rota jogador médio: 7,6 s (8,6 s esperado), menor janela 0,62 s, manobras: double ×1, jump ×3
- rota mais segura: 7,3 s (8,8 s esperado), menor janela 0,5 s, manobras: jump ×5, walk ×1
- prévia: [p-s4-saguao.svg](./p-s4-saguao.svg)
- problemas: nenhum

## p-s4-sala-um-ponto — Sala de um ponto só

- tema portas · padrão sala de um ponto só (vídeo), solo · 86 × 22 células de 4 studs · portas: in (entrada, esquerda, pos 5, largura 5), out (saída, direita, pos 13, largura 5) · fecha trecho temático (checkpoint depois)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 8,4 s (10,6 s esperado), menor janela 0,18 s, manobras: hook+double ×2, jump ×1
- rota jogador médio: 8,6 s (10,5 s esperado), menor janela 0,18 s, manobras: hook+double ×2
- rota mais segura: 8,4 s (10,6 s esperado), menor janela 0,18 s, manobras: hook+double ×2, jump ×1
- prévia: [p-s4-sala-um-ponto.svg](./p-s4-sala-um-ponto.svg)
- problemas: nenhum

## p-s4-valvulas — Válvulas

- tema portas · padrão original: corredores paralelos com mão única · 80 × 17 células de 4 studs · portas: in (entrada, esquerda, pos 9, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, mão única, andar
- rota mais rápida: 6,8 s (16,7 s esperado), menor janela 0,08 s, manobras: hook+double ×2, jump ×1
- rota jogador médio: 7,8 s (9,6 s esperado), menor janela 0,21 s, manobras: double ×1, hook+double ×1, hook+momentum ×1, jump ×1, jump+hook ×1
- rota mais segura: 8,7 s (10,4 s esperado), menor janela 0,26 s, manobras: double ×1, hook ×1, hook+double ×1, hook+momentum ×1, jump ×1, jump+hook ×1
- prévia: [p-s4-valvulas.svg](./p-s4-valvulas.svg)
- problemas: nenhum

## p-s5-chamine — Chaminés gêmeas

- tema poco · padrão chaminé / poço (vídeo) · 32 × 34 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 28, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 8,9 s (20 s esperado), menor janela 0,07 s, manobras: hook+double ×2, jump+hook ×2
- rota jogador médio: 10,2 s (13,4 s esperado), menor janela 0,17 s, manobras: hook ×1, hook+double ×2, jump+hook ×1
- rota mais segura: 16,3 s (24,2 s esperado), menor janela 0,18 s, manobras: double ×12
- prévia: [p-s5-chamine.svg](./p-s5-chamine.svg)
- problemas: nenhum

## p-s5-descida — Descida das cortinas

- tema poco · padrão original: escada de descida com cortinas · 70 × 26 células de 4 studs · portas: in (entrada, esquerda, pos 20, largura 5), out (saída, direita, pos 0, largura 5)
- mecânicas usadas pelas rotas do validador: pulo, andar
- rota mais rápida: 8 s (9,5 s esperado), menor janela 0,42 s, manobras: jump ×2, walk ×4
- rota jogador médio: 8 s (9,5 s esperado), menor janela 0,42 s, manobras: jump ×2, walk ×4
- rota mais segura: 8,1 s (9,6 s esperado), menor janela 0,66 s, manobras: jump ×1, walk ×5
- prévia: [p-s5-descida.svg](./p-s5-descida.svg)
- problemas:
  - erro: porta out (direita) sem chão (a célula (69, -1) tem de ser sólida)

## p-s5-furo — Furo que troca de lado

- tema poco · padrão furo que troca de lado (vídeo) · 26 × 42 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 3), out (saída, direita, pos 33, largura 5) · fecha trecho temático (checkpoint depois)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 21,7 s (28,1 s esperado), menor janela 0,18 s, manobras: double ×13, jump ×2
- rota jogador médio: 21,8 s (27,9 s esperado), menor janela 0,18 s, manobras: double ×13, jump ×1
- rota mais segura: 22,4 s (28,5 s esperado), menor janela 0,21 s, manobras: double ×13, jump ×2
- prévia: [p-s5-furo.svg](./p-s5-furo.svg)
- problemas: nenhum

## p-s5-ilhas — Ilhas suspensas

- tema poco · padrão campo de ilhas flutuantes (vídeo), sem freeze · 72 × 18 células de 4 studs · portas: in (entrada, esquerda, pos 6, largura 5), out (saída, direita, pos 6, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 6,3 s (8 s esperado), menor janela 0,18 s, manobras: hook+double ×2, jump ×1
- rota jogador médio: 6,5 s (7,4 s esperado), menor janela 0,25 s, manobras: hook+double ×2
- rota mais segura: 8,2 s (9,5 s esperado), menor janela 0,37 s, manobras: double ×3, hook+double ×1, jump ×1
- prévia: [p-s5-ilhas.svg](./p-s5-ilhas.svg)
- problemas: nenhum

## p-s6-gaiola — Gaiola

- tema cume · padrão original: gancho através da grade · 92 × 18 células de 4 studs · portas: in (entrada, esquerda, pos 4, largura 5), out (saída, direita, pos 4, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, andar
- rota mais rápida: 8,1 s (16,1 s esperado), menor janela 0,11 s, manobras: hook+double ×2, hook+momentum ×3, jump+hook ×1
- rota jogador médio: 10,1 s (22,6 s esperado), menor janela 0,05 s, manobras: hook+double ×2, hook+momentum ×2, jump+hook ×2
- rota mais segura: 10,8 s (23,3 s esperado), menor janela 0,05 s, manobras: double ×1, hook ×1, hook+double ×2, hook+momentum ×1, jump+hook ×2
- prévia: [p-s6-gaiola.svg](./p-s6-gaiola.svg)
- problemas: nenhum

## p-s6-mirante — Mirante

- tema cume · padrão original: respiro antes do final · 64 × 14 células de 4 studs · portas: in (entrada, esquerda, pos 1, largura 5), out (saída, direita, pos 5, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, pulo, andar
- rota mais rápida: 7,3 s (8,8 s esperado), menor janela 0,37 s, manobras: double ×3, jump ×2, walk ×1
- rota jogador médio: 7,6 s (8,4 s esperado), menor janela 0,37 s, manobras: double ×2, jump ×1
- rota mais segura: 7,3 s (8,8 s esperado), menor janela 0,55 s, manobras: double ×2, jump ×2, walk ×2
- prévia: [p-s6-mirante.svg](./p-s6-mirante.svg)
- problemas: nenhum

## p-s6-ponte — Ponte do cume

- tema cume · padrão original: corrente de gancho com verde, vermelho e gelo · 72 × 20 células de 4 studs · portas: in (entrada, esquerda, pos 8, largura 5), out (saída, direita, pos 8, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, andar
- rota mais rápida: 6,4 s (21,2 s esperado), menor janela 0,05 s, manobras: hook+double ×2
- rota jogador médio: 6,6 s (21 s esperado), menor janela 0,05 s, manobras: hook+double ×2
- rota mais segura: 6,7 s (21,3 s esperado), menor janela 0,05 s, manobras: double ×1, hook+double ×2
- prévia: [p-s6-ponte.svg](./p-s6-ponte.svg)
- problemas: nenhum

## p-s6-reta — Reta final

- tema cume · padrão original: bifurcação de chegada · 76 × 18 células de 4 studs · portas: in (entrada, esquerda, pos 9, largura 5), out (saída, direita, pos 9, largura 5)
- mecânicas usadas pelas rotas do validador: pulo duplo, gancho, pulo, embalo do gancho, andar
- rota mais rápida: 7,1 s (8,2 s esperado), menor janela 0,26 s, manobras: double ×1, hook+double ×1, hook+momentum ×1, jump ×1
- rota jogador médio: 7,1 s (8 s esperado), menor janela 0,26 s, manobras: double ×1, hook+double ×1, hook+momentum ×1
- rota mais segura: 7,9 s (9,2 s esperado), menor janela 0,37 s, manobras: hook+double ×1, hook+momentum ×2, jump ×1, walk ×1
- prévia: [p-s6-reta.svg](./p-s6-reta.svg)
- problemas: nenhum
