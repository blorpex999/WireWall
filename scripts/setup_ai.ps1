param(
    [string]$Model = "qwen2.5:3b",
    [string]$OfflineInstallerPath = "",
    [switch]$SkipOllamaInstall
)

$ErrorActionPreference = "Stop"

Write-Output "Verification de l'etat Ollama pour WireWall..."
$statusJson = powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\check_ollama.ps1" -Model $Model -AsJson
$status = $statusJson | ConvertFrom-Json

if (-not $status.installed) {
    if (-not $OfflineInstallerPath) {
        $bundledInstaller = Join-Path $PSScriptRoot "OllamaSetup.exe"
        if (Test-Path $bundledInstaller) {
            $OfflineInstallerPath = $bundledInstaller
            Write-Output "Installeur Ollama embarque detecte: $bundledInstaller"
        }
    }

    if ($SkipOllamaInstall) {
        Write-Error "Ollama n'est pas installe et -SkipOllamaInstall est actif."
        exit 1
    }
    powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\install_ollama.ps1" -OfflineInstallerPath $OfflineInstallerPath
    if ($LASTEXITCODE -ne 0) {
        exit 1
    }
}

powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\install_ollama_model.ps1" -Model $Model
if ($LASTEXITCODE -ne 0) {
    exit 1
}

Write-Output "Configuration IA locale terminee pour WireWall."
exit 0
