# Ferramentas e bibliotecas do projeto

Este documento lista **tudo que o projeto usa**: o que é, para que serve, a versão e onde fica.
Sempre que uma ferramenta ou biblioteca entrar ou sair do projeto, este arquivo é atualizado.

Para quem vem do Java, a comparação ajuda:

| Aqui | Equivalente no mundo Java | Papel |
|---|---|---|
| Rokit | SDKMAN / Maven Wrapper | Garante a **versão das ferramentas** |
| Wally | Dependências do Maven / Gradle | Baixa **bibliotecas** de terceiros |
| Rojo | Plugin de build (empacotar o projeto) | Transforma os arquivos em um **jogo do Roblox** |
| Selene | Checkstyle / SpotBugs | Aponta **erros e más práticas** |
| StyLua | Spotless / google-java-format | **Formata** o código automaticamente |
| luau-lsp | Suporte a Java da IDE | Autocomplete e erros no editor |

> Atenção: o Rojo **não** gerencia dependências. Quem faz isso é o Wally.
> O Rojo é a "ponte" entre os arquivos do projeto e o Roblox Studio.

---

## Ferramentas (linha de comando)

Todas são instaladas e versionadas pelo **Rokit**. As versões ficam no [`rokit.toml`](../../rokit.toml).

### Rokit (v1.2.0)
- **O que é:** gerenciador de ferramentas (*toolchain manager*).
- **Para que serve:** instala Rojo, Wally, Selene e StyLua nas versões exatas do `rokit.toml`.
  Quem abrir o projeto em outro PC roda `rokit install` e recebe as mesmas versões.
- **Onde fica:** pasta do usuário, `C:\Users\<usuário>\.rokit` (~9 MB). Os outros programas
  também ficam guardados lá.
- **Repositório:** https://github.com/rojo-rbx/rokit

### Rojo (v7.7.1)
- **O que é:** ferramenta de sincronização e build para o Roblox.
- **Para que serve:**
  - `rojo serve`: mantém o Roblox Studio sincronizado com a pasta `src/` em tempo real.
    Precisa do **plugin do Rojo** instalado no Studio.
  - `rojo build -o build/jogo.rbxl`: gera um arquivo de jogo a partir do código.
- **Configuração:** [`default.project.json`](../../default.project.json) diz qual pasta vira o quê no
  Roblox (ex.: `src/server` → `ServerScriptService.Server`).
- **Repositório:** https://github.com/rojo-rbx/rojo

### Wally (v0.3.2)
- **O que é:** gerenciador de pacotes (bibliotecas) para Luau.
- **Para que serve:** `wally install` baixa as bibliotecas listadas no [`wally.toml`](../../wally.toml)
  para a pasta `Packages/`. Essa pasta **não vai para o Git** (está no `.gitignore`).
- **Repositório:** https://github.com/UpliftGames/wally

### Selene (v0.32.0)
- **O que é:** linter de Luau.
- **Para que serve:** `selene src` analisa o código e aponta erros (variável não usada, API
  deprecada, etc.) antes de testar no jogo.
- **Configuração:** [`selene.toml`](../../selene.toml).
- **Repositório:** https://github.com/Kampfkarren/selene

### StyLua (v2.6.0)
- **O que é:** formatador de código Luau.
- **Para que serve:** `stylua src` deixa o código todo no mesmo estilo. `stylua --check src` só
  verifica sem alterar (para usar no CI).
- **Configuração:** [`stylua.toml`](../../stylua.toml) (tabs, 110 colunas, aspas duplas).
- **Repositório:** https://github.com/JohnnyMorganz/StyLua

---

## Extensões do VS Code

Recomendadas em [`.vscode/extensions.json`](../../.vscode/extensions.json) (o VS Code sugere instalar
ao abrir o projeto).

| Extensão | Para que serve |
|---|---|
| **Luau Language Server** (luau-lsp) | Autocomplete, tipos e erros enquanto se escreve. Conhece a API do Roblox. |
| **Selene** | Mostra os avisos do Selene direto no editor. |
| **StyLua** | Formata o arquivo ao salvar. |
| **Rojo** | Botões para iniciar o `rojo serve` pelo VS Code. |

## Plugin do Roblox Studio

| Plugin | Para que serve |
|---|---|
| **Rojo** (7.7.1) | Recebe o código do `rojo serve` e aplica no Studio. Instalado com `rojo plugin install`, que coloca a versão igual à do Rojo do projeto. |

## MCP do Roblox Studio

- **O que é:** servidor MCP oficial do Roblox (`StudioMCP.exe`), instalado junto com o Studio.
  Conecta o Claude ao Studio aberto.
- **Para que serve:** ler a estrutura do place, montar mapas de teste, rodar Luau no Studio,
  testar o jogo e ler o Output.
- **Configuração:** [`.mcp.json`](../../.mcp.json) na raiz do projeto. Ele roda
  `%LOCALAPPDATA%\Roblox\mcp.bat`, que acha o `StudioMCP.exe` da versão atual do Studio.
- **Regras de uso:**
  - **Código só pelo Rojo** (arquivos em `src/`). Nunca editar scripts pelo MCP: o Rojo sobrescreveria.
  - MCP é para **mapa, testes e inspeção**.
  - Usar só com o place do projeto aberto no Studio.

---

## Bibliotecas (Wally)

| Biblioteca | Versão | Para que serve |
|---|---|---|
| **Trove** (sleitnick) | 1.8.0 | "Lixeira" de conexões e objetos: limpa tudo de uma vez quando um personagem morre ou sai da equipe. Evita vazamento de memória. |
| **Signal** (sleitnick) | 2.0.3 | Eventos internos entre módulos (ex.: "jogador congelou"), sem usar objetos do Roblox para isso. |

### Só para desenvolvimento (`[dev-dependencies]` do Wally)

Ficam em `DevPackages/` (fora do Git) e o Rojo põe em `ServerStorage.DevPackages`: **não vão
para o cliente** e o jogo não usa.

| Biblioteca | Versão | Para que serve |
|---|---|---|
| **TestEZ** (roblox) | 0.4.1 | Testes automáticos da lógica pura (RNF-04). Estilo `describe`/`it`/`expect` (parecido com JUnit + AssertJ). |

#### Testes automáticos (TestEZ)

- **Onde ficam:** pasta `tests/`, um arquivo por módulo (`Aim.spec.luau`, `HookRules.spec.luau`,
  `DoubleJump.spec.luau`, `Zones.spec.luau`, `HookSurface.spec.luau`). O Rojo põe em
  `ServerStorage.Tests` (fora do cliente).
- **Runner:** `tests/Runner.luau` é um ModuleScript (não roda sozinho no jogo). Com o Studio em
  **modo Edit** (sem play) e o Rojo conectado, rode na barra de comando ou pelo `execute_luau` do MCP:
  ```lua
  return require(game.ServerStorage.Tests.Runner)()
  ```
  Devolve (e imprime no Output) `X passaram, Y falharam, Z pulados` e o caminho de cada falha.
- **Por que TestEZ e não Jest-Lua:** o Jest-Lua precisa de `debug.loadmodule`, que no Studio só
  liga com uma FFlag em arquivo de configuração do Studio (`ClientAppSettings.json`). Testado em
  2026-11-17: `debug.loadmodule is not enabled.` Para não mexer em configuração do Studio, usamos o
  TestEZ, que roda com `require` normal.
- **Specs com `--!nonstrict`:** `describe`, `it`, `expect`, `beforeEach` etc. são globais que o
  TestEZ injeta no ambiente de cada spec; o modo strict acusaria "global desconhecida". O runner e o
  código do jogo continuam `--!strict`.
- **Selene:** `selene.toml` usa `std = "roblox+testez"`; as globais do TestEZ estão em
  [`testez.yml`](../../testez.yml) (raiz). Rode `selene src tests` e `stylua --check src tests`.
- **Cache do `require`:** se um módulo mudar e o resultado parecer antigo, rode de novo; se
  persistir, o Studio guardou o módulo antigo na sessão (feche e abra o place).

### Planejadas (entram quando forem necessárias)

| Biblioteca | Quando entra | Para que serve |
|---|---|---|
| ProfileStore (loleris) | M5 | Salvar dados dos jogadores com segurança. |
| Promise (evaera) | M5 | Fluxos assíncronos (DataStore, teleporte). |
| Blink ou ByteNet | M3 | Rede tipada e compacta entre servidor e cliente. |
| React-lua ou Fusion | M4/M6 | Interface (HUD, menus). |
| Jest-Lua | se um dia ligarmos `debug.loadmodule` | Substituto do TestEZ (ver acima por que não entrou). |

---

## Comandos do dia a dia

```bash
rokit install          # instala as ferramentas nas versões do projeto
wally install          # baixa as bibliotecas
rojo serve             # sincroniza com o Studio (deixar rodando)
selene src tests       # lint
stylua src tests       # formatar
```

Testes (Studio em modo Edit, Rojo conectado): `return require(game.ServerStorage.Tests.Runner)()`.

## Histórico

| Data | Mudança |
|---|---|
| 2026-11-11 | M0: Rokit 1.2.0, Rojo 7.7.1, Wally 0.3.2, Selene 0.32.0, StyLua 2.6.0, Trove 1.8.0, Signal 2.0.3 |
| 2026-11-11 | Plugin do Rojo 7.7.1 instalado no Studio |
| 2026-11-11 | MCP do Roblox Studio configurado no projeto (`.mcp.json`) |
| 2026-11-17 | TestEZ 0.4.1 (dev-dependency), pasta `tests/`, `ServerStorage.Tests`/`DevPackages`, selene `roblox+testez` |
