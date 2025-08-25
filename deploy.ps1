# AI Product Council Backend Deployment Script for Windows PowerShell
param(
    [switch]$Help,
    [switch]$Local
)

if ($Help) {
    Write-Host @"
AI Product Council Backend Deployment Script

Usage:
    .\deploy.ps1              # Deploy to production using Docker
    .\deploy.ps1 -Local       # Deploy locally without Docker
    .\deploy.ps1 -Help        # Show this help message

Requirements:
    - Docker Desktop (for production deployment)
    - Python 3.11+ (for local deployment)
    - Google API Key
"@
    exit 0
}

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host "🚀 Starting AI Product Council Backend Deployment..." -ForegroundColor Cyan

if ($Local) {
    # Local deployment
    Write-Status "Starting local deployment..."
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Python found: $pythonVersion"
    } catch {
        Write-Error "Python is not installed or not in PATH"
        Write-Host "Please install Python 3.11+ and try again"
        exit 1
    }
    
    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found!"
        Write-Host "Please copy env.example to .env and fill in your values:"
        Write-Host "Copy-Item env.example .env"
        Write-Host "Then edit .env with your actual configuration values."
        exit 1
    }
    
    # Install dependencies
    Write-Status "Installing Python dependencies..."
    try {
        pip install -r requirements.txt
        Write-Status "Dependencies installed successfully"
    } catch {
        Write-Error "Failed to install dependencies"
        exit 1
    }
    
    # Start the server
    Write-Status "Starting local server..."
    Write-Host "📡 API will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🏥 Health check: http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    
    python run_local.py
    
} else {
    # Production deployment with Docker
    Write-Status "Starting production deployment with Docker..."
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-Status "Docker is running"
    } catch {
        Write-Error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    }
    
    # Check if .env.prod exists
    if (-not (Test-Path ".env.prod")) {
        Write-Error ".env.prod file not found!"
        Write-Host "Please copy env.prod.example to .env.prod and fill in your values:"
        Write-Host "Copy-Item env.prod.example .env.prod"
        Write-Host "Then edit .env.prod with your actual configuration values."
        exit 1
    }
    
    # Create necessary directories
    Write-Status "Creating necessary directories..."
    New-Item -ItemType Directory -Force -Path "logs\nginx" | Out-Null
    New-Item -ItemType Directory -Force -Path "init-db" | Out-Null
    
    # Stop existing containers
    Write-Status "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>$null
    
    # Build and start services
    Write-Status "Building and starting services..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be healthy
    Write-Status "Waiting for services to be healthy..."
    Start-Sleep -Seconds 30
    
    # Check service health
    Write-Status "Checking service health..."
    
    # Check API health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Status "✅ API is healthy"
        } else {
            Write-Warning "⚠️  API health check failed, but continuing..."
        }
    } catch {
        Write-Warning "⚠️  API health check failed, but continuing..."
    }
    
    # Show service status
    Write-Status "Service status:"
    docker-compose -f docker-compose.prod.yml ps
    
    # Show logs
    Write-Status "Recent logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=20
    
    Write-Host ""
    Write-Status "🎉 Deployment completed successfully!"
    Write-Host ""
    Write-Host "📡 Your API is now available at:" -ForegroundColor Cyan
    Write-Host "   - Local: http://localhost:8000" -ForegroundColor White
    Write-Host "   - Network: http://localhost:8000" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🏥 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
    Write-Host "   - View logs: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
    Write-Host "   - Stop services: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
    Write-Host "   - Restart services: docker-compose -f docker-compose.prod.yml restart" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Remember to:" -ForegroundColor Yellow
    Write-Host "   - Update your frontend to use the correct backend URL" -ForegroundColor White
    Write-Host "   - Configure CORS_ORIGINS in .env.prod for your frontend domain" -ForegroundColor White
    Write-Host "   - Set up SSL certificates if deploying to production" -ForegroundColor White
    Write-Host "   - Configure your firewall to allow traffic on port 8000" -ForegroundColor White
}
