# Mapa montado — Mapa novo (proposta A)

Gerado por `python -I -X utf8 tools/mapkit/assemble.py maps/proposta-a/plano.json` (ADR 0052, etapa 4). **Proposta**: o mapa só entra no jogo depois de o dono aprovar (ADR 0055).

- Tamanho: 582 × 604 células de 2 studs (1164 × 1208 studs); bloco = 2 células (4 studs).
- Peças: 26 trechos, 1 largada, 9 curva, 5 checkpoint, 1 degraus, 1 chegada.
- Prévia: [mapa.svg](mapa.svg) (rótulos) e [mapa.png](mapa.png); relatório completo do validador: [validacao.md](validacao.md).
- Checkpoints: elemento `Checkpoint` (fora do MapBuilder por enquanto) com `Order`, `Split = true` (marca de tempo parcial), `Section` e `Name`; o plugin pula ao importar e avisa.

## Resumo

- **Dá para terminar sozinho?** sim — o validador joga com 1 jogador (rápido, 133 s, 58545 simulações).
- **Tempo:** mais rápida 4 min 42 s; jogador médio 7 min 10 s (alvo ~8 min 00 s).
- Ilhas (plataformas não alcançadas): 27; armadilhas (não levam à chegada): 9.

## Seções (tempo parcial em cada checkpoint)

| Seção | Tema | Trechos | Rápida | Jogador médio | % do total | Menor janela | Bifurcações | Fáceis | Fim |
|---|---|---|---|---|---|---|---|---|---|
| s1 Vale do Despertar | vale | 4 | 36,4 s | 47,1 s | 11% | 0,18 s | 1 | 1 | CP1 |
| s2 Torres Geladas | torres | 5 | 54,5 s | 1 min 33 s | 22% | 0,07 s | 2 | 1 | CP2 |
| s3 Ventania | ventania | 4 | 44,1 s | 1 min 14 s | 17% | 0,05 s | 1 | 1 | CP3 |
| s4 Casa das Portas | portas | 5 | 47,4 s | 1 min 02 s | 14% | 0,13 s | 1 | 1 | CP4 |
| s5 Poço Fundo | poco | 4 | 57,7 s | 1 min 17 s | 18% | 0,18 s | 2 | 1 | CP5 |
| s6 Cume | cume | 4 | 41,8 s | 1 min 17 s | 18% | 0,05 s | 1 | 1 | chegada |

## Curva de dificuldade (por peça, na ordem da corrida)

Medida = menor janela da rota mais segura dentro da peça (1 = sem precisão, 2 ≥ 0,4 s, 3 = 0,2–0,4 s, 4 = 0,1–0,2 s, 5 < 0,1 s; +1 com 3+ manobras < 0,2 s). Caminhos = faixas que passam sozinhas ou caminhos por plataformas diferentes (piso).

| Peça | Trecho | Ritmo | Alvo | Medida | Curva | Rápida | Menor janela | Caminhos | Manobras (rápida) |
|---|---|---|---|---|---|---|---|---|---|
| S1.1 | p-s1-escadaria | respiro | 2 | 2 | ██ | 6,8 s | 0,55 s | 1 | jump ×4, walk ×1 |
| S1.2 | p-s1-fosso-duplo | amplo | 3 | 3 | ███ | 6,6 s | 0,21 s | 2 | double ×2, jump ×3, walk ×1 |
| S1.3 | p-s1-primeiro-gancho | gargalo | 3 | 4 | ████ | 6 s | 0,18 s | 1 | hook+double ×2, hook+momentum ×1 |
| ~curva-1 | ~curva-1 | — | — | 2 | ██ | 4,5 s | 0,62 s | 1 | hook ×1, hook+double ×2, hook+momentum ×1 |
| S1.4 | p-s1-cortinas ↔ | amplo | 3 | 3 | ███ | 10 s | 0,24 s | 1 | double ×5, jump ×2 |
| S2.1 | p-s2-galeria ↔ | respiro | 2 | 2 | ██ | 6,4 s | 0,62 s | 1 | jump ×3, walk ×1 |
| ~curva-2 | ~curva-2 ↔ | — | — | 2 | ██ | 6,1 s | 0,62 s | 1 | hook ×1, hook+double ×4, hook+momentum ×1 |
| S2.2 | p-s2-teto-de-gelo | apertado | 4 | 4 | ████ | 10,6 s | 0,11 s | 1 | double ×1, jump ×8 |
| S2.3 | p-s2-patamar | amplo | 3 | 3 | ███ | 6,8 s | 0,37 s | 2 | double ×2, jump ×2 |
| S2.4 | p-s2-torres | apertado | 4 | 5 | █████ | 5,6 s | 0,07 s | 2 | hook+double ×1, hook+momentum ×3 |
| ~curva-3 | ~curva-3 | — | — | 2 | ██ | 6,1 s | 0,62 s | 1 | hook ×1, hook+double ×4, hook+momentum ×1 |
| S2.5 | p-s2-brasas ↔ | apertado | 4 | 5 | █████ | 12,9 s | 0,15 s | 1 | hook+momentum ×1, jump ×11 |
| S3.1 | p-s3-planicie ↔ | respiro | 2 | 2 | ██ | 6,8 s | 0,52 s | 1 | double ×1, hook ×1, hook+double ×1, jump ×2 |
| ~curva-4 | ~curva-4 ↔ | — | — | 2 | ██ | 8,2 s | 0,62 s | 1 | hook ×1, hook+double ×8 |
| S3.2 | p-s3-balanco | amplo | 3 | 3 | ███ | 7,7 s | 0,34 s | 2 | double ×1, hook+double ×2, jump ×1 |
| S3.3 | p-s3-rajada | apertado | 4 | 5 | █████ | 6,6 s | 0,05 s | 1 | double ×1, hook+double ×2 |
| ~curva-5 | ~curva-5 | — | — | 2 | ██ | 8,4 s | 0,62 s | 1 | hook ×2, hook+double ×7 |
| S3.4 | p-s3-verde ↔ | gargalo | 4 | 5 | █████ | 6,4 s | 0,05 s | 1 | hook+double ×3 |
| S4.1 | p-s4-saguao ↔ | respiro | 2 | 2 | ██ | 6,3 s | 0,55 s | 1 | double ×1, jump ×3, walk ×1 |
| S4.2 | p-s4-portas ↔ | apertado | 4 | 4 | ████ | 12,4 s | 0,13 s | 1 | double ×7, hook ×1, walk ×2 |
| ~curva-6 | ~curva-6 ↔ | — | — | 2 | ██ | 8,4 s | 0,62 s | 1 | hook ×1, hook+double ×8 |
| S4.3 | p-s4-valvulas | amplo | 3 | 3 | ███ | 6,1 s | 0,21 s | 5 | hook+double ×2, walk ×1 |
| S4.4 | p-s4-dica | gargalo | 4 | 4 | ████ | 5,7 s | 0,17 s | 1 | hook+double ×2, hook+momentum ×1 |
| S4.5 | p-s4-sala-um-ponto | gargalo | 4 | 4 | ████ | 8,5 s | 0,18 s | 1 | hook+double ×2, hook+momentum ×1 |
| ~curva-7 | ~curva-7 | — | — | 2 | ██ | 13,3 s | 0,62 s | 1 | hook ×1, hook+double ×12, hook+momentum ×1 |
| S5.1 | p-s5-descida ↔ | respiro | 2 | 2 | ██ | 8,2 s | 0,52 s | 1 | hook+double ×1, jump ×1, walk ×4 |
| ~degraus-1 | ~degraus-1 ↔ | — | — | 3 | ███ | 1,6 s | 0,34 s | 2 | jump ×1, jump+hook ×1 |
| S5.2 | p-s5-ilhas ↔ | amplo | 3 | 3 | ███ | 5,7 s | 0,37 s | 3 | hook+double ×2, jump ×1 |
| S5.3 | p-s5-chamine ↔ | apertado | 4 | 5 | █████ | 7,9 s | 0,18 s | 2 | hook+double ×2, jump+hook ×2 |
| S5.4 | p-s5-furo ↔ | gargalo | 3 | 3 | ███ | 21 s | 0,21 s | 1 | double ×13, hook+momentum ×1, jump ×1 |
| ~curva-8 | ~curva-8 ↔ | — | — | 2 | ██ | 3,1 s | 0,62 s | 2 | hook ×1, hook+double ×2 |
| S6.1 | p-s6-mirante | respiro | 2 | 2 | ██ | 6,3 s | 0,55 s | 1 | double ×1, jump ×3, walk ×1 |
| S6.2 | p-s6-gaiola | apertado | 4 | 5 | █████ | 8,2 s | 0,05 s | 1 | double ×1, hook+double ×1, hook+momentum ×2, jump+hook ×2 |
| S6.3 | p-s6-ponte | gargalo | 5 | 5 | █████ | 5,8 s | 0,05 s | 1 | hook+double ×2 |
| ~curva-9 | ~curva-9 | — | — | 2 | ██ | 11,5 s | 0,62 s | 1 | hook ×1, hook+double ×10, hook+momentum ×1 |
| S6.4 | p-s6-reta ↔ | amplo | 3 | 3 | ███ | 5,9 s | 0,26 s | 4 | hook+double ×1, hook+momentum ×2 |

## Bifurcações declaradas (faixas) no mapa montado

| Peça | Faixa | Tipo | Passa? | Tempo | Chance sem erro | Menor janela |
|---|---|---|---|---|---|---|
| S1.2 | alto por cima, três pulos duplos | rapida | sim | 6,9 s | 100% | 0,65 s |
| S1.2 | fosso pelo fosso, pulando calombos | segura | sim | 6,6 s | 99% | 0,3 s |
| S2.3 | ponte pela ponte alta | rapida | sim | 6,8 s | 100% | 0,4 s |
| S2.3 | chao pelo chão, pulando calombos | segura | sim | 7,4 s | 98% | 0,3 s |
| S3.2 | balanco um balanço só, por cima | rapida | sim | 7,7 s | 100% | 0,5 s |
| S3.2 | baixo por baixo, a pé | segura | sim | 8,9 s | 100% | 0,4 s |
| S4.3 | cima corredor de cima: gancho no teto sobre o vermelho | rapida | sim | 6,1 s | 96% | 0,25 s |
| S4.3 | baixo corredor de baixo: a pé | segura | sim | 7 s | 100% | 0,5 s |
| S5.2 | ganchos dois balanços por cima, com um poleiro alto | rapida | sim | 5,8 s | 90% | 0,2 s |
| S5.2 | ilhas de ilha em ilha | segura | sim | 7,7 s | 100% | 0,4 s |
| S5.3 | gancho salão da direita, de gancho em gancho | rapida | sim | 7,9 s | 99% | 0,3 s |
| S5.3 | degraus poço da esquerda, de ressalto em ressalto | segura | sim | 12 s | 100% | 0,4 s |
| S6.4 | embalo balanços por cima, com poleiros | rapida | sim | 5,9 s | 87% | 0,2 s |
| S6.4 | chao a pé pelo vale | segura | sim | 8,2 s | 100% | 0,5 s |

## Problemas

- nenhum

## Peças

| Peça | Tipo | Origem | Seção | Células (x, y, l, a) | Entrada | Saída |
|---|---|---|---|---|---|---|
| Largada | largada | ~largada | s1 | 0, 0, 20, 14 | — | b R |
| S1.1 | trecho | p-s1-escadaria | s1 | 20, 0, 144, 24 | in L | out R |
| S1.2 | trecho | p-s1-fosso-duplo | s1 | 164, 0, 132, 28 | in L | out R |
| S1.3 | trecho | p-s1-primeiro-gancho | s1 | 296, 0, 144, 40 | in L | out R |
| ~curva-1 | curva | ~curva-1 | s1 | 440, 26, 20, 38 | bottom L | top L |
| S1.4 | trecho | p-s1-cortinas (espelhado) | s1 | 256, 44, 184, 28 | in R | out L |
| CP1 | checkpoint | ~checkpoint-1 | s1 | 240, 58, 16, 14 | a R | b L |
| S2.1 | trecho | p-s2-galeria (espelhado) | s2 | 100, 58, 140, 28 | in R | out L |
| ~curva-2 | curva | ~curva-2 | s2 | 80, 68, 20, 46 | bottom R | top R |
| S2.2 | trecho | p-s2-teto-de-gelo | s2 | 100, 96, 178, 52 | in L | out R |
| S2.3 | trecho | p-s2-patamar | s2 | 278, 132, 144, 32 | in L | out R |
| S2.4 | trecho | p-s2-torres | s2 | 422, 130, 140, 30 | in L | out R |
| ~curva-3 | curva | ~curva-3 | s2 | 562, 144, 20, 46 | bottom L | top L |
| S2.5 | trecho | p-s2-brasas (espelhado) | s2 | 330, 168, 232, 22 | in R | out L |
| CP2 | checkpoint | ~checkpoint-2 | s2 | 314, 176, 16, 14 | a R | b L |
| S3.1 | trecho | p-s3-planicie (espelhado) | s3 | 170, 176, 144, 32 | in R | out L |
| ~curva-4 | curva | ~curva-4 | s3 | 150, 186, 20, 62 | bottom R | top R |
| S3.2 | trecho | p-s3-balanco | s3 | 170, 216, 180, 40 | in L | out R |
| S3.3 | trecho | p-s3-rajada | s3 | 350, 222, 172, 36 | in L | out R |
| ~curva-5 | curva | ~curva-5 | s3 | 522, 234, 20, 54 | bottom L | top L |
| S3.4 | trecho | p-s3-verde (espelhado) | s3 | 378, 262, 144, 36 | in R | out L |
| CP3 | checkpoint | ~checkpoint-3 | s3 | 362, 274, 16, 14 | a R | b L |
| S4.1 | trecho | p-s4-saguao (espelhado) | s4 | 226, 274, 136, 28 | in R | out L |
| S4.2 | trecho | p-s4-portas (espelhado) | s4 | 46, 282, 180, 32 | in R | out L |
| ~curva-6 | curva | ~curva-6 | s4 | 26, 286, 20, 62 | bottom R | top R |
| S4.3 | trecho | p-s4-valvulas | s4 | 46, 318, 160, 34 | in L | out R |
| S4.4 | trecho | p-s4-dica | s4 | 206, 318, 160, 30 | in L | out R |
| S4.5 | trecho | p-s4-sala-um-ponto | s4 | 366, 320, 172, 44 | in L | out R |
| CP4 | checkpoint | ~checkpoint-4 | s4 | 538, 344, 16, 14 | a L | b R |
| ~curva-7 | curva | ~curva-7 | s5 | 554, 344, 20, 78 | bottom L | top L |
| S5.1 | trecho | p-s5-descida (espelhado) | s5 | 414, 370, 140, 52 | in R | out L |
| ~degraus-1 | degraus | ~degraus-1 | s5 | 366, 368, 48, 24 | low R | high L |
| S5.2 | trecho | p-s5-ilhas (espelhado) | s5 | 222, 368, 144, 36 | in R | out L |
| S5.3 | trecho | p-s5-chamine (espelhado) | s5 | 158, 378, 64, 68 | in R | out L |
| S5.4 | trecho | p-s5-furo (espelhado) | s5 | 106, 432, 52, 84 | in R | out L |
| CP5 | checkpoint | ~checkpoint-5 | s5 | 90, 496, 16, 14 | a R | b L |
| ~curva-8 | curva | ~curva-8 | s6 | 70, 496, 20, 38 | bottom R | top R |
| S6.1 | trecho | p-s6-mirante | s6 | 90, 520, 128, 28 | in L | out R |
| S6.2 | trecho | p-s6-gaiola | s6 | 218, 522, 184, 36 | in L | out R |
| S6.3 | trecho | p-s6-ponte | s6 | 402, 514, 144, 40 | in L | out R |
| ~curva-9 | curva | ~curva-9 | s6 | 546, 528, 20, 70 | bottom L | top L |
| S6.4 | trecho | p-s6-reta (espelhado) | s6 | 394, 568, 152, 36 | in R | out L |
| Chegada | chegada | ~chegada | s6 | 374, 584, 20, 14 | a R | — |
