<#
.SYNOPSIS
Install EON_PFA on Windows from the extracted release package.

.DESCRIPTION
Creates a Python virtual environment, installs dependencies, and prints the command to run the app.
#>
[CmdletBinding()]
param(
    [string]$ModelPath = $env:EON_PFA_MODEL_PATH
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Error "Python 3 is not found in PATH. Install Python 3 and rerun this script."
    exit 1
}

$pythonExe = $python.Source
Write-Host "Using Python: $pythonExe"

Write-Host "Creating virtual environment..."
& "$pythonExe" -m venv ".venv"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create virtual environment."
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment python executable not found: $venvPython"
}

Write-Host "Upgrading pip..."
& "$venvPython" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

Write-Host "Installing requirements..."
& "$venvPython" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install requirements."
}

if ($ModelPath) {
    Write-Host "Model path override detected: $ModelPath"
    Write-Host "You can set EON_PFA_MODEL_PATH in PowerShell before running the app:"
    Write-Host "  $env:USERPROFILE\> $env:EON_PFA_MODEL_PATH = '$ModelPath'"
}

Write-Host ""
Write-Host "Installation complete. Run the app with:"
Write-Host "  .\\.venv\\Scripts\\python.exe EON_PFA.py"
Write-Host "Or set EON_PFA_MODEL_PATH to your GGUF model path before launch."
