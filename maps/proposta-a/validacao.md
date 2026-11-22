# Validação do mapa Mapa novo (proposta A) (gerado)

> **Arquivo gerado** por `tools/mapkit/validate.py` (ADR 0052, etapa 3). Não edite à mão: rode de novo.
> Comando: `python -I -X utf8 tools/mapkit/validate.py maps/proposta-a/tiles.json --quick` · modo rápido (--quick) · 2 min 13 s de execução.
> Simulação: 58545 manobras simuladas, 422 plataformas alcançadas, 166 pontos pendurados, 12555 ligações (arestas). Desenho: [validacao.svg](validacao.svg).

O validador "joga" o mapa sozinho: de cada ponto onde dá para ficar em pé (ou pendurado), testa um conjunto
de manobras com o simulador do movimento (`tools/mapkit/physics.py`, números do `Config.luau`) e anota aonde
cada uma leva, quanto tempo leva e **quanta folga** ela tem (a *janela de acerto*: quanto dá para errar o
momento de pular/soltar/onde pular e ainda dar certo). Leia as [limitações](#limitações) antes de decidir.

## Resumo

1. **O mapa se completa** sozinho na simulação: spawn → checkpoint 1 → checkpoint 2 → checkpoint 3 → cp4 → cp5 → chegada. 422 de 449 plataformas foram alcançadas.
2. **Tempo:** rota mais rápida (entrada perfeita) 4 min 42 s; jogador médio (erra e refaz) ≈ 7 min 10 s na rota que ele escolheria.
3. **Gancho em quase tudo:** na rota mais rápida, 119 de 213 manobras (56%) usam o gancho e 94 são só pulo/andar. Terminar **sem gancho**: não dá. **Só com gancho, sem apertar pulo**: não dá (o pulo é o ajudante do gancho: sair do chão, pulo duplo depois de soltar).
4. **Desafio:** na rota do jogador médio, 3 de 213 manobras têm janela de acerto < 0,1 s (muito difíceis) e 112 têm ≥ 0,4 s (fáceis); o jogador médio erra ≈ 13 vezes no mapa (o maior peso vem das manobras de poucos quadros).
5. **Alturas:** 1 quedas às cegas na rota do jogador médio (destino mais de 20,8 studs abaixo dos pés, fora da tela ao sair); 64 degraus entre plataformas (até 60 studs) passam de 24 studs e só sobem com gancho; 243 são de pulo/pulo duplo.
6. **Pontos de gancho:** dos 14 pontos de gancho de propósito (verdes, soltos, nível 2), 14 são usados, 0 alcançáveis mas nunca usados, 0 só alcançáveis fora da tela e 0 fora do alcance.
7. **Ilhas e armadilhas:** 27 plataformas da área jogável nunca foram alcançadas; 9 alcançadas não levam à chegada (só se sai morrendo/recomeçando, ou a saída não foi amostrada).

**Como ler a janela de acerto:** < 0,1 s = muito difícil (poucos quadros); 0,1–0,2 s = difícil; 0,2–0,4 s =
médio; ≥ 0,4 s = fácil; "livre" = sem tempo certo (andar, segurar o gancho). Uma variação "dá certo" se o
jogador não fica mais de 1 s atrás de onde a manobra original o deixaria.

## Tempo estimado

| Rota | Tempo (sem errar) | Tempo esperado do jogador médio | Manobras | Erros esperados do jogador médio |
|---|---|---|---|---|
| mais rápida | 4 min 42 s | 50 min 26 s | 213 | 521 |
| jogador médio | 5 min 00 s | 7 min 10 s | 213 | 13 |
| mais segura | 5 min 37 s | 8 min 20 s | 245 | 17 |

*Mais rápida* = menor tempo com entrada perfeita. *Jogador médio* = rota que minimiza o tempo esperado de quem
erra o tempo das teclas com desvio de 60 ms, pensa 0,25 s antes de cada manobra
e perde 4 s a cada erro. *Mais segura* = a que maximiza a chance de não errar (o tempo só desempata).

Por trecho:

| Trecho | Mais rápida | Jogador médio (esperado) | Manobras (rápida / médio) |
|---|---|---|---|
| spawn → checkpoint 1 | 36,4 s | 47,1 s | 26 / 24 |
| checkpoint 1 → checkpoint 2 | 54,5 s | 1 min 33 s | 45 / 46 |
| checkpoint 2 → checkpoint 3 | 44,1 s | 1 min 14 s | 33 / 33 |
| checkpoint 3 → cp4 | 47,4 s | 1 min 02 s | 33 / 34 |
| cp4 → cp5 | 57,7 s | 1 min 17 s | 44 / 45 |
| cp5 → chegada | 41,8 s | 1 min 17 s | 32 / 31 |

## Alcançabilidade

- spawn → checkpoint 1: **alcançável**
- checkpoint 1 → checkpoint 2: **alcançável**
- checkpoint 2 → checkpoint 3: **alcançável**
- checkpoint 3 → cp4: **alcançável**
- cp4 → cp5: **alcançável**
- cp5 → chegada: **alcançável**
- Plataformas: 464 no mapa, 449 na área jogável (ligadas por ar ao spawn), 422 alcançadas pela simulação.

### Ilhas (27 plataformas nunca alcançadas)

Por estágio: Mapa 16, S3.1 1, S3.2 1, S3.3 3, S4.2 1, S4.5 1, S5.2 2, S6.3 2.

| Estágio | Plataforma (studs) | Largura |
|---|---|---|
| Mapa | x 436..804, chão y 1116 | 368 |
| Mapa | x 340..700, chão y 512 | 360 |
| Mapa | x 200..556, chão y 296 | 356 |
| Mapa | x 700..1044, chão y 516 | 344 |
| Mapa | x 40..328, chão y 48 | 288 |
| Mapa | x 592..880, chão y 80 | 288 |
| Mapa | x 556..844, chão y 328 | 288 |
| Mapa | x 804..1092, chão y 1108 | 288 |
| Mapa | x 844..1124, chão y 320 | 280 |
| Mapa | x 328..592, chão y 56 | 264 |
| Mapa | x 180..436, chão y 1096 | 256 |
| Mapa | x 0..40, chão y 28 | 40 |
| Mapa | x 160..200, chão y 228 | 40 |
| Mapa | x 300..340, chão y 496 | 40 |
| Mapa | x 140..180, chão y 1068 | 40 |
| … | mais 12 (menores) | |

Ilha pode ser decoração (topo de pilar, borda de rocha) ou um lugar que o dono queria acessível. Pode também
ser alcançável com uma manobra que o validador não testa (gancho em parceiro, martelo, 2 ganchos no ar).

### Armadilhas (9 plataformas alcançadas de onde não se chega à chegada)

| Estágio | Plataforma (studs) |
|---|---|
| Mapa | x 52..92, chão y 696 |
| Mapa | x 92..412, chão y 704 |
| Mapa | x 200..480, chão y 172 |
| Mapa | x 412..732, chão y 696 |
| Mapa | x 480..880, chão y 144 |
| Mapa | x 732..1076, chão y 728 |
| Mapa | x 880..920, chão y 128 |
| Mapa | x 1076..1108, chão y 716 |
| S6.3 | x 968..972, chão y 1092 |

Sozinho, quem cai aqui só sai morrendo (Kill) ou recomeçando. Com parceiro pode haver saída (puxão).

## Tipos de manobra ("só gancho"?)

| Manobra | mais rápida | jogador médio | mais segura |
|---|---|---|---|
| andar/cair | 12 (6%) | 7 (3%) | 15 (6%) |
| pulo | 46 (22%) | 37 (17%) | 46 (19%) |
| pulo duplo | 36 (17%) | 48 (23%) | 58 (24%) |
| gancho | 13 (6%) | 18 (8%) | 24 (10%) |
| pulo + gancho | 5 (2%) | 4 (2%) | 4 (2%) |
| gancho + embalo | 18 (8%) | 72 (34%) | 69 (28%) |
| gancho + pulo duplo | 83 (39%) | 27 (13%) | 29 (12%) |

Dá para terminar o mapa inteiro…

- **só gancho (sem pulo nenhum)**: não
- **sem gancho**: não
- **sem pulo duplo**: não
- **sem embalo**: não

Por estágio (cruzando o estágio do ponto onde a rota mais rápida entra até onde sai; "não" = não passa):

| Estágio | Tempo | Manobras na rota | só gancho (sem pulo nenhum) | sem gancho | sem pulo duplo | sem embalo |
|---|---|---|---|---|---|---|
| Largada | 1,3 s | — | sim | sim | sim | sim |
| S1.1 | 6,8 s | pulo 4, andar/cair 1 | não | sim | sim | sim |
| S1.2 | 6,6 s | pulo 3, pulo duplo 2, andar/cair 1 | não | sim | sim | sim |
| S1.3 | 6 s | gancho + pulo duplo 2, gancho + embalo 1 | sim (8,6 s) | não | sim | não |
| ~curva-1 | 4,5 s | gancho + pulo duplo 2, gancho + embalo 1, gancho 1 | sim | sim | sim | sim |
| S1.4 | 10 s | pulo duplo 5, pulo 2 | não | sim | não | sim |
| CP1 | 1,1 s | gancho + embalo 1 | não | sim | sim | sim |
| S2.1 | 6,4 s | pulo 3, andar/cair 1 | não | sim | sim | sim |
| ~curva-2 | 6,1 s | gancho + pulo duplo 4, gancho + embalo 1, gancho 1 | sim | sim | sim | sim |
| S2.2 | 10,6 s | pulo 8, pulo duplo 1 | não | sim | sim | sim |
| S2.3 | 6,8 s | pulo duplo 2, pulo 2 | não | sim | sim | sim |
| S2.4 | 5,6 s | gancho + embalo 3, gancho + pulo duplo 1 | sim | sim (7,8 s) | sim | sim |
| ~curva-3 | 6,1 s | gancho + pulo duplo 4, gancho + embalo 1, gancho 1 | sim | sim | sim | sim |
| S2.5 | 12,9 s | pulo 11, gancho + embalo 1 | não | sim | sim | sim |
| S3.1 | 6,8 s | pulo 2, pulo duplo 1, gancho + pulo duplo 1, gancho 1 | não | sim (9,4 s) | sim | sim |
| ~curva-4 | 8,2 s | gancho + pulo duplo 8, gancho 1 | sim | sim | sim | sim |
| S3.2 | 7,7 s | gancho + pulo duplo 2, pulo 1, pulo duplo 1 | não | sim | sim | sim |
| S3.3 | 6,6 s | gancho + pulo duplo 2, pulo duplo 1 | não | não | sim (9,4 s) | sim (9,8 s) |
| ~curva-5 | 8,4 s | gancho + pulo duplo 7, gancho 2 | sim | sim | sim | sim |
| S3.4 | 6,4 s | gancho + pulo duplo 3 | não | não | não | sim (16,4 s) |
| S4.1 | 6,3 s | pulo 3, andar/cair 1, pulo duplo 1 | não | sim | sim | sim |
| S4.2 | 12,4 s | pulo duplo 7, andar/cair 2, gancho 1 | não | sim | não | sim |
| ~curva-6 | 8,4 s | gancho + pulo duplo 8, gancho 1 | sim | sim | sim | sim |
| S4.3 | 6,1 s | gancho + pulo duplo 2, andar/cair 1 | sim | sim (8,6 s) | sim | sim |
| S4.4 | 5,7 s | gancho + pulo duplo 2, gancho + embalo 1 | não | não | sim (11,1 s) | não |
| S4.5 | 8,5 s | gancho + pulo duplo 2, gancho + embalo 1 | não | não | não | não |
| ~curva-7 | 13,3 s | gancho + pulo duplo 12, gancho + embalo 1, gancho 1 | sim | sim | sim | sim |
| S5.1 | 8,2 s | andar/cair 4, pulo 1, gancho + pulo duplo 1 | não | sim | sim | sim |
| ~degraus-1 | 1,6 s | pulo + gancho 1, pulo 1 | não | sim | sim | sim |
| S5.2 | 5,7 s | gancho + pulo duplo 2, pulo 1 | não | sim | não | sim |
| S5.3 | 7,9 s | pulo + gancho 2, gancho + pulo duplo 2 | não | sim (12 s) | não | sim (10,8 s) |
| S5.4 | 21 s | pulo duplo 13, pulo 1, gancho + embalo 1 | não | sim | não | sim |
| CP5 | 0,9 s | gancho 1 | sim | sim (2,7 s) | sim | sim |
| ~curva-8 | 3,1 s | gancho + pulo duplo 2, gancho 1 | sim | sim | sim | sim |
| S6.1 | 6,3 s | pulo 3, pulo duplo 1, andar/cair 1 | não | sim | sim | sim |
| S6.2 | 8,2 s | gancho + embalo 2, pulo + gancho 2, pulo duplo 1, gancho + pulo duplo 1 | não | não | sim | sim |
| S6.3 | 5,8 s | gancho + pulo duplo 2 | não | não | não | não |
| ~curva-9 | 11,5 s | gancho + pulo duplo 10, gancho + embalo 1, gancho 1 | sim | sim | sim | sim |
| S6.4 | 5,9 s | gancho + embalo 2, gancho + pulo duplo 1 | não | sim | sim | sim |
| Chegada | 0 s | — | não | não | não | não |

"sim" sozinho = passa sem perder quase nada (até 30% mais lento); "sim (tempo)" = passa, mas mais devagar.
Onde "sem pulo duplo" ou "sem embalo" dá "sim", aquela mecânica **nunca é necessária** no estágio.

## Bifurcações

Caminhos por plataformas diferentes entre a entrada e a saída de cada estágio (o validador acha o mais rápido,
proíbe as plataformas do meio dele e procura outro). "Afastamento" = distância média (studs) do caminho até o
primeiro; abaixo de ~12 é praticamente o mesmo caminho por outro degrau.

| Estágio | Previstas no rascunho | Caminhos achados | Diferentes de verdade (afastamento ≥ 12) | Tempos | Menor janela de cada |
|---|---|---|---|---|---|

## Desafio

Rota do jogador médio, por estágio (janela = folga da manobra mais apertada; refinada quadro a quadro):

| Estágio | Manobras | Menor janela | Muito difíceis (< 0,1 s) | Fáceis (≥ 0,4 s) | Classe |
|---|---|---|---|---|---|
| Largada | 0 | livre | 0 | 0 | — |
| S1.1 | 4 | 0,62 s | 0 | 4 | fácil |
| S1.2 | 3 | 0,37 s | 0 | 0 | médio |
| S1.3 | 3 | 0,18 s | 0 | 0 | difícil |
| ~curva-1 | 5 | 0,34 s | 0 | 4 | médio |
| S1.4 | 8 | 0,24 s | 0 | 1 | médio |
| CP1 | 1 | 0,32 s | 0 | 0 | médio |
| S2.1 | 3 | 0,37 s | 0 | 2 | médio |
| ~curva-2 | 7 | 0,34 s | 0 | 6 | médio |
| S2.2 | 9 | 0,11 s | 0 | 1 | difícil |
| S2.3 | 4 | 0,37 s | 0 | 3 | médio |
| S2.4 | 4 | 0,13 s | 0 | 0 | difícil |
| ~curva-3 | 7 | 0,34 s | 0 | 6 | médio |
| S2.5 | 12 | 0,15 s | 0 | 1 | difícil |
| S3.1 | 4 | 0,34 s | 0 | 3 | médio |
| ~curva-4 | 9 | 0,62 s | 0 | 9 | fácil |
| S3.2 | 4 | 0,22 s | 0 | 1 | médio |
| S3.3 | 4 | 0,13 s | 0 | 0 | difícil |
| ~curva-5 | 9 | 0,62 s | 0 | 9 | fácil |
| S3.4 | 2 | 0,05 s | 1 | 0 | muito difícil |
| CP3 | 1 | 0,32 s | 0 | 0 | médio |
| S4.1 | 3 | 0,34 s | 0 | 0 | médio |
| S4.2 | 11 | 0,17 s | 0 | 4 | difícil |
| ~curva-6 | 9 | 0,62 s | 0 | 9 | fácil |
| S4.3 | 5 | 0,29 s | 0 | 3 | médio |
| S4.4 | 3 | 0,17 s | 0 | 1 | difícil |
| S4.5 | 3 | 0,18 s | 0 | 0 | difícil |
| ~curva-7 | 15 | 0,34 s | 0 | 14 | médio |
| S5.1 | 6 | 0,45 s | 0 | 6 | fácil |
| ~degraus-1 | 2 | 0,34 s | 0 | 0 | médio |
| S5.2 | 2 | 0,25 s | 0 | 0 | médio |
| S5.3 | 5 | 0,17 s | 0 | 3 | difícil |
| S5.4 | 15 | 0,18 s | 0 | 1 | difícil |
| CP5 | 1 | livre | 0 | 1 | fácil |
| ~curva-8 | 3 | 0,62 s | 0 | 3 | fácil |
| S6.1 | 3 | 0,37 s | 0 | 2 | médio |
| S6.2 | 6 | 0,05 s | 1 | 2 | muito difícil |
| S6.3 | 2 | 0,05 s | 1 | 0 | muito difícil |
| ~curva-9 | 13 | 0,34 s | 0 | 12 | médio |
| S6.4 | 3 | 0,26 s | 0 | 1 | médio |

Curva de dificuldade (menor janela por estágio, na ordem da corrida; o ADR 0052 quer alternar difícil e fácil):

```
Largada █                    livre
S1.1 █                    0,62 s
S1.2 █████                0,37 s
S1.3 █████████████        0,18 s
~curva-1 ██████               0,34 s
S1.4 ███████████          0,24 s
 CP1 ███████              0,32 s
S2.1 █████                0,37 s
~curva-2 ██████               0,34 s
S2.2 ████████████████     0,11 s
S2.3 █████                0,37 s
S2.4 ███████████████      0,13 s
~curva-3 ██████               0,34 s
S2.5 ██████████████       0,15 s
S3.1 ██████               0,34 s
~curva-4 █                    0,62 s
S3.2 ███████████          0,22 s
S3.3 ███████████████      0,13 s
~curva-5 █                    0,62 s
S3.4 ██████████████████   0,05 s
 CP3 ███████              0,32 s
S4.1 ██████               0,34 s
S4.2 █████████████        0,17 s
~curva-6 █                    0,62 s
S4.3 ████████             0,29 s
S4.4 █████████████        0,17 s
S4.5 █████████████        0,18 s
~curva-7 ██████               0,34 s
S5.1 ██                   0,45 s
~degraus-1 ██████               0,34 s
S5.2 ██████████           0,25 s
S5.3 █████████████        0,17 s
S5.4 █████████████        0,18 s
 CP5 █                    livre
~curva-8 █                    0,62 s
S6.1 █████                0,37 s
S6.2 ██████████████████   0,05 s
S6.3 ██████████████████   0,05 s
~curva-9 ██████               0,34 s
S6.4 █████████            0,26 s
```
(barra maior = mais difícil)

Manobras mais apertadas da rota do jogador médio:

| Onde (pés, studs) | Manobra | Janela | O que aperta | Mira (graus) |
|---|---|---|---|---|
| (917, 552) S3.4 → (803, 552) | gancho + pulo duplo | 0,05 s | soltar o gancho | 5 |
| (939, 1060) S6.3 → (1053, 1060) | gancho + pulo duplo | 0,05 s | soltar o gancho | 7 |
| (649, 1060) S6.2 → (703, 1080) | gancho + pulo duplo | 0,05 s | lugar do pulo | 5 |
| (367, 236) S2.2 → (393, 244) | pulo | 0,11 s | lugar do pulo | — |
| (407, 244) S2.2 → (433, 252) | pulo | 0,11 s | lugar do pulo | — |
| (735, 472) S3.3 → (797, 476) | pulo duplo | 0,13 s | lugar do pulo | — |
| (907, 288) S2.4 → (963, 288) | gancho + embalo | 0,13 s | disparar o gancho | 1 |
| (997, 356) S2.5 → (953, 356) | pulo duplo | 0,15 s | pulo duplo | — |
| (925, 356) S2.5 → (881, 356) | pulo duplo | 0,15 s | pulo duplo | — |
| (849, 356) S2.5 → (805, 356) | pulo duplo | 0,15 s | pulo duplo | — |
| (777, 356) S2.5 → (733, 356) | pulo duplo | 0,15 s | pulo duplo | — |
| (1065, 356) S2.5 → (1029, 356) | pulo duplo | 0,16 s | lugar do pulo | — |

Estágios triviais (tudo com janela ≥ 0,4 s): S1.1, ~curva-4, ~curva-5, ~curva-6, S5.1, CP5, ~curva-8.

## Alturas

Degraus (fim de plataforma encostado numa parede de até 60 studs com outra plataforma em cima), pelas regras de `MEDIDAS_DO_MAPA.md`: pulo 163, pulo duplo 80, só gancho 44, 2+ ganchos 20.

| Onde (studs) | Altura | Classe | Subido pelo validador com |
|---|---|---|---|
| (408, 808) S5.3 | 60 | 2+ ganchos | não subiu daqui |
| (312, 980) S5.4 | 52 | 2+ ganchos | não subiu daqui |
| (916, 80) ~curva-1 | 48 | 2+ ganchos | não subiu daqui |
| (196, 156) ~curva-2 | 48 | 2+ ganchos | não subiu daqui |
| (164, 180) ~curva-2 | 48 | 2+ ganchos | não subiu daqui |
| (1128, 308) ~curva-3 | 48 | 2+ ganchos | não subiu daqui |
| (1160, 332) ~curva-3 | 48 | 2+ ganchos | não subiu daqui |
| (336, 424) ~curva-4 | 48 | 2+ ganchos | não subiu daqui |
| (304, 448) ~curva-4 | 48 | 2+ ganchos | não subiu daqui |
| (1048, 504) ~curva-5 | 48 | 2+ ganchos | não subiu daqui |
| (1080, 528) ~curva-5 | 48 | 2+ ganchos | não subiu daqui |
| (88, 624) ~curva-6 | 48 | 2+ ganchos | não subiu daqui |
| (56, 648) ~curva-6 | 48 | 2+ ganchos | não subiu daqui |
| (1112, 772) ~curva-7 | 48 | 2+ ganchos | não subiu daqui |
| (1144, 796) ~curva-7 | 48 | 2+ ganchos | não subiu daqui |

**Quedas às cegas** (o destino fica mais de 20,8 studs abaixo dos pés: fora da tela ao sair):

- rota mais rápida: 0
- rota jogador médio: 1: 24 studs em S4.3
- no mapa todo: 204 pares de plataformas ligados por uma queda assim (qualquer manobra).

Altura dos pés ao longo da rota do jogador médio, por estágio (mín.–máx., studs):

Largada 4–4, S1.1 4–24, S1.2 24–24, S1.3 24–52, ~curva-1 56–104, S1.4 104–120, CP1 120–120, S2.1 124–140, ~curva-2 140–204, S2.2 204–268, S2.3 276–292, S2.4 284–296, ~curva-3 292–356, S2.5 356–356, S3.1 356–376, ~curva-4 392–472, S3.2 468–472, S3.3 472–476, ~curva-5 472–552, S3.4 552–552, CP3 552–552, S4.1 552–568, S4.2 568–584, ~curva-6 592–672, S4.3 640–672, S4.4 660–660, S4.5 660–692, ~curva-7 692–820, S5.1 744–820, ~degraus-1 748–756, S5.2 760–776, S5.3 760–868, S5.4 868–996, CP5 996–996, ~curva-8 1012–1044, S6.1 1044–1060, S6.2 1060–1080, S6.3 1060–1060, ~curva-9 1060–1172, S6.4 1160–1172, Chegada 1172–1172.

## Alcance do gancho

Pontos de gancho "de propósito": peças HookOnce (verdes), blocos pequenos soltos (até 40 células) e peças com
`RequiresHookLevel`. "Alcançável" = algum ponto alcançado (em pé, no topo do pulo/pulo duplo ou pendurado) vê o
ponto no alcance (40 studs) e na tela (até 35,8 acima e 23,8 abaixo do root).

| Tipo | Usado | Alcançável, não usado | Só fora da tela | Fora do alcance |
|---|---|---|---|---|
| HookOnce | 1 | 0 | 0 | 0 |
| solto | 13 | 0 | 0 | 0 |
| nível 2 | 0 | 0 | 0 | 0 |

O nível do gancho (`RequiresHookLevel`) é ignorado pelo simulador: as peças de nível 2 contam como prendíveis.

## Limitações

- **Um jogador só.** Sem gancho em parceiro, martelo, empurrão, modo solo. Gelo (Freeze) conta como fracasso
  (sem parceiro para soltar). Os trechos pensados para a dupla aparecem como difíceis, armadilhas ou ilhas.
- **Amostragem.** Cada ponto testa um conjunto pequeno de manobras (alguns momentos de pulo duplo, alguns
  alvos de gancho por setor de ângulo, soltar em 6 momentos, 1 gancho por manobra ou um
  gancho de cada vez a partir de pendurado). Rotas que precisam de algo fora disso não aparecem: **"não alcançado",
  ilha, armadilha e "não passa sem X" querem dizer "o validador não achou", não "impossível"**. Os tempos são
  um teto (um jogador bom acha atalhos) e as bifurcações, um piso.
- **Janela de acerto** = variação de cada entrada sozinha (as outras fixas), em passos de 1 quadro (tempo), 1 stud
  (lugar) e 1 grau (mira); a janela da manobra é a da entrada mais apertada. Só as manobras das rotas são
  refinadas assim; as outras usam a janela grosseira da família de manobras.
- **Simulador** (ver o topo de `physics.py`): caixa 2 × 5,5 sem atrito, sem subida automática de degrau, mundo
  em grade (rampas viraram degraus de 2 studs), Humanoid com velocidade instantânea. Pousar "com embalo" conta
  como parar no ponto de pouso.
- **Câmera:** "na tela" usa a área visível parada (16:9), sem o adiantamento da câmera nem o atraso na queda.
- **Checkpoint e chegada** contam como no jogo (root na coluna acima da peça, até ZoneHeight); morrer volta ao
  checkpoint, mas o validador não usa isso como atalho.

