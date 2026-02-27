# CYBERHOUND B2B WEBSITE - WINDOWS DEPLOYMENT
# ============================================
# This deploys the standalone website (NOT the core hunting system)
# The website connects to Cyberhound/ via API

Write-Host "`n🐺 CYBERHOUND B2B WEBSITE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Install from https://python.org/" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "`n📦 Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# Install Vercel CLI if needed
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
}

# Deploy
Write-Host "`n🚀 Deploying to Vercel..." -ForegroundColor Green
vercel --prod

Write-Host "`n✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "`nThe website is now live and connected to your main Cyberhound system.`n"
