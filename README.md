# 🐺 Cyberhound B2B v2.1

**Autonomous Compliance Gap Hunting for Enterprise**

The new, better system. No deal hunter. Pure B2B compliance strikes.

---

## 🎯 What This Is

Cyberhound hunts **$5K-25K B2B compliance deals**:
- Quebec **Law 25** (privacy)
- Quebec **Bill 96** (AI disclosure)
- **Article 34** (data breach notification)
- **GDPR/CCPA** gaps

**Human-on-the-Loop (HOTL)**: Approve strikes from your phone via Telegram.

---

## 🏗️ Architecture

```
📁 hound_core/           ← THE HUNTING SYSTEM
   ├── sovereign_loop.py ← Master controller with Telegram HOTL
   ├── cron_hunt.py      ← ⭐ PRODUCTION: Cron job wrapper
   ├── swarm.py          ← 20-hound parallel scrapers (rate limited)
   ├── envoy_bot.py      ← Telegram notifications
   ├── target_discovery.py # Prospecting guidance
   └── data/             ← LE_BUTIN.json (leads database)

📁 web_dashboard/        ← THE WEBSITE
   └── index.html        ← Live dashboard

📁 tests/                ← UNIT TESTS
   ├── test_swarm.py     # 500+ lines of tests
   └── test_sovereign.py # 300+ lines of tests

📁 scripts/              ← DEPLOYMENT SCRIPTS
   ├── setup_cron.sh     # Linux/Mac cron setup
   └── setup_cron.ps1    # Windows Task Scheduler setup

📁 pitches/              ← B2B sales materials
```

---

## 🚀 Quick Start (Development)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Add Targets
```bash
# Edit the targets file
echo "stripe.com" > hound_core/data/targets.txt
```

### 3. Run Tests
```bash
python run_tests.py
```

### 4. Quick Hunt (One-Time)
```bash
cd hound_core
python sovereign_loop.py --quick stripe.com
```

### 5. View Dashboard
```bash
cd web_dashboard
python -m http.server 8080
# Open http://localhost:8080
```

---

## 🕐 Production Deployment (Cron - RECOMMENDED)

### Linux/Mac
```bash
# Run interactive setup
./scripts/setup_cron.sh

# Or manually: Add to crontab (every 30 minutes)
crontab -e
# Add: */30 * * * * cd /path/to/cyberhound && python3 hound_core/cron_hunt.py
```

### Windows
```powershell
# Run interactive setup
.\scripts\setup_cron.ps1 -Schedule 30min
```

### Why Cron?
- ✅ Resource efficient (doesn't run 24/7)
- ✅ Error isolation (each run is independent)
- ✅ Simple monitoring (exit codes, logs)
- ✅ Auto-restart on failure
- ✅ Industry standard

**See [CRON_GUIDE.md](CRON_GUIDE.md) for detailed scheduling options.**

---

## 🔄 Continuous Loop (Alternative)

For demos or when you want real-time processing:

```bash
cd hound_core
python sovereign_loop.py  # Runs forever, every 30 min
```

**Not recommended for production** - use cron instead.

---

## 🐺 The 20-Hound Swarm

| Hound | Specialty | Target | Rate Limit |
|-------|-----------|--------|------------|
| Québec (×5) | Law 25 gaps | $25K fines | 1 req/sec |
| Loi 96 (×5) | AI disclosure | $50K fines | 1 req/sec |
| Cali (×5) | CCPA gaps | $7.5K fines | 1 req/sec |
| Euro (×5) | GDPR gaps | €20M fines | 1 req/sec |

**Rate Limiting:** Configurable delays between requests (default: 1 sec)

---

## 💰 Deal Flow

```
Scout → Forge → Command (Telegram) → Strike
  ↓       ↓          ↓                ↓
Find  → Price  →  Approve?        Deploy
Gap     Deal     [✅/❌/❓]         Contractor
```

---

## 📱 Telegram HOTL

Get alerts like:

```
🚨 COMPLIANCE GAP DETECTED

Company: FinTech Inc
Gap: AI not disclosed (Bill 96)
Risk: $50,000 fine

💰 PROPOSED: $15,000
ROI: 3.3x cost avoidance

Reply: ✅ APPROVE | ❌ VETO | ❓ ASK
```

**Setup:**
1. Create bot with [@BotFather](https://t.me/botfather)
2. Get your chat ID
3. Set environment variables
4. Bot auto-initializes on startup

---

## 🧪 Testing

### Run Tests
```bash
# All tests
python run_tests.py

# With coverage
python run_tests.py --coverage

# Specific test file
python run_tests.py --type swarm
```

### Test Coverage
| Module | Tests | Coverage |
|--------|-------|----------|
| swarm.py | 15+ | 85%+ |
| sovereign_loop.py | 10+ | 80%+ |
| envoy_bot.py | 5+ | 75%+ |
| cron_hunt.py | 5+ | 80%+ |

---

## 📊 Cron Monitoring

### Check Status
```bash
python hound_core/cron_hunt.py --status
```

### View Logs
```bash
tail -f hound_core/data/logs/cron.log
```

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime Error |
| 2 | No Targets Configured |
| 3 | Overlapping Run (Lock) |

---

## ⚙️ Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | - | Telegram chat ID |
| `CYCLE_INTERVAL` | 1800 | Seconds between hunts (loop mode) |
| `RATE_LIMIT_DELAY` | 1.0 | Seconds between requests |
| `ALERT_WEBHOOK_URL` | - | Webhook for failure alerts |

### Command Line Options
```bash
# Quick hunt
python sovereign_loop.py --quick domain1.com domain2.com

# Fast mode (no rate limiting - careful!)
python sovereign_loop.py --quick stripe.com --fast

# Show prospecting guide
python sovereign_loop.py --discover

# Cron: Check status
python hound_core/cron_hunt.py --status

# Cron: Dry run (validate config)
python hound_core/cron_hunt.py --dry-run

# Version
python sovereign_loop.py --version
```

---

## 🛡️ Production Features

### ✅ Implemented
- **Cron Support** - Production scheduling
- **Rate Limiting** - Polite scraping
- **Lock Files** - Prevents overlapping runs
- **Retry Logic** - Automatic retry on errors
- **Exit Codes** - Proper cron integration
- **Error Handling** - Specific exceptions
- **Telegram HOTL** - Mobile approval
- **Unit Tests** - 25+ tests
- **Graceful Shutdown** - SIGINT/SIGTERM
- **File Persistence** - JSON storage
- **Domain Validation** - Prevents invalid targets
- **Log Rotation** - Configurable

### 🚧 Roadmap
- [ ] Proxy rotation for scale
- [ ] PostgreSQL backend
- [ ] Web dashboard authentication
- [ ] Slack/Discord integrations
- [ ] ML-based gap detection
- [ ] Automated pitch generation

---

## 📊 System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.8+ |
| RAM | 512 MB minimum |
| Disk | 100 MB |
| Network | HTTP/HTTPS outbound |
| Cron | Optional (for production) |
| Telegram | Optional (for HOTL) |

---

## 📚 Documentation

- [CRON_GUIDE.md](CRON_GUIDE.md) - Production scheduling
- [REAL_VERIFICATION.md](REAL_VERIFICATION.md) - Proof of realness
- [REPO_REVIEW.md](REPO_REVIEW.md) - Code review
- [TEST_REPORT.md](TEST_REPORT.md) - Test results

---

**The better system. No old deal hunter code. Clean B2B hunting.**
