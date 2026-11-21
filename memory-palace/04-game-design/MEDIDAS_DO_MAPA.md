# Medidas do mapa (gerado)

> **Arquivo gerado** por `tools/mapkit/metrics.py`. Não edite à mão: mude o `Config.luau`
> ou o simulador e regenere. ADR 0052, etapa 1.
>
> Config: `src/shared/Config.luau` · sha256 `aeacf8308d81d561…` · gancho modo `DDNet`.
> Unidades: studs; **bloco** = `MapElements.DefaultGrid` = 4 studs; **célula** do MapBuilder = 2 studs.

## Como regenerar

Na raiz do repositório:

```
python -I -X utf8 tools/mapkit/metrics.py           # grava maps/metrics.json e este arquivo
python -I -X utf8 tools/mapkit/metrics.py --check   # só confere se estão em dia
python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .
```

Os números saem do simulador (`tools/mapkit/physics.py`), que porta o código do movimento e do
gancho (veja as simplificações no topo dele). Os máximos são **teóricos** (entrada perfeita);
as regras abaixo já têm folga.

## Pulo

| Medida | Valor |
|---|---|
| Altura do pulo (pés) | 11,56 studs · 2,89 blocos · 5,78 células (fórmula JumpPower²/2g: 11,56) |
| Tempo até o topo | 0,45 s |
| Tempo no ar (mesmo nível) | 0,92 s (fórmula: 0,91 s) |
| Altura com pulo duplo no topo | 21,8 studs · 5,45 blocos · 10,9 células (duplo em t = 0,45 s; ganho do duplo 10,24) |
| Tempo no ar com duplo no topo | 1,5 s |

### Vão máximo por desnível (borda a borda, correndo e pulando na borda)

Desnível = altura do lado de chegada menos a do lado de partida (positivo = subindo).
O pulo duplo do alcance máximo é tardio (perto do pouso), não no topo.

| Desnível (studs / blocos) | Só pulo | Pulo + duplo | Duplo em t = |
|---|---|---|---|
| -24 / -6 | 49,4 | 83,9 | 1,08 s |
| -16 / -4 | 45,8 | 79,5 | 1,03 s |
| -12 / -3 | 43,8 | 77,1 | 1 s |
| -8 / -2 | 41,6 | 74,6 | 0,97 s |
| -4 / -1 | 39,2 | 71,8 | 0,93 s |
| 0 / 0 | 36,5 | 68,9 | 0,9 s |
| 4 / 1 | 33,2 | 65,6 | 0,82 s |
| 8 / 2 | 28,8 | 61,1 | 0,7 s |
| 12 / 3 | — | 57,9 | 0,75 s |
| 16 / 4 | — | 52,7 | 0,68 s |
| 20 / 5 | — | 45 | 0,58 s |

## Gancho

| Medida | Valor |
|---|---|
| Alcance (`Hook.Range`, do root) | 40 studs · 10 blocos · 20 células |
| Tempo de voo até o alcance | 0,111 s (FireSpeed 360) |
| Recarga entre prender | 0,1 s |
| Pendurado (segurando) | root 5,88 abaixo do ponto; pés 8,88 abaixo |
| Subida com 1 gancho a 39,5 acima (no alcance) | pés sobem até 50,7 sem duplo · 61 com duplo no topo |
| Subida com 1 gancho a 34 acima (limite da tela) | pés sobem até 45,2 sem duplo · 55,4 com duplo no topo |
| Parede subida com 1 gancho, saindo a 2 do pé dela | até 38 de altura |
| Parede subida com 1 gancho, saindo a 12 do pé dela | até 38 de altura |
| Parede subida com 1 gancho, saindo a 20 do pé dela | até 38 de altura |
| Vão máximo com gancho + soltar + embalo + duplo | 168 studs · 42 blocos · 84 células (ponto a 20°, solta em t = 1,17 s a 72 studs/s) |

As duas "subidas com 1 gancho" usam um ponto solto (sem bloco para o corpo bater): é o teto
otimista de altura. A parede e o vão usam blocos de verdade (o vão: um bloco de gancho a
Range - 1 do jogador no disparo). Paredes ficam limitadas pelo alcance e pela tela, não pela
força do puxão. O embalo segurando D no ar não perde velocidade (o controle do DDNet não corta
velocidade acima do limite), por isso o vão com gancho é bem maior que o do pulo.

## Câmera (16:9) e alvo do gancho na tela

| Medida | Valor |
|---|---|
| Área visível no plano | 106,1 × 59,7 studs (largura × altura) |
| Acima do root | 35,8 studs (`Camera.Height` sobe o centro) |
| Abaixo do root | 23,8 studs |
| Para os lados | 53,1 parado · 59,1 à frente e 47,1 atrás correndo (LookAhead) |
| Altura visível na face da frente dos blocos | 54,1 studs |
| Gancho na tela | até 35,8 acima, 23,8 abaixo, 40 para os lados (alcance 40) |

Para cima o alcance (40) passa da borda da tela: um ponto a 40 bem acima fica fora da tela.

## Queda

Sem dano de queda: nenhum código do jogo tira vida por queda e o Humanoid do Roblox não tem dano de queda. Só matam a zona Kill e cair abaixo do FallenPartsDestroyHeight do place.

| Altura da queda | Velocidade | Tempo | Atraso da câmera | Visível abaixo dos pés |
|---|---|---|---|---|
| 12 | 52 studs/s | 0,46 s | 5,2 | 15,6 |
| 24 | 73,5 studs/s | 0,65 s | 7,3 | 13,5 |
| 40 | 94,9 studs/s | 0,84 s | 9,5 | 11,4 |
| 60 | 116,2 studs/s | 1,03 s | 11,6 | 9,2 |
| 100 | 150 studs/s | 1,33 s | 15 | 5,8 |
| 160 | 189,7 studs/s | 1,69 s | 19 | 1,9 |

## Velocidades (studs/s)

| Andar | Controle no ar (gancho/embalo) | Puxão máx. (DragSpeed) | Limite do balanço | Pulo | Pulo duplo |
|---|---|---|---|---|---|
| 38 | 22 | 68 | 180 | 51 | 48 |

Embalo medido no melhor vão com gancho: até 77,1 studs/s na horizontal.

## Regras de desenho (com folga)

| Regra | Valor | Blocos | Células |
|---|---|---|---|
| Degrau (só pulo, sem gancho): confortável. (`step_jump_comfort`) | <= 8 studs | 2 | 4 |
| Degrau máximo só com pulo (na grade de células; acima disso precisa do pulo duplo). (`step_jump_max`) | <= 10 studs | 2,5 | 5 |
| Degrau com pulo duplo: confortável. (`step_double_jump_comfort`) | <= 16 studs | 4 | 8 |
| Degrau máximo com pulo duplo bem cronometrado (no topo do 1º pulo). (`step_double_jump_max`) | <= 20 studs | 5 | 10 |
| Degrau a partir do qual só se sobe com gancho (impossível com os dois pulos). (`step_needs_hook`) | >= 24 studs | 6 | 12 |
| Vão no mesmo nível só com pulo: confortável (borda a borda). (`gap_jump_comfort`) | <= 24 studs | 6 | 12 |
| Vão no mesmo nível só com pulo: difícil (pular quase na borda). (`gap_jump_max`) | <= 32 studs | 8 | 16 |
| Vão no mesmo nível com pulo duplo: confortável. (`gap_double_jump_comfort`) | <= 48 studs | 12 | 24 |
| Vão no mesmo nível com pulo duplo: difícil (duplo tarde, perto do pouso). (`gap_double_jump_max`) | <= 60 studs | 15 | 30 |
| Vão a partir do qual só se passa com gancho (ou embalo de gancho). (`gap_needs_hook`) | >= 72 studs | 18 | 36 |
| Vão com 1 gancho + embalo + pulo duplo: confortável (metade do máximo medido). (`gap_hook_comfort`) | <= 84 studs | 21 | 42 |
| Parede que se sobe com 1 gancho (prende na face perto do topo e passa por cima). (`wall_one_hook_max`) | <= 32 studs | 8 | 16 |
| Parede mais alta que isto precisa de 2 ganchos (soltar e prender de novo no ar). (`wall_needs_two_hooks`) | > 38 studs | 9,5 | 19 |
| Distância do root até o ponto de gancho (alcance com folga). (`hook_target_distance`) | <= 36 studs | 9 | 18 |
| Ponto de gancho acima do jogador: no máximo isto, para ficar na tela com folga. (`hook_target_up`) | <= 32 studs | 8 | 16 |
| Ponto de gancho abaixo do jogador: no máximo isto (a câmera mostra menos para baixo). (`hook_target_down`) | <= 20 studs | 5 | 10 |
| Espaço horizontal entre pontos de gancho seguidos na mesma altura (pendurado no anterior). (`hook_chain_spacing`) | <= 28 studs | 7 | 14 |
| Altura livre mínima para passar andando (corpo de 5,5). (`ceiling_walk_min`) | >= 8 studs | 2 | 4 |
| Altura livre para pular sem bater a cabeça (pulo inteiro). (`ceiling_jump_free`) | >= 20 studs | 5 | 10 |
| Largura mínima de poço/corredor vertical (corpo de 2; 1 bloco). (`corridor_width_min`) | >= 4 studs | 1 | 2 |
| Largura confortável de poço para subir com gancho/pulos (balanço e erro de mira). (`shaft_width_hook`) | >= 8 studs | 2 | 4 |
| Do ponto de gancho no teto até o chão, para ficar pendurado sem encostar os pés. (`hang_clearance`) | >= 12 studs | 3 | 6 |

Folga: "confortável" = 75% do máximo; "difícil" = 90%; tudo
arredondado para baixo na grade de blocos (para cima nos mínimos).

## Limites do simulador (resumo)

- Um jogador só: sem gancho em jogador, martelo, empurrão nem modo solo.
- Humanoid fora do gancho chega à velocidade de andar na hora, no chão e no ar; sem subida
  automática de degrau baixo (o Humanoid real sobe quinas pequenas) e sem rampas.
- Corpo = caixa 2 × 5,5 sem atrito nem quique; mão única é atravessável; zonas pela grade.
- Prender de novo durante o embalo não devolve o pulo duplo (igual ao jogo hoje: a recarga vem
  da mudança do atributo `HookActive`, que já está ligado no embalo).
- Detalhes no topo de `tools/mapkit/physics.py`.
