# ForestWatch AI - PowerShell Unified Launcher
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectRoot

Write-Host "========================================================================" -ForegroundColor Green
Write-Host "      ForestWatch AI - Starting Multi-Subsystem Platform" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    Write-Host "[*] Using virtual environment python: $VenvPython" -ForegroundColor Cyan
    & $VenvPython (Join-Path $ProjectRoot "runproj.py") @args
} else {
    Write-Host "[*] Using system python" -ForegroundColor Cyan
    & python (Join-Path $ProjectRoot "runproj.py") @args
}

