param(
    [string]$Model = "qwen2.5:3b"
)

$ErrorActionPreference = "Stop"

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Error "Ollama n'est pas installe. Installez-le d'abord."
    exit 1
}

$status = powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\check_ollama.ps1" -Model $Model -AsJson | ConvertFrom-Json
if ($status.model_present) {
    Write-Output "Le modele $Model est deja disponible."
    exit 0
}

Write-Output "Telechargement du modele $Model via Ollama..."
ollama pull $Model
if ($LASTEXITCODE -ne 0) {
    Write-Error "Echec du telechargement du modele $Model."
    exit 1
}

$status = powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\check_ollama.ps1" -Model $Model -AsJson | ConvertFrom-Json
if (-not $status.model_present) {
    Write-Error "Le modele $Model reste indisponible apres le pull."
    exit 1
}

Write-Output "Modele $Model pret pour WireWall."
exit 0
