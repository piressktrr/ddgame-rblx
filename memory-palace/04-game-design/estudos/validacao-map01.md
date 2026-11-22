# Validação do mapa Map01 (gerado)

> **Arquivo gerado** por `tools/mapkit/validate.py` (ADR 0052, etapa 3). Não edite à mão: rode de novo.
> Comando: `python -I -X utf8 tools/mapkit/validate.py maps/map01/tiles.json --quick` · modo rápido (--quick) · 3 min 07 s de execução.
> Simulação: 91660 manobras simuladas, 278 plataformas alcançadas, 595 pontos pendurados, 18509 ligações (arestas). Desenho: [validacao-map01.svg](validacao-map01.svg).

O validador "joga" o mapa sozinho: de cada ponto onde dá para ficar em pé (ou pendurado), testa um conjunto
de manobras com o simulador do movimento (`tools/mapkit/physics.py`, números do `Config.luau`) e anota aonde
cada uma leva, quanto tempo leva e **quanta folga** ela tem (a *janela de acerto*: quanto dá para errar o
momento de pular/soltar/onde pular e ainda dar certo). Leia as [limitações](#limitações) antes de decidir.

## Resumo

1. **O mapa se completa** sozinho na simulação: spawn → checkpoint 1 → checkpoint 2 → chegada. 278 de 290 plataformas foram alcançadas.
2. **Tempo:** rota mais rápida (entrada perfeita) 2 min 00 s; jogador médio (erra e refaz) ≈ 8 min 10 s na rota que ele escolheria.
3. **Gancho em quase tudo:** na rota mais rápida, 73 de 83 manobras (88%) usam o gancho e 10 são só pulo/andar. Terminar **sem gancho**: não dá. **Só com gancho, sem apertar pulo**: não dá (o pulo é o ajudante do gancho: sair do chão, pulo duplo depois de soltar).
4. **Mecânicas que sobram:** 7 de 9 estágios passam sem pulo duplo (E1, E3, E4, E6, E7, E8, E9) e 7 sem embalo de gancho (E1, E3, E4, E6, E7, E8, E9). Nenhum estágio exige martelo nem parceiro (o simulador não tem).
5. **Bifurcações:** só 4 de 9 estágios têm um 2º caminho por plataformas diferentes (E3, E4, E7, E8); E1, E2, E5, E6, E9 têm um caminho só (o rascunho previa 2–3 rotas por estágio).
6. **Desafio:** na rota do jogador médio, 16 de 98 manobras têm janela de acerto < 0,1 s (muito difíceis) e 34 têm ≥ 0,4 s (fáceis); o jogador médio erra ≈ 47 vezes no mapa (o maior peso vem das manobras de poucos quadros).
7. **Alturas:** 3 quedas às cegas na rota do jogador médio (destino mais de 20,8 studs abaixo dos pés, fora da tela ao sair); 6 degraus entre plataformas (até 60 studs) passam de 24 studs e só sobem com gancho; 18 são de pulo/pulo duplo.
8. **Pontos de gancho:** dos 171 pontos de gancho de propósito (verdes, soltos, nível 2), 166 são usados, 1 alcançáveis mas nunca usados, 0 só alcançáveis fora da tela e 4 fora do alcance.
9. **Ilhas e armadilhas:** 12 plataformas da área jogável nunca foram alcançadas; 4 alcançadas não levam à chegada (só se sai morrendo/recomeçando, ou a saída não foi amostrada).

**Como ler a janela de acerto:** < 0,1 s = muito difícil (poucos quadros); 0,1–0,2 s = difícil; 0,2–0,4 s =
médio; ≥ 0,4 s = fácil; "livre" = sem tempo certo (andar, segurar o gancho). Uma variação "dá certo" se o
jogador não fica mais de 1 s atrás de onde a manobra original o deixaria.

## Tempo estimado

| Rota | Tempo (sem errar) | Tempo esperado do jogador médio | Manobras | Erros esperados do jogador médio |
|---|---|---|---|---|
| mais rápida | 2 min 00 s | 16 min 18 s | 83 | 141 |
| jogador médio | 2 min 53 s | 8 min 10 s | 98 | 47 |
| mais segura | 4 min 35 s | 10 min 28 s | 143 | 48 |

*Mais rápida* = menor tempo com entrada perfeita. *Jogador médio* = rota que minimiza o tempo esperado de quem
erra o tempo das teclas com desvio de 60 ms, pensa 0,25 s antes de cada manobra
e perde 4 s a cada erro. *Mais segura* = a que maximiza a chance de não errar (o tempo só desempata).

Por trecho:

| Trecho | Mais rápida | Jogador médio (esperado) | Manobras (rápida / médio) |
|---|---|---|---|
| spawn → checkpoint 1 | 32,2 s | 1 min 52 s | 22 / 26 |
| checkpoint 1 → checkpoint 2 | 49,3 s | 3 min 14 s | 31 / 40 |
| checkpoint 2 → chegada | 38,9 s | 3 min 04 s | 30 / 32 |

## Alcançabilidade

- spawn → checkpoint 1: **alcançável**
- checkpoint 1 → checkpoint 2: **alcançável**
- checkpoint 2 → chegada: **alcançável**
- Plataformas: 291 no mapa, 290 na área jogável (ligadas por ar ao spawn), 278 alcançadas pela simulação.

### Ilhas (12 plataformas nunca alcançadas)

Por estágio: E7 2, E8 3, E9 7.

| Estágio | Plataforma (studs) | Largura |
|---|---|---|
| E9 | x 0..8, chão y 710 | 8 |
| E9 | x 0..8, chão y 740 | 8 |
| E9 | x 0..8, chão y 770 | 8 |
| E9 | x 0..8, chão y 800 | 8 |
| E9 | x 0..8, chão y 830 | 8 |
| E9 | x 0..8, chão y 860 | 8 |
| E8 | x 396..400, chão y 792 | 4 |
| E8 | x 544..548, chão y 792 | 4 |
| E8 | x 692..696, chão y 792 | 4 |
| E9 | x 196..200, chão y 814 | 4 |
| E7 | x 844..848, chão y 910 | 4 |
| E7 | x 874..878, chão y 930 | 4 |

Ilha pode ser decoração (topo de pilar, borda de rocha) ou um lugar que o dono queria acessível. Pode também
ser alcançável com uma manobra que o validador não testa (gancho em parceiro, martelo, 2 ganchos no ar).

### Armadilhas (4 plataformas alcançadas de onde não se chega à chegada)

| Estágio | Plataforma (studs) |
|---|---|
| E8 | x 376..396, chão y 566 |
| E8 | x 454..458, chão y 714 |
| E8 | x 458..464, chão y 680 |
| E8 | x 526..546, chão y 566 |

Sozinho, quem cai aqui só sai morrendo (Kill) ou recomeçando. Com parceiro pode haver saída (puxão).

## Tipos de manobra ("só gancho"?)

| Manobra | mais rápida | jogador médio | mais segura |
|---|---|---|---|
| andar/cair | 1 (1%) | 1 (1%) | 4 (3%) |
| pulo | 4 (5%) | 4 (4%) | 0 (0%) |
| pulo duplo | 5 (6%) | 8 (8%) | 6 (4%) |
| gancho | 6 (7%) | 28 (29%) | 81 (57%) |
| pulo + gancho | 14 (17%) | 12 (12%) | 19 (13%) |
| gancho + embalo | 23 (28%) | 20 (20%) | 13 (9%) |
| gancho + pulo duplo | 30 (36%) | 25 (26%) | 20 (14%) |

Dá para terminar o mapa inteiro…

- **só gancho (sem pulo nenhum)**: não
- **sem gancho**: não
- **sem pulo duplo**: não
- **sem embalo**: não

Por estágio (cruzando o estágio do ponto onde a rota mais rápida entra até onde sai; "não" = não passa):

| Estágio | Tempo | Manobras na rota | só gancho (sem pulo nenhum) | sem gancho | sem pulo duplo | sem embalo |
|---|---|---|---|---|---|---|
| E1 (Clareira dos Troncos) | 9,6 s | gancho + pulo duplo 5, pulo duplo 1 | não | não | sim | sim |
| E2 (Copa e Raízes) | 15,2 s | gancho + pulo duplo 6, gancho + embalo 2, pulo + gancho 1, gancho 1 | não | não | não | não |
| R2 (respiro) | 1,6 s | gancho + pulo duplo 1 | sim | não | sim | sim (3,4 s) |
| E3 (Garganta Gelada) | 6,9 s | gancho + pulo duplo 3, gancho + embalo 2, andar/cair 1 | sim | não | sim | sim (9,7 s) |
| R3 (respiro) | 1,1 s | gancho + pulo duplo 1 | sim (2 s) | sim (1,9 s) | sim | sim (1,9 s) |
| E4 (Escombros Flutuantes) | 10,4 s | gancho + embalo 5, gancho + pulo duplo 2, pulo duplo 1, gancho 1 | não | não | sim | sim |
| E5 (Torre Partida) | 25,5 s | gancho + embalo 6, pulo + gancho 3, gancho 3, gancho + pulo duplo 1 | não | não | não | não |
| R5 (respiro) | 1,9 s | pulo duplo 1 | não | sim | sim (3,6 s) | sim |
| E6 (Pontes Quebradas) | 10,2 s | gancho + pulo duplo 4, gancho + embalo 2, pulo duplo 1 | não | sim (14,2 s) | sim | sim |
| R6 (respiro) | 0,9 s | gancho + pulo duplo 1 | sim (2,7 s) | sim | sim (1,7 s) | sim |
| E7 (Galeria dos Cristais) | 6,9 s | gancho + embalo 4, gancho + pulo duplo 3 | não | sim (10,3 s) | sim | sim |
| R7 (respiro) | 1,7 s | gancho 1 | sim | sim | sim | sim |
| E8 (Coração da Montanha) | 12,8 s | pulo + gancho 4, pulo 4, pulo duplo 1, gancho + embalo 1, gancho + pulo duplo 1 | não | não | sim | sim |
| E9 (Torre do Mago) | 15,6 s | pulo + gancho 6, gancho + pulo duplo 2, gancho + embalo 1 | não | não | sim | sim (20,8 s) |

"sim" sozinho = passa sem perder quase nada (até 30% mais lento); "sim (tempo)" = passa, mas mais devagar.
Onde "sem pulo duplo" ou "sem embalo" dá "sim", aquela mecânica **nunca é necessária** no estágio.

## Bifurcações

Caminhos por plataformas diferentes entre a entrada e a saída de cada estágio (o validador acha o mais rápido,
proíbe as plataformas do meio dele e procura outro). "Afastamento" = distância média (studs) do caminho até o
primeiro; abaixo de ~12 é praticamente o mesmo caminho por outro degrau.

| Estágio | Previstas no rascunho | Caminhos achados | Diferentes de verdade (afastamento ≥ 12) | Tempos | Menor janela de cada |
|---|---|---|---|---|---|
| E1 (Clareira dos Troncos) | 2 | 1 | 1 | 9,6 s | 0,03 s |
| E2 (Copa e Raízes) | 3 | 1 | 1 | 15,2 s | 0,02 s |
| E3 (Garganta Gelada) | 2 | 4 | 4 | 6,9 s / 9 s / 10,6 s / 13,6 s | 0,03 s / 0,07 s / 0,15 s / 0,1 s |
| E4 (Escombros Flutuantes) | 2 | 2 | 2 | 10,4 s / 12,8 s | 0,02 s / 0,05 s |
| E5 (Torre Partida) | 3 | 1 | 1 | 25,5 s | 0,03 s |
| E6 (Pontes Quebradas) | 2 | 1 | 1 | 10,2 s | 0,02 s |
| E7 (Galeria dos Cristais) | 2 | 2 | 2 | 6,9 s / 7,9 s | 0,03 s / 0,05 s |
| E8 (Coração da Montanha) | 3 | 2 | 2 | 12,8 s / 44,2 s | 0,02 s / 0,05 s |
| E9 (Torre do Mago) | 3 | 1 | 1 | 15,6 s | 0,02 s |

## Desafio

Rota do jogador médio, por estágio (janela = folga da manobra mais apertada; refinada quadro a quadro):

| Estágio | Manobras | Menor janela | Muito difíceis (< 0,1 s) | Fáceis (≥ 0,4 s) | Classe |
|---|---|---|---|---|---|
| E1 (Clareira dos Troncos) | 7 | 0,08 s | 1 | 0 | muito difícil |
| E2 (Copa e Raízes) | 13 | 0,05 s | 1 | 6 | muito difícil |
| R2 (respiro) | 1 | 0,03 s | 1 | 0 | muito difícil |
| E3 (Garganta Gelada) | 6 | 0,05 s | 1 | 3 | muito difícil |
| R3 (respiro) | 1 | 0,37 s | 0 | 0 | médio |
| E4 (Escombros Flutuantes) | 9 | 0,03 s | 2 | 2 | muito difícil |
| E5 (Torre Partida) | 21 | 0,03 s | 4 | 14 | muito difícil |
| R5 (respiro) | 1 | 0,42 s | 0 | 1 | fácil |
| E6 (Pontes Quebradas) | 8 | 0,22 s | 0 | 1 | médio |
| R6 (respiro) | 1 | 0,12 s | 0 | 0 | difícil |
| E7 (Galeria dos Cristais) | 6 | 0,08 s | 1 | 1 | muito difícil |
| R7 (respiro) | 1 | 0,55 s | 0 | 1 | fácil |
| E8 (Coração da Montanha) | 7 | 0,15 s | 0 | 0 | difícil |
| R8 (respiro) | 2 | 0,05 s | 2 | 0 | muito difícil |
| E9 (Torre do Mago) | 14 | 0,03 s | 3 | 5 | muito difícil |

Curva de dificuldade (menor janela por estágio, na ordem da corrida; o ADR 0052 quer alternar difícil e fácil):

```
  E1 █████████████████    0,08 s
  E2 ██████████████████   0,05 s
  R2 ███████████████████  0,03 s
  E3 ██████████████████   0,05 s
  R3 █████                0,37 s
  E4 ███████████████████  0,03 s
  E5 ███████████████████  0,03 s
  R5 ███                  0,42 s
  E6 ███████████          0,22 s
  R6 ███████████████      0,12 s
  E7 █████████████████    0,08 s
  R7 █                    0,55 s
  E8 ██████████████       0,15 s
  R8 ██████████████████   0,05 s
  E9 ███████████████████  0,03 s
```
(barra maior = mais difícil)

Manobras mais apertadas da rota do jogador médio:

| Onde (pés, studs) | Manobra | Janela | O que aperta | Mira (graus) |
|---|---|---|---|---|
| (1879, 628) E5 → (1857, 654) | gancho + embalo | 0,03 s | lugar do pulo | 7 |
| (121, 852) E9 → (73, 888) | gancho + pulo duplo | 0,03 s | lugar do pulo | 2 |
| (881, 230) R2 → (1001, 226) | gancho + pulo duplo | 0,03 s | soltar o gancho | 2 |
| (1587, 362) E4 → (1625, 374) | pulo duplo | 0,03 s | pulo duplo | — |
| (1625, 374) E4 → (1675, 412) | gancho + embalo | 0,03 s | disparar o gancho | 1 |
| (73, 888) E9 → (71, 928) | pulo + gancho | 0,03 s | disparar o gancho | 1 |
| (499, 70) E2 → (461, 106) | gancho + embalo | 0,05 s | lugar do pulo | 18 |
| (1001, 226) E3 → (1083, 250) | gancho + embalo | 0,05 s | lugar do pulo | 7 |
| (1859, 654) E5 → (1857, 693) | pulo + gancho | 0,05 s | lugar do pulo | 7 |
| (229, 762) R8 → (205, 762) | pulo + gancho | 0,05 s | lugar do pulo | 18 |
| (205, 762) R8 → (177, 788) | pulo + gancho | 0,05 s | lugar do pulo | 17 |
| (1823, 530) E5 → (1849, 552) | pulo + gancho | 0,08 s | lugar do pulo | 3 |

Estágios triviais (tudo com janela ≥ 0,4 s): R5, R7.

## Alturas

Degraus (fim de plataforma encostado numa parede de até 60 studs com outra plataforma em cima), pelas regras de `MEDIDAS_DO_MAPA.md`: pulo 16, 2+ ganchos 4, pulo duplo 2, só gancho 2.

| Onde (studs) | Altura | Classe | Subido pelo validador com |
|---|---|---|---|
| (500, 20) E2 | 50 | 2+ ganchos | não subiu daqui |
| (1850, 530) E5 | 50 | 2+ ganchos | não subiu daqui |
| (1856, 706) E5 | 48 | 2+ ganchos | não subiu daqui |
| (322, 46) E1 | 44 | 2+ ganchos | gancho + embalo |
| (1880, 784) E5 | 36 | só gancho | gancho + pulo duplo, gancho + embalo |
| (1856, 550) E5 | 30 | só gancho | não subiu daqui |

**Quedas às cegas** (o destino fica mais de 20,8 studs abaixo dos pés: fora da tela ao sair):

- rota mais rápida: 1: 98 studs em R7
- rota jogador médio: 3: 98 studs em R7; 24 studs em E3; 22 studs em E6
- no mapa todo: 1105 pares de plataformas ligados por uma queda assim (qualquer manobra).

Altura dos pés ao longo da rota do jogador médio, por estágio (mín.–máx., studs):

E1 70–88, E2 70–212, R2 230–230, E3 226–272, R3 270–270, E4 284–444, E5 470–810, R5 820–820, E6 830–862, R6 860–860, E7 842–864, R7 860–860, E8 762–762, R8 762–762, E9 788–1062.

## Alcance do gancho

Pontos de gancho "de propósito": peças HookOnce (verdes), blocos pequenos soltos (até 40 células) e peças com
`RequiresHookLevel`. "Alcançável" = algum ponto alcançado (em pé, no topo do pulo/pulo duplo ou pendurado) vê o
ponto no alcance (40 studs) e na tela (até 35,8 acima e 23,8 abaixo do root).

| Tipo | Usado | Alcançável, não usado | Só fora da tela | Fora do alcance |
|---|---|---|---|---|
| HookOnce | 17 | 1 | 0 | 0 |
| solto | 141 | 0 | 0 | 4 |
| nível 2 | 8 | 0 | 0 | 0 |

| Ponto (centro, studs) | Tipo | Situação | Mais perto que se mira |
|---|---|---|---|
| (456, 740) E8 | HookOnce | alcançável, não usado | 3 studs |
| (876, 928) E7 | solto | fora do alcance | — |
| (386, 643) E8 | solto | fora do alcance | — |
| (536, 643) E8 | solto | fora do alcance | — |
| (686, 643) E8 | solto | fora do alcance | — |

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

