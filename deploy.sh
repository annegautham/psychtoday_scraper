#!/bin/bash

# Psychology Today Scraper - Fly.io Deployment Script

echo "🚀 Deploying Psychology Today Scraper to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI not found. Installing..."
    
    # Install on Windows (PowerShell)
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
    else
        # Install on Linux/Mac
        curl -L https://fly.io/install.sh | sh
    fi
    
    echo "✅ Fly CLI installed. Please restart your terminal and run this script again."
    exit 1
fi

# Login to Fly.io
echo "🔐 Logging into Fly.io..."
flyctl auth login

# Launch the app
echo "🛠️ Launching app on Fly.io..."
flyctl launch --no-deploy

# Deploy the app
echo "🚀 Deploying app..."
flyctl deploy

echo "✅ Deployment complete!"
echo "📱 Your app is live at: https://psychtoday-scraper.fly.dev"
echo "🔧 Monitor with: flyctl logs"
echo "📊 Dashboard: https://fly.io/dashboard"
