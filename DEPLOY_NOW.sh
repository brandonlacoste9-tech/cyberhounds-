#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CYBERHOUND WEB - DEPLOY NOW
# New repo - separate from main hunting system
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   🐺 CYBERHOUND WEB - B2B DEPLOYMENT                           ║"
echo "║   Separate Repo | Clean Architecture                            ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check directory
if [ ! -f "frontend/index.html" ]; then
    echo "❌ ERROR: frontend/index.html not found"
    echo "   Make sure you're in the Cyberhound-Web directory"
    exit 1
fi

echo "📦 Step 1: Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🔗 Step 2: Checking connection to main Cyberhound system..."
python3 -c "
from pathlib import Path
cyberhound = Path.home() / 'Cyberhound'
if cyberhound.exists():
    print(f'   ✅ Found: {cyberhound}')
else:
    print(f'   ⚠️  Warning: {cyberhound} not found')
    print('   The website will deploy but cannot connect to hunts')
"

echo ""
echo "🚀 Step 3: Deploying to Vercel..."

# Check vercel
if ! command -v vercel &> /dev/null; then
    echo "📥 Installing Vercel CLI..."
    npm install -g vercel
fi

# Deploy
vercel --prod --yes

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   ✅ DEPLOYED: Cyberhound-Web                                    ║"
echo "║                                                                  ║"
echo "║   This is your B2B website (separate from hunting system)        ║"
echo "║                                                                  ║"
echo "║   It connects to:                                                ║"
echo "║   ~/Cyberhound/sovereign_loop.py                                 ║"
echo "║   ~/Cyberhound/LE_BUTIN.json                                     ║"
echo "║                                                                  ║"
echo "║   Send the URL to Toss Bank executives                           ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
