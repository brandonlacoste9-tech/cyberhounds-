# 🐺 Cyberhound Web

**Public-facing website and dashboard for the Cyberhound B2B compliance hunting platform.**

This is a **separate repository** from the core Cyberhound hunting system. It communicates with the main system via API.

---

## 🏗️ Architecture

```
┌─────────────────────┐         API Calls          ┌─────────────────────┐
│   Cyberhound-Web    │  ◄──────────────────────►  │    Cyberhound       │
│   (This Repo)       │                            │   (Main System)     │
│                     │                            │                     │
│  • Landing Page     │    GET /api/hunts          │  • sovereign_loop   │
│  • Dashboard UI     │    POST /deploy            │  • scout_http       │
│  • Pitch Decks      │    POST /forge             │  • forge_engine     │
│  • Deal Pipeline    │    POST /strike            │  • envoy_bot        │
└─────────────────────┘                            └─────────────────────┘
         │                                                  │
    Deploy to Vercel                                 Runs on your server
```

---

## 📁 Structure

```
Cyberhound-Web/
├── frontend/                 # Static website files
│   ├── index.html           # B2B landing page
│   ├── css/
│   └── js/
├── api/                     # Backend API (communicates with Cyberhound)
│   └── main.py
├── pitches/                 # Executive pitch documents
│   └── toss_bank_*.md
├── config/                  # Configuration
│   └── cyberhound.json      # Connection settings to main system
├── DEPLOY_NOW.sh           # One-command deployment
├── requirements.txt
└── README.md               # This file
```

---

## 🔌 Connection to Cyberhound Main System

The website connects to your main Cyberhound system via environment variables:

```bash
# .env file
CYBERHOUND_API_URL=http://localhost:8080  # Your main system
CYBERHOUND_TOKEN=your_secret_token         # API auth
TELEGRAM_BOT_TOKEN=xxx                     # For notifications
```

### API Contract

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/hunts` | GET | Fetch recent hunts from LE_BUTIN.json |
| `/api/stats` | GET | Get hunting statistics |
| `/api/deploy` | POST | Deploy scout pack |
| `/api/forge` | POST | Generate solution for lead |
| `/api/strike` | POST | Send strike email |

---

## 🚀 Deploy

```bash
# Install
pip install -r requirements.txt

# Local dev
python api/main.py

# Production (Vercel)
vercel --prod
```

---

## 🎯 Purpose

- **Public face** for Toss Bank, enterprise prospects
- **Dashboard** to monitor hunts without touching core code
- **Pitch delivery** system for executives
- **Deal pipeline** visualization

**Keep it separate. Keep it safe. Keep it hunting.** 🐺⚡
