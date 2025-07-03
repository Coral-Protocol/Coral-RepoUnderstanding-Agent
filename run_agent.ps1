# PowerShell script to set up a virtual environment and run a specified Python script
# Usage: .\run_agent.ps1 <python_script_path>

param (
    [Parameter(Mandatory=$true)]
    [string]$PythonScript
)

# Resolve script and project directory
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$ProjectDir = $ScriptDir

# Determine OS platform
$VenvDir = Join-Path $ProjectDir "venv\Scripts"
$VenvPython = Join-Path $VenvDir "python.exe"

# Normalize Python script path
$FullPythonScript = Join-Path $ProjectDir $PythonScript

if (!(Test-Path $FullPythonScript)) {
    Write-Error "Python script '$PythonScript' not found in $ProjectDir"
    exit 1
}

# Create virtual environment if it doesn't exist
if (!(Test-Path (Join-Path $ProjectDir "venv"))) {
    Write-Host "Creating virtual environment in $ProjectDir\venv..."
    python -m venv (Join-Path $ProjectDir "venv")
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Check if 'uv' is installed in the virtual environment
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing uv in virtual environment..."
    & $VenvPython -m pip install uv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install uv"
        exit 1
    }
}

# Change to project directory
Set-Location $ProjectDir

# Run uv sync
Write-Host "Running uv sync in $ProjectDir..."
& $VenvPython -m uv sync
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv sync failed"
    exit 1
}

# Run the Python script using uv
Write-Host "Running $PythonScript..."
& $VenvPython -m uv run $PythonScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run $PythonScript"
    exit 1
}

Write-Host "Script executed successfully."
