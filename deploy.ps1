# Psychology Today Scraper - Fly.io Deployment Script (PowerShell)

Write-Host "🚀 Deploying Psychology Today Scraper to Fly.io..." -ForegroundColor Green

# Check if flyctl is installed
if (-not (Get-Command flyctl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Fly CLI not found. Installing..." -ForegroundColor Red
    
    # Install Fly CLI
    iwr https://fly.io/install.ps1 -useb | iex
    
    Write-Host "✅ Fly CLI installed. Please restart your terminal and run this script again." -ForegroundColor Green
    exit 1
}

# Login to Fly.io
Write-Host "🔐 Logging into Fly.io..." -ForegroundColor Yellow
flyctl auth login

# Launch the app
Write-Host "🛠️ Launching app on Fly.io..." -ForegroundColor Yellow
flyctl launch --no-deploy

# Deploy the app
Write-Host "🚀 Deploying app..." -ForegroundColor Yellow
flyctl deploy

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "📱 Your app is live at: https://psychtoday-scraper.fly.dev" -ForegroundColor Cyan
Write-Host "🔧 Monitor with: flyctl logs" -ForegroundColor Gray
Write-Host "📊 Dashboard: https://fly.io/dashboard" -ForegroundColor Gray
