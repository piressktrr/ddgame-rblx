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
