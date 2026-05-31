# build_exe.ps1 — Windows-native standalone EXE packager for mybotzhuli.
#
# This script packages the FastAPI API service and AI Agent Worker into standalone Windows executable (.exe) files.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "📦 Starting Standalone Windows EXE Packaging..." -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$venvPath = Join-Path -Path $PSScriptRoot -ChildPath ".venv"
if (-not (Test-Path -LiteralPath $venvPath)) {
    Write-Host "❌ Error: Virtual environment (.venv) not found. Please run .\setup_win.ps1 first." -ForegroundColor Red
    exit 1
}

$pyinstallerPath = Join-Path -Path $venvPath -ChildPath "Scripts\pyinstaller.exe"
if (-not (Test-Path -LiteralPath $pyinstallerPath)) {
    Write-Host "⚙️ Installing pyinstaller in the virtual environment..." -ForegroundColor Yellow
    $pipPath = Join-Path -Path $venvPath -ChildPath "Scripts\pip.exe"
    & $pipPath install pyinstaller
}

# Clean previous build directories
$distDir = Join-Path -Path $PSScriptRoot -ChildPath "dist"
$buildDir = Join-Path -Path $PSScriptRoot -ChildPath "build"
if (Test-Path -LiteralPath $distDir) {
    Remove-Item -Path $distDir -Recurse -Force
}
if (Test-Path -LiteralPath $buildDir) {
    Remove-Item -Path $buildDir -Recurse -Force
}

# 1. Package API Service
Write-Host "`n🚀 Packaging mybotzhuli_api.exe..." -ForegroundColor Yellow
& $pyinstallerPath --onefile `
    --collect-all uvicorn `
    --collect-all fastapi `
    --collect-all starlette `
    --collect-all pydantic `
    --collect-all pydantic_settings `
    --collect-all psycopg `
    --collect-all psycopg_binary `
    --name mybotzhuli_api `
    (Join-Path -Path $PSScriptRoot -ChildPath "run_api.py")

# 2. Package Worker Service
Write-Host "`n🤖 Packaging mybotzhuli_worker.exe..." -ForegroundColor Yellow
& $pyinstallerPath --onefile `
    --collect-all pydantic `
    --collect-all pydantic_settings `
    --collect-all psycopg `
    --collect-all psycopg_binary `
    --name mybotzhuli_worker `
    (Join-Path -Path $PSScriptRoot -ChildPath "run_worker.py")

Write-Host "`n✅ Standalone Windows EXEs created successfully!" -ForegroundColor Green
Write-Host "-------------------------------------------------" -ForegroundColor Cyan
Write-Host "EXE files are located in the 'dist' directory:" -ForegroundColor Cyan
Write-Host "API Service:    dist\mybotzhuli_api.exe" -ForegroundColor Yellow
Write-Host "Worker Service: dist\mybotzhuli_worker.exe" -ForegroundColor Yellow
