param(
    [string]$OfflineInstallerPath = ""
)

$ErrorActionPreference = "Stop"

$existing = Get-Command ollama -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "Ollama est deja installe: $($existing.Source)"
    exit 0
}

if ($OfflineInstallerPath) {
    if (-not (Test-Path $OfflineInstallerPath)) {
        Write-Error "Installeur Ollama offline introuvable: $OfflineInstallerPath"
        exit 1
    }

    Write-Output "Lancement de l'installeur Ollama fourni: $OfflineInstallerPath"
    Write-Output "Finalisez l'assistant officiel Ollama puis relancez ce script si necessaire."
    Start-Process -FilePath $OfflineInstallerPath -Wait
}
else {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Error "winget est indisponible. Installez Ollama manuellement depuis https://ollama.com/download/windows ou fournissez -OfflineInstallerPath."
        exit 1
    }

    Write-Output "Installation d'Ollama via winget..."
    winget install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Echec de l'installation winget pour Ollama."
        exit 1
    }
}

$installed = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $installed) {
    Write-Error "Ollama ne semble pas disponible apres installation."
    exit 1
}

Write-Output "Ollama installe: $($installed.Source)"
exit 0
