param(
    [string]$OutputPath = "",
    [string]$Url = ""
)

$ErrorActionPreference = "Stop"

if (-not $OutputPath) {
    $OutputPath = Join-Path $PSScriptRoot "..\build\third_party\OllamaSetup.exe"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$targetDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

if (-not $Url) {
    $wingetShow = winget show Ollama.Ollama --accept-source-agreements 2>$null
    if ($LASTEXITCODE -eq 0) {
        foreach ($line in $wingetShow) {
            if ($line -match 'Installer Url:\s+(https?://\S+)') {
                $Url = $Matches[1]
                break
            }
        }
    }
}

if (-not $Url) {
    Write-Error "Impossible de determiner l'URL de l'installeur Ollama. Fournissez -Url ou verifiez winget."
    exit 1
}

Write-Output "Telechargement de l'installeur Ollama depuis: $Url"
Invoke-WebRequest -Uri $Url -OutFile $OutputPath

if (-not (Test-Path $OutputPath)) {
    Write-Error "Installeur Ollama introuvable apres telechargement: $OutputPath"
    exit 1
}

Write-Output "Installeur Ollama pret: $OutputPath"
exit 0
