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
   ├── swarm.py          ← 20-hound parallel scrapers (rate limited)
   ├── envoy_bot.py      ← Telegram notifications
   ├── target_discovery.py # Prospecting guidance
   └── data/             ← LE_BUTIN.json (leads database)

📁 web_dashboard/        ← THE WEBSITE
   └── index.html        ← Live dashboard

📁 tests/                ← UNIT TESTS
   ├── test_swarm.py     # 500+ lines of tests
   └── test_sovereign.py # 300+ lines of tests

📁 pitches/              ← B2B sales materials
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure Telegram (Optional)
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Add Targets
```bash
# Edit the targets file
echo "stripe.com" > hound_core/data/targets.txt
```

### 4. Run Tests
```bash
# Run all tests
python run_tests.py

# With coverage
python run_tests.py --coverage

# Specific test file
python run_tests.py --type swarm
```

### 5. Run the Hunt
```bash
# Quick hunt (one-time)
cd hound_core
python sovereign_loop.py --quick stripe.com

# Full sovereign loop (every 30 min)
python sovereign_loop.py
```

### 6. View Dashboard
```bash
cd web_dashboard
python -m http.server 8080
# Open http://localhost:8080
```

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

# Unit tests only
python run_tests.py --type unit

# Integration tests
python run_tests.py --type integration

# With coverage report
python run_tests.py --coverage

# Verbose output
python run_tests.py -v
```

### Test Coverage
| Module | Tests | Coverage |
|--------|-------|----------|
| swarm.py | 15+ | 85%+ |
| sovereign_loop.py | 10+ | 80%+ |
| envoy_bot.py | 5+ | 75%+ |

---

## ⚙️ Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | - | Telegram chat ID |
| `CYCLE_INTERVAL` | 1800 | Seconds between hunts |
| `RATE_LIMIT_DELAY` | 1.0 | Seconds between requests |

### Command Line Options
```bash
# Quick hunt
python sovereign_loop.py --quick domain1.com domain2.com

# Fast mode (no rate limiting - careful!)
python sovereign_loop.py --quick stripe.com --fast

# Show prospecting guide
python sovereign_loop.py --discover

# Version
python sovereign_loop.py --version
```

---

## 🛡️ Production Features

### ✅ Implemented
- **Rate Limiting** - Polite scraping (1 req/sec)
- **Retry Logic** - Automatic retry on 429/5xx errors
- **Error Handling** - Specific exceptions with logging
- **Telegram HOTL** - Mobile approval workflow
- **Unit Tests** - 25+ comprehensive tests
- **Graceful Shutdown** - SIGINT/SIGTERM handling
- **File Persistence** - JSON data storage
- **Domain Validation** - Prevents invalid targets

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
| Telegram | Optional (for HOTL) |

---

**The better system. No old deal hunter code. Clean B2B hunting.**
