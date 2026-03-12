param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$version = (Get-Content (Join-Path $root "VERSION") -Encoding UTF8).Trim()
$distDir = Join-Path $root "dist\WireWall"
$releaseDir = Join-Path $root "release"
$portableName = "WireWall-$version-win64-portable"
$portableStage = Join-Path $releaseDir $portableName
$portableZip = Join-Path $releaseDir "$portableName.zip"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$isccCandidates = @(
    $env:ISCC_EXE,
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) }
$iscc = $isccCandidates | Select-Object -First 1
$ollamaInstaller = Join-Path $root "build\third_party\OllamaSetup.exe"

if (!(Test-Path (Join-Path $distDir "WireWall.exe"))) {
    throw "Bundle dist absent: execute d'abord scripts\build.bat."
}

if (!(Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

if (Test-Path $portableStage) {
    Remove-Item $portableStage -Recurse -Force
}
if (Test-Path $portableZip) {
    Remove-Item $portableZip -Force
}

New-Item -ItemType Directory -Path $portableStage | Out-Null
$null = robocopy $distDir $portableStage /E
if ($LASTEXITCODE -ge 8) {
    throw "Echec de copie du bundle dist vers le package portable."
}

New-Item -ItemType Directory -Path (Join-Path $portableStage "docs") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $portableStage "tools") | Out-Null
Copy-Item `
    (Join-Path $root "README.md"), `
    (Join-Path $root "CHANGELOG.md"), `
    (Join-Path $root "config.example.json"), `
    (Join-Path $root "VERSION") `
    -Destination $portableStage -Force

$null = robocopy (Join-Path $root "docs") (Join-Path $portableStage "docs") /E
if ($LASTEXITCODE -ge 8) {
    throw "Echec de copie de la documentation vers le package portable."
}

Copy-Item `
    (Join-Path $root "scripts\check_target_prereqs.bat"), `
    (Join-Path $root "scripts\check_target_prereqs.ps1"), `
    (Join-Path $root "scripts\setup_ai.bat"), `
    (Join-Path $root "scripts\check_ollama.ps1"), `
    (Join-Path $root "scripts\install_ollama.ps1"), `
    (Join-Path $root "scripts\install_ollama_model.ps1"), `
    (Join-Path $root "scripts\setup_ai.ps1") `
    -Destination (Join-Path $portableStage "tools") -Force

if (Test-Path $ollamaInstaller) {
    Copy-Item $ollamaInstaller -Destination (Join-Path $portableStage "tools\OllamaSetup.exe") -Force
}

Compress-Archive -Path (Join-Path $portableStage "*") -DestinationPath $portableZip -Force
Write-Host "Package portable genere: $portableZip"

if (-not $SkipInstaller) {
    if (-not $iscc) {
        Write-Warning "Inno Setup 6 absent. Les installateurs ne seront pas generes."
    } else {
        & $iscc "/DAppVersion=$version" "/DSourceDist=$distDir" "/DReleaseDir=$releaseDir" (Join-Path $root "installer\WireWall.iss")
        if ($LASTEXITCODE -ne 0) {
            throw "Echec de compilation de l'installateur standard."
        }
        Write-Host "Installateur standard genere."

        if (Test-Path $ollamaInstaller) {
            & $iscc "/DAppVersion=$version" "/DSourceDist=$distDir" "/DReleaseDir=$releaseDir" /DBundleOllamaInstaller=1 "/DOllamaInstallerSource=$ollamaInstaller" (Join-Path $root "installer\WireWall.iss")
            if ($LASTEXITCODE -ne 0) {
                throw "Echec de compilation de l'installateur full."
            }
            Write-Host "Installateur full genere."
        } else {
            Write-Warning "OllamaSetup.exe absent. L'installateur full n'a pas ete regenere."
        }
    }
}

if (Test-Path $venvPython) {
    & $venvPython (Join-Path $root "scripts\write_release_manifest.py")
} else {
    python (Join-Path $root "scripts\write_release_manifest.py")
}
if ($LASTEXITCODE -ne 0) {
    throw "Echec de generation du manifeste release."
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\write_release_hashes.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Echec de generation des hashes."
}

Push-Location $root
try {
    & cmd /c scripts\validate_artifacts.bat
    if ($LASTEXITCODE -ne 0) {
        throw "Validation des artefacts en echec."
    }
} finally {
    Pop-Location
}

Get-ChildItem $releaseDir | Where-Object {
    $_.Name -like "*$version*" -or $_.Name -eq "SHA256SUMS.txt"
} | Select-Object Name, Length, LastWriteTime
