# Quick PostgreSQL Setup Script for Windows
# This script helps you set up PostgreSQL for the project

Write-Host "=== PostgreSQL Setup Helper ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
$dockerAvailable = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerAvailable = $true
        Write-Host "✅ Docker is available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Docker not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1. Use Docker PostgreSQL (Recommended - Easiest)"
Write-Host "2. Check if PostgreSQL is installed locally"
Write-Host "3. Use SQLite for development (No setup needed)"
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

if ($choice -eq "1") {
    if ($dockerAvailable) {
        Write-Host ""
        Write-Host "Starting PostgreSQL in Docker..." -ForegroundColor Cyan
        docker run --name postmeeting-db `
            -e POSTGRES_PASSWORD=postgres `
            -e POSTGRES_DB=postmeeting `
            -p 5432:5432 `
            -d postgres:15
        
        Write-Host ""
        Write-Host "✅ PostgreSQL container started!" -ForegroundColor Green
        Write-Host "Database: postmeeting" -ForegroundColor Green
        Write-Host "User: postgres" -ForegroundColor Green
        Write-Host "Password: postgres" -ForegroundColor Green
        Write-Host "Port: 5432" -ForegroundColor Green
        Write-Host ""
        Write-Host "Now run migrations:" -ForegroundColor Cyan
        Write-Host "  cd backend" -ForegroundColor White
        Write-Host "  alembic revision --autogenerate -m 'Initial migration'" -ForegroundColor White
        Write-Host "  alembic upgrade head" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ Docker is not installed" -ForegroundColor Red
        Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    }
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Checking for PostgreSQL services..." -ForegroundColor Cyan
    $services = Get-Service | Where-Object {$_.Name -like "*postgres*"}
    if ($services) {
        Write-Host "Found PostgreSQL services:" -ForegroundColor Green
        $services | Format-Table Name, Status, DisplayName
        Write-Host ""
        Write-Host "To start a service, run:" -ForegroundColor Cyan
        Write-Host "  Start-Service <service-name>" -ForegroundColor White
    } else {
        Write-Host "❌ No PostgreSQL services found" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "PostgreSQL is not installed. Options:" -ForegroundColor Cyan
        Write-Host "1. Install PostgreSQL from: https://www.postgresql.org/download/windows/" -ForegroundColor White
        Write-Host "2. Use Docker (option 1)" -ForegroundColor White
        Write-Host "3. Use SQLite for development (option 3)" -ForegroundColor White
    }
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "Setting up SQLite for development..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  Note: SQLite is for development only, not production" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To use SQLite:" -ForegroundColor Cyan
    Write-Host "1. Install aiosqlite: pip install aiosqlite" -ForegroundColor White
    Write-Host "2. Update DATABASE_URL in config.py to: sqlite+aiosqlite:///./postmeeting.db" -ForegroundColor White
    Write-Host "3. Update database.py to use SQLite engine" -ForegroundColor White
    Write-Host ""
    Write-Host "See DATABASE_SETUP.md for detailed instructions" -ForegroundColor Cyan
} else {
    Write-Host "Invalid choice" -ForegroundColor Red
}

