# 🏗️ Cyberhound Dual-Repository Architecture

## Overview

Cyberhound operates across **two separate repositories** for security and deployment flexibility:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DEPLOYMENT                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐         ┌──────────────────────────────┐        │
│   │  Cyberhound-Web  │◄────────┤     Vercel/Railway           │        │
│   │  (This Repo)     │  HTTP   │     Public Website           │        │
│   │  - Website       │         │                              │        │
│   │  - Dashboard     │         └──────────────────────────────┘        │
│   │  - API Bridge    │                                                  │
│   └────────┬─────────┘                                                  │
│            │ API Calls                                                  │
│            ▼                                                            │
│   ┌──────────────────┐         ┌──────────────────────────────┐        │
│   │  Cyberhound/     │◄────────┤    Local Server/VPS          │        │
│   │  (Main System)   │  SSH    │    (Secret Sauce)            │        │
│   │  - sovereign_    │         │                              │        │
│   │    loop.py       │         └──────────────────────────────┘        │
│   │  - scout_http.py │                                                  │
│   │  - forge_engine  │                                                  │
│   │  - 20-hound      │                                                  │
│   │    swarm         │                                                  │
│   └──────────────────┘                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 Repository 1: Cyberhound-Web (This Repo)

**Purpose**: Public-facing website and dashboard  
**Deployment**: Vercel, Railway, or any static host  
**Security**: Safe to deploy - contains no hunting logic

### Contents:
- `frontend/index.html` - Landing page, dashboard, deal flow
- `api/main.py` - FastAPI bridge to main system
- `config/cyberhound.json` - Connection configuration
- `pitches/` - B2B sales materials

### Key Files:
| File | Purpose |
|------|---------|
| `frontend/index.html` | B2B website with compliance focus |
| `api/main.py` | API bridge to Cyberhound/ system |
| `config/cyberhound.json` | Connection settings |

### API Endpoints:
- `GET /api/status` - Check connection to main system
- `POST /api/deploy/{pack_id}` - Trigger deployment
- `GET /api/ledger` - View hunting results

---

## 🐺 Repository 2: Cyberhound/ (Main System)

**Purpose**: Core hunting intelligence (kept private)  
**Deployment**: Local server, VPS, or self-hosted  
**Security**: Contains proprietary hunting algorithms

### Contents:
- `sovereign_loop.py` - Master HOTL controller
- `scout_http.py` - 20-hound swarm scouts
- `forge_engine.py` - Deal analyzer
- `envoy_bot.py` - Telegram integration
- `LE_BUTIN.json` - Hunting results database

### Key Files:
| File | Purpose |
|------|---------|
| `sovereign_loop.py` | Main hunting loop with Telegram approval |
| `scout_http.py` | Parallel scouting across jurisdictions |
| `forge_engine.py` | B2B deal analysis and pricing |
| `envoy_bot.py` | Telegram HOTL notifications |
| `LE_BUTIN.json` | Strike database (read by website) |

---

## 🔌 Connection Methods

### Method 1: File-Based (Recommended)
The website reads `LE_BUTIN.json` from the main system:

```python
# In Cyberhound-Web/api/main.py
BUTIN_PATH = "~/Cyberhound/LE_BUTIN.json"

@app.get("/api/ledger")
async def get_ledger():
    with open(BUTIN_PATH) as f:
        return json.load(f)
```

### Method 2: HTTP API
The website can call the main system's API:

```python
# In Cyberhound-Web/api/main.py
MAIN_SYSTEM_URL = "http://localhost:8001"

@app.post("/api/deploy/{pack_id}")
async def deploy_pack(pack_id: str):
    response = requests.post(
        f"{MAIN_SYSTEM_URL}/deploy/{pack_id}"
    )
    return response.json()
```

### Method 3: WebSocket (Real-time)
For live dashboard updates:

```python
# WebSocket connection for real-time strike updates
@app.websocket("/ws/strikes")
async def websocket_strikes(websocket: WebSocket):
    await websocket.accept()
    while True:
        strikes = read_butin()
        await websocket.send_json(strikes)
        await asyncio.sleep(5)
```

---

## 🚀 Deployment Workflow

### Website Only (Cyberhound-Web/):
```bash
# Deploy just the website
cd ~/Cyberhound-Web
./DEPLOY_NOW.sh
# or
vercel --prod
```

### Main System (Cyberhound/):
```bash
# Run locally (kept private)
cd ~/Cyberhound
python sovereign_loop.py
```

### Both Together:
```bash
# Terminal 1: Run main system
cd ~/Cyberhound && python sovereign_loop.py

# Terminal 2: Deploy website
cd ~/Cyberhound-Web && vercel --prod
```

---

## 🛡️ Security Model

### What's Safe to Deploy (This Repo):
- ✅ Website frontend
- ✅ Dashboard UI
- ✅ API bridge code
- ✅ Public pitch decks
- ✅ Configuration files

### What's Private (Main Repo):
- 🔒 Hunting algorithms
- 🔒 Scout implementations
- 🔒 Strike database (LE_BUTIN.json)
- 🔒 Telegram bot tokens
- 🔒 API keys and credentials

### Separation Benefits:
1. **Public website can be open-sourced**
2. **Main system stays private/secure**
3. **Website can scale independently**
4. **Easy to change deployment targets**
5. **No credential exposure risk**

---

## 📁 File Mapping

| Cyberhound-Web/ | Connects To | Cyberhound/ |
|-----------------|-------------|-------------|
| `api/main.py` | → | `sovereign_loop.py` |
| `config/cyberhound.json` | → | Root config |
| `frontend/index.html` | → | `LE_BUTIN.json` (read-only) |
| `pitches/` | → | `pitches/` (synced) |

---

## 🎯 Quick Start

### View Website Locally:
```bash
cd ~/Cyberhound-Web
python -m http.server 8080 --directory frontend
# Open http://localhost:8080
```

### Deploy Website:
```bash
cd ~/Cyberhound-Web
./DEPLOY_NOW.sh
```

### Run Main System:
```bash
cd ~/Cyberhound
python sovereign_loop.py
```

---

**Key Principle**: Website shows the results. Main system does the hunting. They communicate through APIs and shared files, not direct code coupling.
