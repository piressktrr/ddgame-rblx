# Gera um .rbxm por elemento do MapBuilder (para publicar no inventário do Roblox).
# Valores iguais aos de src/shared/MapElements.luau. Saída em build/blocks/ (fora do Git).
# Uso: powershell -File tools/build_block_models.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root "build\blocks"
$tmp = Join-Path $out "projects"
New-Item -ItemType Directory -Force $tmp | Out-Null

$elements = @(
    @{ id = "Block";       name = "DD Bloco";        tag = $null;          color = @(150,150,105); t = 0;    collide = $true },
    @{ id = "Unhookable";  name = "DD Unhookable";   tag = "NoHook";       color = @(142,91,214);  t = 0;    collide = $true },
    @{ id = "HookThrough"; name = "DD Hookthrough";  tag = "HookThrough";  color = @(45,45,52);    t = 0;    collide = $true },
    @{ id = "Freeze";      name = "DD Freeze";       tag = "FreezeZone";   color = @(70,75,90);    t = 0.45; collide = $false },
    @{ id = "Unfreeze";    name = "DD Unfreeze";     tag = "UnfreezeZone"; color = @(255,215,70);  t = 0.45; collide = $false },
    @{ id = "OneWay";      name = "DD Mao unica";    tag = "OneWay";       color = @(235,242,255); t = 0.5;  collide = $false },
    @{ id = "Kill";        name = "DD Morte";        tag = "KillZone";     color = @(220,60,70);   t = 0.45; collide = $false },
    @{ id = "HookOnce";    name = "DD Gancho unico"; tag = "HookOnce";     color = @(95,191,106);  t = 0;    collide = $true }
)

foreach ($e in $elements) {
    $c = $e.color | ForEach-Object { $_ / 255 }
    $props = [ordered]@{
        Anchored     = $true
        Size         = @(4, 4, 12)
        Color        = @($c[0], $c[1], $c[2])
        Material     = "SmoothPlastic"
        Transparency = $e.t
        CanCollide   = $e.collide
        CastShadow   = ($e.t -eq 0)
        TopSurface   = "Smooth"
        BottomSurface = "Smooth"
    }
    if ($e.tag) { $props.Tags = @($e.tag) }
    $attrs = [ordered]@{ Element = $e.id }
    $node = [ordered]@{ '$className' = "Part"; '$properties' = $props; '$attributes' = $attrs }
    if ($e.id -eq "OneWay") {
        $attrs.Direction = "Up"
        $node.Arrows = [ordered]@{
            '$className' = "SurfaceGui"
            '$properties' = [ordered]@{ Face = "Back"; SizingMode = "PixelsPerStud"; PixelsPerStud = 25; LightInfluence = 0 }
            Label = [ordered]@{
                '$className' = "TextLabel"
                '$properties' = [ordered]@{
                    BackgroundTransparency = 1; Size = "__FULL_UDIM2__"; Text = "^ ^ ^"; TextScaled = $true
                    TextColor3 = @(0.431, 0.49, 0.627)
                }
            }
        }
    }
    $project = [ordered]@{ name = $e.name; tree = $node }
    $projectPath = Join-Path $tmp "$($e.id).project.json"
    # Sem BOM: o Rojo não aceita o BOM que o Set-Content do PowerShell 5 escreve.
    # O ConvertTo-Json do PowerShell 5 achata arrays aninhados: o UDim2 entra como texto pronto.
    $json = ($project | ConvertTo-Json -Depth 10).Replace('"__FULL_UDIM2__"', '{ "UDim2": [[1, 0], [1, 0]] }')
    [IO.File]::WriteAllText($projectPath, $json, (New-Object Text.UTF8Encoding $false))
    rojo build $projectPath -o (Join-Path $out "$($e.id).rbxm")
}
