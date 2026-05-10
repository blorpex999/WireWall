param(
    [Parameter(Mandatory = $true)]
    [string]$DriveLetter
)

$drive = $DriveLetter.Trim().TrimEnd('\')
if ($drive.Length -eq 1) {
    $drive = "$drive`:"
}
$root = "$drive\"
if (-not (Test-Path -LiteralPath $root)) {
    Write-Error "Lecteur introuvable: $root"
    exit 1
}

$markerPath = Join-Path $root "WIREWALL_DEMO_THREAT.txt"
$payloadPath = Join-Path $root "wirewall_demo_payload.bat"

@"
WireWall demo marker

Ce fichier est inoffensif.
Il sert uniquement a declencher une alerte de simulation dans WireWall en mode demo.
Aucun malware reel n'est present sur ce support.
"@ | Set-Content -LiteralPath $markerPath -Encoding UTF8

@"
@echo off
setlocal
set "ROOT=%~d0\"
echo WireWall demo payload inoffensif.
echo Aucun changement systeme n'est effectue.
echo Execution demo: %DATE% %TIME% > "%ROOT%wirewall_demo_payload_ran.log"
echo Un fichier de log demo a ete ecrit sur le support USB.
pause
"@ | Set-Content -LiteralPath $payloadPath -Encoding ASCII

Write-Host "Marqueur demo cree: $markerPath"
Write-Host "Payload inoffensif cree: $payloadPath"
Write-Host "Branche le support avec WireWall en mode demo pour declencher l'alerte de simulation."
