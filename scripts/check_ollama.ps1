param(
    [string]$Model = "qwen2.5:14b",
    [switch]$AsJson,
    [switch]$RequireInstalled,
    [switch]$RequireRunning,
    [switch]$RequireModel
)

$ErrorActionPreference = "Stop"

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$installed = $null -ne $ollamaCommand
$running = $false
$modelPresent = $false
$models = @()
$details = ""

if ($installed) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
        $running = $true
        if ($response.models) {
            $models = @($response.models | ForEach-Object { "$($_.name)" })
            $modelPresent = $models -contains $Model
        }
        if (-not $models) {
            $details = "Ollama est installe et repond, mais aucun modele n'a ete detecte."
        } elseif ($modelPresent) {
            $details = "Ollama repond et le modele '$Model' est disponible."
        } else {
            $details = "Ollama repond, mais le modele '$Model' est absent."
        }
    }
    catch {
        $details = "Ollama est installe, mais l'API locale ne repond pas: $($_.Exception.Message)"
    }
}
else {
    $details = "Ollama n'est pas installe."
}

$status = [pscustomobject]@{
    installed = $installed
    running = $running
    model = $Model
    model_present = $modelPresent
    models = $models
    executable = if ($ollamaCommand) { $ollamaCommand.Source } else { "" }
    details = $details
}

if ($AsJson) {
    $status | ConvertTo-Json -Depth 4
}
else {
    $status
}

$failed = ($RequireInstalled -and -not $installed) -or ($RequireRunning -and -not $running) -or ($RequireModel -and -not $modelPresent)
if ($failed) {
    exit 1
}
exit 0
