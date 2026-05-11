param(
    [string]$ReleaseDir = "release"
)

$ErrorActionPreference = "Stop"

$releasePath = Resolve-Path $ReleaseDir
$outputFile = Join-Path $releasePath "SHA256SUMS.txt"
$lines = @()

Get-ChildItem -Path $releasePath -File | Where-Object { $_.Name -notin @("SHA256SUMS.txt") -and $_.Extension -ne ".pptx" } | Sort-Object Name | ForEach-Object {
    $hash = Get-FileHash -Path $_.FullName -Algorithm SHA256
    $lines += "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), $_.Name
}

Set-Content -Path $outputFile -Value $lines -Encoding UTF8
Write-Output $outputFile
