# MapBuilder (plugin do Studio)

Paleta para montar mapas 2D pintando blocos numa grade. Código em `plugins/MapBuilder`; os elementos
(cor, tag, colisão) vêm de `src/shared/MapElements.luau`, os mesmos que o jogo usa.

## Instalar / atualizar

```powershell
rojo build plugin.project.json --plugin MapBuilder.rbxm
```

Reabra o Studio depois (plugins locais só carregam ao abrir). Precisa do Rojo conectado: o plugin lê
`ReplicatedStorage.Shared.MapElements`.

## Usar

1. Aba **Plugins → MapBuilder** abre a paleta.
2. Escolha o elemento e clique/arraste no plano do jogo para pintar. **Apagar** remove o bloco
   clicado. **Ctrl+Z** desfaz cada traço.
3. **Mão única**: escolha a seta (↑ ↓ ← →) = sentido em que se pode passar.
4. **Grade** 2/4/8 studs. **Câmera 2D na área** põe a câmera de frente para o mapa.
5. Os blocos vão para `Workspace.Maps.Editor`. Salve o place (Ctrl+S) e faça commit do `.rbxl`.

## Testar o que pintou

**Spawn de teste** e clique no mapa: põe o ponto de nascer. **Testar no editor: LIGADO** faz o
playtest no Studio nascer ali (só no Studio; desligue antes de publicar).

## Elementos

| Elemento | Sólido | Gancho | Efeito |
|---|---|---|---|
| Bloco | sim | prende | terreno |
| Unhookable (`NoHook`) | sim | não prende | |
| Hookthrough (`HookThrough`) | sim | atravessa | |
| Freeze (`FreezeZone`) | não | — | congela enquanto dentro e `Freeze.ReleaseDelay` depois |
| Unfreeze (`UnfreezeZone`) | não | — | descongela na hora |
| Mão única (`OneWay` + `Direction`) | só contra a seta | atravessa | passa no sentido da seta |
| Morte (`KillZone`) | não | — | volta na hora ao checkpoint, sem morrer |
| Gancho único (`HookOnce`) | sim | prende 1x | por vida/checkpoint |

## Mapa como dados: exportar e importar (ADR 0052, etapa 2)

O mapa pintado vira um arquivo de texto, `maps/<nome>/tiles.json`, no formato
`race-and-escape/tiles@1` (grade de células de 2 studs; descrição completa em
[`tools/mapkit/README.md`](../../tools/mapkit/README.md)). É o que o validador e os scripts de
montagem leem; o `maps/map01/tiles.json` sai do greybox por `tools/mapkit/convert_layout.py`.

**Exportar** (seção *Mapa como dados* da paleta): lê `Workspace.Maps.Editor` (peças unidas viram as
células que cobrem, a mão única leva a direção, o spawn de teste vira `spawn`) e mostra o JSON na
caixa de texto do widget. Clique na caixa, **Ctrl+A, Ctrl+C**, cole num arquivo novo
`maps/<nome>/tiles.json` (UTF-8). O mesmo JSON sai no Output, em pedaços que quebram só entre linhas.
Sem o plugin (ou pelo MCP), `tools/mapkit/export_editor.luau` faz a mesma exportação e devolve o
JSON como retorno (Command Bar ou `execute_luau`, modo Edit; só lê).

**Importar:**
- **Importar arquivo .json** abre o seletor do Studio (`StudioService:PromptImportFileAsync`);
- **Importar do texto colado**: cole o JSON na caixa e clique (se o seletor falhar).

Se o Editor já tiver peças, aparece um aviso com a contagem e os botões **Apagar o Editor e
importar** / **Cancelar**. A importação apaga o Editor, pinta as células (cada célula de `cell`
studs vira blocos de 2), junta os vizinhos iguais e põe o spawn de teste. **Ctrl+Z** desfaz tudo de
uma vez. Ficam de fora, com aviso: `Checkpoint` e `RaceStart` (só existem nos mapas antigos),
`collide` (o MapBuilder monta cada elemento com a colisão padrão) e `attributes`.

Exportar → salvar → ler no Python → gravar dá o mesmo texto (diff limpo). Para conferir um arquivo:
`python -I -X utf8 -m unittest discover -s tools/mapkit/tests -t .` e, para o map01,
`python -I -X utf8 tools/mapkit/convert_layout.py`.
