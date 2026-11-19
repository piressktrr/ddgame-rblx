# Abre o place no Roblox Studio já com o `rojo serve` rodando (inicia se ainda não estiver).
# Uso: powershell -ExecutionPolicy Bypass -File tools/abrir-mapa.ps1  (ou pelo atalho da Área de Trabalho)

$root = Split-Path $PSScriptRoot -Parent
$port = 34872 # porta padrão do `rojo serve`

$listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    $rojo = Join-Path $HOME ".rokit\bin\rojo.exe"
    if (-not (Test-Path $rojo)) { $rojo = "rojo" }
    # Janela minimizada com o servidor; fechar a janela desliga o Rojo.
    Start-Process powershell -WorkingDirectory $root -WindowStyle Minimized `
        -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'rojo serve'; & '$rojo' serve"
}

Start-Process (Join-Path $root "place\RaceAndEscape.rbxl")
