$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv --system-site-packages .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:HF_HUB_DISABLE_XET = '1'
& '.venv\Scripts\python.exe' prepare_models.py
if ($LASTEXITCODE -ne 0) { throw 'Model download failed. Run Setup.ps1 again to resume.' }
Write-Output 'Ready. Double-click Start.cmd.'
