# Onde as ferramentas estão instaladas e como desinstalar

Este documento lista **tudo que foi instalado no computador** para este projeto, fora e dentro da
pasta do projeto, e como remover cada item. Ele é atualizado sempre que algo novo é instalado.

> Levantamento feito em 2026-11-11, no Windows, usuário `Usuario`.

## Resumo

| O quê | Caminho | Tamanho |
|---|---|---|
| Rokit + Rojo, Wally, Selene, StyLua | `C:\Users\Usuario\.rokit\` | ~82 MB |
| Entrada no PATH do Windows | `C:\Users\Usuario\.rokit\bin` (variável `Path` do usuário) | — |
| Cache do Wally (índice de pacotes) | `C:\Users\Usuario\AppData\Local\wally\` | ~16 MB |
| Cache do Selene (definições da API do Roblox) | `C:\Users\Usuario\AppData\Local\selene\` | ~0,8 MB |
| Bibliotecas baixadas (dentro do projeto) | `D:\Projetos\dddrace-roblox\Packages\` | < 1 MB |
| Bibliotecas só de desenvolvimento: TestEZ (dentro do projeto) | `D:\Projetos\dddrace-roblox\DevPackages\` | ~0,5 MB |
| Arquivo de jogo de teste (dentro do projeto) | `D:\Projetos\dddrace-roblox\build\` | < 1 MB |
| Plugin do Rojo no Roblox Studio | `C:\Users\Usuario\AppData\Local\Roblox\Plugins\RojoManagedPlugin.rbxm` | ~0,5 MB |
| FFmpeg (fora do PATH) | `D:\Ferramentas\ffmpeg\` | ~0,3 GB |
| Frames do vídeo de referência de 2026-11-14 (fora do Git) | `D:\Projetos\dddrace-roblox\memory-palace\04-game-design\referencias\imagens\video-2026-11-14\` | ~40 GB |

**Ainda não instalados** (entram nesta lista quando forem instalados):

| O quê | Caminho esperado |
|---|---|
| Extensões do VS Code | `C:\Users\Usuario\.vscode\extensions\` |

## O que tem dentro de `.rokit`

```
C:\Users\Usuario\.rokit\
  bin\              atalhos: rokit.exe, rojo.exe, wally.exe, selene.exe, stylua.exe
  tool-storage\     os programas de verdade, separados por versão
                      rojo-rbx\rojo\7.7.1
                      upliftgames\wally\0.3.2
                      kampfkarren\selene\0.32.0
                      johnnymorganz\stylua\2.6.0
  rokit.toml        ferramentas globais (vazio por enquanto)
  auth.toml         token opcional do GitHub (vazio)
```

Os arquivos em `bin\` são atalhos: todos chamam o Rokit, que escolhe a versão certa pelo
`rokit.toml` do projeto.

---

## Como desinstalar

Feche o VS Code, os terminais e o Roblox Studio antes.

### 1. Rokit e todas as ferramentas (Rojo, Wally, Selene, StyLua)

1. Apague a pasta `C:\Users\Usuario\.rokit`.
2. Tire o Rokit do PATH:
   - Menu Iniciar → digite **"variáveis de ambiente"** → *Editar as variáveis de ambiente para a sua conta*.
   - Em **Variáveis de usuário**, selecione `Path` → **Editar**.
   - Remova a linha `C:\Users\Usuario\.rokit\bin` → **OK**.

Ou pelo PowerShell (faz os dois passos):

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.rokit"
$p = [Environment]::GetEnvironmentVariable('Path','User') -split ';' | Where-Object { $_ -notlike '*\.rokit\bin*' }
[Environment]::SetEnvironmentVariable('Path', ($p -join ';'), 'User')
```

Quer remover **só uma** ferramenta e manter o resto? Apague a pasta dela em `tool-storage\`, o
atalho em `bin\` e a linha correspondente no `rokit.toml` do projeto.

### 2. Caches

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\wally"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\selene"
```

São só caches: se as ferramentas continuarem instaladas, elas baixam de novo quando precisarem.

### 3. Arquivos dentro do projeto

As pastas `Packages\`, `DevPackages\` e `build\` são geradas e já estão fora do Git. Pode apagar
quando quiser; `wally install` e `rojo build` recriam.

Para tirar o **TestEZ** de vez: apague a seção `[dev-dependencies]` do `wally.toml`, a pasta
`DevPackages\`, a entrada `ServerStorage` do `default.project.json`, o arquivo `testez.yml` da raiz e
volte o `selene.toml` para `std = "roblox"`. A pasta `tests\` é código do projeto (não é instalação).

### 4. Plugin do Rojo no Studio

Com o Studio fechado, apague o arquivo
`C:\Users\Usuario\AppData\Local\Roblox\Plugins\RojoManagedPlugin.rbxm`:

```powershell
Remove-Item "$env:LOCALAPPDATA\Roblox\Plugins\RojoManagedPlugin.rbxm"
```

### 5. MCP do Roblox Studio

O MCP não instalou nada novo: o `StudioMCP.exe` e o `mcp.bat` vêm com o próprio Studio
(`C:\Users\Usuario\AppData\Local\Roblox\`) e saem quando o Studio for desinstalado.
Para desligar a conexão com o Claude, apague o arquivo `.mcp.json` da raiz do projeto.

### 5b. FFmpeg e frames de vídeo

Não mexe no PATH nem no registro. Para remover, apague as pastas:

```powershell
Remove-Item -Recurse -Force "D:\Ferramentas\ffmpeg"
Remove-Item -Recurse -Force "D:\Projetos\dddrace-roblox\memory-palace\04-game-design\referencias\imagens\video-2026-11-14"
```

### 6. Extensões do VS Code (quando forem instaladas)

No VS Code: aba **Extensões** (Ctrl+Shift+X) → clique na extensão → **Desinstalar**.
Extensões deste projeto: Luau Language Server, Selene, StyLua, Rojo.

---

## Conferir se sobrou algo

```powershell
Test-Path "$env:USERPROFILE\.rokit"
Test-Path "$env:LOCALAPPDATA\wally"
Test-Path "$env:LOCALAPPDATA\selene"
Test-Path "$env:LOCALAPPDATA\Roblox\Plugins\RojoManagedPlugin.rbxm"
[Environment]::GetEnvironmentVariable('Path','User') -split ';' | Select-String rokit
```

Se todos os `Test-Path` mostrarem `False` e o último comando não mostrar nada, está tudo removido.

## Histórico

| Data | Mudança |
|---|---|
| 2026-11-11 | Rokit 1.2.0 + Rojo, Wally, Selene, StyLua; caches do Wally e do Selene |
| 2026-11-11 | Plugin do Rojo no Studio (`RojoManagedPlugin.rbxm`) |
| 2026-11-11 | MCP do Roblox Studio configurado (`.mcp.json` no projeto; nada instalado no PC) |
| 2026-11-17 | TestEZ 0.4.1 via Wally em `DevPackages\` (só dentro do projeto; nada instalado no PC) |
| 2026-11-21 | FFmpeg 9.1 em `D:\Ferramentas\ffmpeg\` e frames do vídeo de referência (fora do Git) |
