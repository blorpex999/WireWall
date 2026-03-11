param(
    [string]$Model = "qwen2.5:3b",
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

$os = Get-CimInstance Win32_OperatingSystem
$buildNumber = [int]$os.BuildNumber
$isSupportedWindows = [Environment]::Is64BitOperatingSystem -and $buildNumber -ge 19041
$localAppData = $env:LOCALAPPDATA
$runtimeRoot = if ($localAppData) { Join-Path $localAppData "WireWall" } else { "" }
$runtimeWritable = $false
$runtimeMessage = ""

if ($runtimeRoot) {
    try {
        New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
        $probeFile = Join-Path $runtimeRoot "write-test.tmp"
        Set-Content -Path $probeFile -Value "wirewall" -Encoding ascii
        Remove-Item -Path $probeFile -Force
        $runtimeWritable = $true
        $runtimeMessage = "Le repertoire runtime est accessible."
    }
    catch {
        $runtimeMessage = "Le repertoire runtime n'est pas accessible: $($_.Exception.Message)"
    }
}
else {
    $runtimeMessage = "LOCALAPPDATA est indisponible."
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$ollamaStatusJson = powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\check_ollama.ps1" -Model $Model -AsJson
$ollamaStatus = $ollamaStatusJson | ConvertFrom-Json

$result = [pscustomobject]@{
    product = "WireWall"
    recommended_model = $Model
    windows_caption = $os.Caption
    windows_version = $os.Version
    windows_build = $buildNumber
    is_supported_windows = $isSupportedWindows
    is_64bit = [Environment]::Is64BitOperatingSystem
    localappdata = $localAppData
    runtime_root = $runtimeRoot
    runtime_writable = $runtimeWritable
    runtime_message = $runtimeMessage
    is_admin = $isAdmin
    ollama = $ollamaStatus
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 6
    exit 0
}

Write-Output "Diagnostic prerequis WireWall"
Write-Output "Product            : $($result.product)"
Write-Output "Windows            : $($result.windows_caption) ($($result.windows_version), build $($result.windows_build))"
Write-Output "Windows supporte   : $($result.is_supported_windows)"
Write-Output "Architecture x64   : $($result.is_64bit)"
Write-Output "Session admin      : $($result.is_admin)"
Write-Output "Runtime root       : $($result.runtime_root)"
Write-Output "Runtime writable   : $($result.runtime_writable)"
Write-Output "Runtime detail     : $($result.runtime_message)"
Write-Output "Ollama installe    : $($result.ollama.installed)"
Write-Output "Ollama actif       : $($result.ollama.running)"
Write-Output "Modele attendu     : $($result.recommended_model)"
Write-Output "Modele disponible  : $($result.ollama.model_present)"
Write-Output "Ollama detail      : $($result.ollama.details)"
exit 0
