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
Il sert a declencher une alerte de simulation dans WireWall en mode reel ou demo.
Aucun malware reel n'est present sur ce support.
"@ | Set-Content -LiteralPath $markerPath -Encoding UTF8

@"
@echo off
setlocal
set "ROOT=%~d0\"
set "PROOF_DIR=%TEMP%\WireWallUsbProof"
set "PROOF_FILE=%PROOF_DIR%\usb_payload_proof.txt"

if not exist "%PROOF_DIR%" mkdir "%PROOF_DIR%" >nul 2>&1
(
  echo WireWall USB execution proof
  echo.
  echo Timestamp: %DATE% %TIME%
  echo User: %USERNAME%
  echo Computer: %COMPUTERNAME%
  echo Source drive: %ROOT%
  echo.
  echo This payload is harmless.
  echo It proves that code launched from a USB support can write a local user-space trace.
  echo No persistence, no network call, no privilege escalation, no file deletion.
) > "%PROOF_FILE%"

copy /Y "%PROOF_FILE%" "%ROOT%wirewall_demo_payload_ran.log" >nul 2>&1

echo WireWall demo payload inoffensif execute.
echo Preuve locale creee:
echo %PROOF_FILE%
echo.
echo Copie de preuve creee sur le support:
echo %ROOT%wirewall_demo_payload_ran.log
pause
"@ | Set-Content -LiteralPath $payloadPath -Encoding ASCII

Write-Host "Marqueur demo cree: $markerPath"
Write-Host "Payload inoffensif cree: $payloadPath"
Write-Host "Branche le support avec WireWall en mode reel ou demo pour declencher l'alerte de simulation."
Write-Host "Optionnel: lance wirewall_demo_payload.bat pour creer une preuve locale inoffensive dans %TEMP%."
