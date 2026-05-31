# run_all_win.ps1 — Starts both API and Worker services in separate console windows.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = $PSScriptRoot

Write-Host "🚀 Spawning mybotzhuli services concurrently..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if virtual environment exists
$venvPath = Join-Path -Path $scriptDir -ChildPath ".venv"
if (-not (Test-Path -LiteralPath $venvPath)) {
    Write-Host "⚠️ Virtual environment not found. Running setup_win.ps1 first..." -ForegroundColor Yellow
    & (Join-Path -Path $scriptDir -ChildPath "setup_win.ps1")
}

# Start API service in a new window
Write-Host "🤖 Starting FastAPI Service..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$scriptDir\run_api.bat`"" -WorkingDirectory $scriptDir

# Start Worker service in a new window
Write-Host "⚙️ Starting Agent Worker..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$scriptDir\run_worker.bat`"" -WorkingDirectory $scriptDir

Write-Host "`n✅ Both services spawned in separate terminal windows!" -ForegroundColor Green
Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "FastAPI Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "Close the popped-up cmd windows to stop the services." -ForegroundColor Gray
