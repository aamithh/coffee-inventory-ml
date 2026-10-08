param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('setup-check', 'data', 'features', 'train', 'inventory', 'simulate', 'api', 'dashboard', 'test')]
    [string]$Task,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$TaskArgs
)
$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Project venv is missing. Run: python -m venv .venv'
}
Push-Location -LiteralPath $PSScriptRoot
try {
    & $projectPython -m src.cli @TaskArgs $Task
    $taskExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $taskExitCode
