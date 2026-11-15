# Mapas

Cada mapa é **dado**, não script: um gerador em `tools/` produz o layout e o código que monta o mapa
no Studio. Nenhum script fica dentro do mapa; o comportamento vem de **tags** (CollectionService).

## Mapa atual: `map01-3d` (experimento 3D, ADR 0029 e 0031)

```
tools/stages3d.py        define os 6 estágios (uma função por estágio) e gera os arquivos abaixo
tools/check_map.py       confere por cálculo se cada salto das rotas cabe no pulo padrão
maps/map01-3d/
  layout.json            todas as peças (centro, tamanho, rotação, tipo, tags)
  build.luau             monta Workspace.Maps.Map01 no Studio (apaga e recria)
  map01-3d.svg           vista de cima + perfil de altura
```

Fluxo:

1. Edite a função do estágio em `tools/stages3d.py`.
2. `python tools/stages3d.py` e depois `python tools/check_map.py` (tem de dar 0 problemas; se o
   estágio ganhou peças novas na rota, atualize `ROUTES` no `check_map.py`).
3. Rode o `build.luau` no Studio (MCP `execute_luau`, modo Edit, ou barra de comandos).
4. Jogue o estágio e salve o place (`place/RaceAndEscape.rbxl`).

Convenções de um estágio ("prefab"):

- 96 studs de comprimento no eixo **+X**; entrada em `x = 0`, saída em `x = 96`; largura 24 (Z de -12 a 12).
- Plataforma de entrada e de saída com 12 de comprimento. A saída pode ficar mais alta que a entrada.
- Tipos de peça (`Kind`): `solid` cinza, `shortcut` azul (atalho), `checkpoint` dourado (tag
  `Checkpoint` + atributo `Order`), `finish` branco (tag `RaceFinish`), `start` verde (lobby).
- O jogador renasce em cima do checkpoint olhando para o +X da peça.

## Regras de medida (pulo padrão: JumpHeight 7,2 e WalkSpeed 16)

- Alcance de um pulo: ~8,6 studs no mesmo nível, ~7,6 subindo 3.
- Usado no mapa: vão de até **5** no mesmo nível; subida de **3** com vão de até **4,5**.
- Passagem por baixo de algo: pelo menos **7** de altura e **4** de largura.
- Cair abaixo de `killHeight` mata; o jogador volta ao último checkpoint.
- Estas medidas valem para a velocidade padrão. Se o atributo de velocidade entrar (Q28), mudam.

## Mapa antigo: `map01` (2.5D)

`maps/map01/` + `tools/mapgen.py`: greybox lateral da fase 2.5D (ADR 0011). Só serve com
`Config.Camera.Mode = "SideView"`. Ver Q29.
