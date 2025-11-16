# Frontend Run Script for Windows PowerShell
# This script starts the Vite development server

Write-Host "Starting Frontend Development Server..." -ForegroundColor Green

# Change to frontend directory
Set-Location $PSScriptRoot

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
}

# Check if port 5173 is already in use
$portInUse = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 5173 is already in use. Stopping existing process..." -ForegroundColor Yellow
    $proc = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Start the frontend server
Write-Host "Starting Vite dev server on http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev

