$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = Join-Path $ScriptDir ".venv/bin/python"

if (Test-Path $VenvPython) {
    $Python = $VenvPython
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $Python = (Get-Command python3).Source
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = (Get-Command python).Source
} else {
    Write-Error "No python interpreter found"
    exit 1
}

& $Python -m filechat.main @args
