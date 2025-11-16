# Backend Run Script for Windows PowerShell
# This script starts the FastAPI backend server

Write-Host "Starting Backend Server..." -ForegroundColor Green

# Change to backend directory
Set-Location $PSScriptRoot

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Warning: Virtual environment not found. Make sure venv is set up." -ForegroundColor Red
    exit 1
}

# Check if port 8000 is already in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 8000 is already in use. Stopping existing process..." -ForegroundColor Yellow
    $proc = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Start the backend server
Write-Host "Starting uvicorn server on http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run uvicorn via wrapper script to ensure Windows event loop policy is set correctly
# This fixes the ProactorEventLoop issue on Windows for psycopg
Write-Host "Using wrapper script to set Windows event loop policy..." -ForegroundColor Yellow
python run_server.py

