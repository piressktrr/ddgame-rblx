# Mapas

Cada mapa é **dado**, não script: um gerador em `tools/` produz o layout e o código que monta o mapa
no Studio. Nenhum script fica dentro do mapa; o comportamento vem de **tags** (CollectionService).

## Mapa atual: `map01` (greybox 2.5D do rascunho v2, ADR 0038, 0039 e 0041)

```
tools/map_layout.py      layout do rascunho v2: ar, sólidos e zonas em studs (fonte única)
tools/map_sketch.py      desenha o rascunho (memory-palace/04-game-design/estudos/mapa-2-5d/)
tools/map2d.py           gera os três arquivos abaixo a partir do layout
maps/map01/
  layout.json            peças: nome, tipo, classe, centro, tamanho, rotZ, tags e atributos
  build.luau             monta Workspace.Maps.Map01 no Studio (apaga e recria)
  map01.svg              o desenho v2 (vista lateral)
```

Fluxo: editar `tools/map_layout.py` → `python tools/map_sketch.py` e `python tools/map2d.py` → rodar
o `build.luau` no Studio (MCP `execute_luau`, modo Edit) → jogar → salvar o place
(`place/RaceAndEscape.rbxl`). `python tools/map2d.py --check arquivo.luau` grava também um script
que confere o mapa montado (contagens por tag, Order, spawn, ar livre, rampas).

Convenções:

- Visto de lado: X horizontal, Y altura. Todo o percurso jogável no plano **Z = 0**; as peças do plano
  têm 12 studs de profundidade (Z de -6 a 6). Atrás, em Z = -10, um fundo escuro sem colisão,
  consulta nem toque (não gruda).
- "Ar" é onde se joga; o resto da caixa do mapa (ar + 10 studs de margem) é **rocha**, juntada em
  poucos retângulos. Bordas inclinadas do ar viram `WedgePart`.
- Tipos de peça (atributo `Kind`) e tags: `Rock` cinza (gruda); `SlopeR`/`SlopeL` rampas de rocha;
  `Kill` vermelho, `KillZone`, sem colisão; `Ice` `FreezeZone`; `Unfreeze` laranja `UnfreezeZone`;
  `NoHook` roxo; `HookOnce` verde; `Checkpoint` dourado, `Checkpoint` + atributo `Order`; `Finish`
  branco, `RaceFinish` + `Checkpoint` (último `Order`); `Spawn` = `SpawnLocation` (Neutral,
  Duration 0, tag `RaceStart`).
- Zonas só ocupam ar (a faixa mortal não passa por baixo de pilares); uma zona apoiada em faixa
  mortal desce até o chão (vira ilha). O tutorial do desenho fica de fora (sala separada).
- `tools/mapgen.py` era do map01 antigo (3 seções, blocos `[x1, x2, y1, y2]`) e ficou obsoleto.

## Regras de medida (pulo padrão: JumpHeight 7,2 e WalkSpeed 16)

- Alcance de um pulo: ~8,8 studs no mesmo nível, ~7,6 subindo 3 (medido em jogo, 2026-11-15).
- Usado no mapa: vão de até **5** no mesmo nível; subida de **3** com vão de até **4,5**.
- Passagem por baixo de algo: pelo menos **7** de altura e **4** de largura.
- Cair abaixo de `workspace.FallenPartsDestroyHeight` (no map01, até 0; o mapa é fechado em rocha)
  mata; o jogador volta ao último checkpoint.
- Gancho: alcance de **40** a partir do `HumanoidRootPart`; personagem com ~5 de altura.
- Estas medidas valem para a velocidade padrão. Se um atributo de velocidade entrar, mudam.
