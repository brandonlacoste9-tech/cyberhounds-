# 🐺 Cyberhound B2B

**Autonomous Compliance Gap Hunting for Enterprise**

The new, better system. No deal hunter. Pure B2B compliance strikes.

---

## 🎯 What This Is

Cyberhound hunts **$5K-25K B2B compliance deals**:
- Quebec **Law 25** (privacy)
- Quebec **Bill 96** (AI disclosure)
- **Article 34** (data breach notification)
- **GDPR/CCPA** gaps

**Human-on-the-Loop (HOTL)**: You approve strikes from your phone via Telegram.

---

## 🏗️ Architecture

```
📁 hound_core/           ← THE HUNTING SYSTEM
   ├── sovereign_loop.py ← Master controller
   ├── swarm.py          ← 20-hound parallel scouts
   └── data/             ← LE_BUTIN.json (leads database)

📁 web_dashboard/        ← THE WEBSITE
   └── index.html        ← Live dashboard

📁 pitches/              ← B2B sales materials
```

---

## 🚀 Quick Start

```bash
# 1. Run the hunting system
cd hound_core
python sovereign_loop.py

# 2. View dashboard
cd web_dashboard
python -m http.server 8080
# Open http://localhost:8080
```

---

## 🐺 The 20-Hound Swarm

| Hound | Specialty | Target |
|-------|-----------|--------|
| Québec (×5) | Law 25 gaps | $25K fines |
| Loi 96 (×5) | AI disclosure | $50K fines |
| Cali (×5) | CCPA gaps | $7.5K fines |
| Euro (×5) | GDPR gaps | €20M fines |

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

---

**The better system. No old deal hunter code. Clean B2B hunting.**
