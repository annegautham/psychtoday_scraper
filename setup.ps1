# Therapist Outreach Script Setup and Test
# PowerShell Script for Windows

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Therapist Outreach Script Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.7+ first." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements_minimal.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Some dependencies may have failed to install" -ForegroundColor Yellow
}

Write-Host ""

# Run tests
Write-Host "Running system tests..." -ForegroundColor Yellow
try {
    python test_outreach.py
    Write-Host "✅ Tests completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Tests failed. Check the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Edit config.json and add your email password" -ForegroundColor White
Write-Host "2. Customize states and universities to target" -ForegroundColor White
Write-Host "3. Run: python therapist_outreach.py" -ForegroundColor White
Write-Host ""

# Wait for user input
Read-Host "Press Enter to continue..."
