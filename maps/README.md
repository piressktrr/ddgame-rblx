# Mapas

Cada mapa é **dado**, não script. A fonte da verdade do greybox é o `layout.json` da pasta do mapa.

```
maps/map01/
  layout.json   blocos [x1, x2, y1, y2] vistos de lado (X horizontal, Y altura, plano Z = 0)
  map01.svg     vista 2D gerada (abrir no navegador para revisar o level design)
  build.luau    código gerado que monta Workspace.Maps.Map01 no Studio
```

## Fluxo

1. Edite `layout.json` (ou peça a um agente).
2. Gere a vista e o build: `python tools/mapgen.py maps/map01`.
3. Confira o `map01.svg`.
4. Rode o `build.luau` no Studio (pelo MCP `execute_luau` ou na barra de comandos). Ele apaga e
   recria `Workspace.Maps.Map01`.
5. Salve o place (`place/RaceAndEscape.rbxl`).

## Regras de medida (pulo padrão do Roblox)

- Altura do pulo ≈ 6,4 studs: subida de no máximo **4** (e só com vão curto).
- Distância do pulo ≈ 8 studs (JumpPower 50): vãos de no máximo **5** no mesmo nível (o pulo cobre ~8 studs no total).
- Passagem por baixo de algo: pelo menos **6** studs de altura livre (personagem ≈ 5).
- Cair abaixo de `killHeight` mata. Por enquanto renasce no início (checkpoints chegam na Fase 2).

Quando o tema de fantasia entrar, a arte é colocada **por cima** do greybox, sem mudar as medidas
de colisão.
