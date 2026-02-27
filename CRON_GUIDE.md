# 🕐 CYBERHOUND CRON GUIDE
**Production Scheduling for Compliance Hunting**

---

## 🤔 Why Cron Instead of Loop?

| Feature | Continuous Loop (`sovereign_loop.py`) | Cron Job (`cron_hunt.py`) |
|---------|--------------------------------------|---------------------------|
| **Resource Usage** | Runs 24/7 (always consuming memory) | Runs on schedule (efficient) |
| **Error Isolation** | One crash stops everything | Each run is independent |
| **Monitoring** | Complex (process managers) | Simple (exit codes, logs) |
| **Recovery** | Needs supervisor/systemd | Cron auto-restarts on failure |
| **Scaling** | Single process | Can run multiple instances |
| **Deployment** | Requires process manager | Works on any Unix/Windows |

**Recommendation:** Use **cron** for production. Use **loop** for development/demo.

---

## 🚀 Quick Setup

### Linux/Mac (Cron)

```bash
# Run setup script
./scripts/setup_cron.sh

# Or manually add to crontab
crontab -e
```

Add this line:
```bash
# Every 30 minutes
*/30 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py >> hound_core/data/logs/cron.log 2>&1
```

### Windows (Task Scheduler)

```powershell
# Run setup script
.\scripts\setup_cron.ps1 -Schedule 30min

# Or manually create task
```

---

## ⚙️ Cron Schedule Examples

### Active Hunting (Recommended Start)
```bash
# Every 30 minutes
*/30 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Use case:** Active prospecting with fresh targets

### Steady State
```bash
# Every hour
0 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Use case:** Ongoing monitoring of existing targets

### Low Volume
```bash
# Every 4 hours
0 */4 * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Use case:** Large target lists (1000+ domains)

### Business Hours Only
```bash
# Every hour, 9 AM to 5 PM, weekdays only
0 9-17 * * 1-5 cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Use case:** B2B prospecting during business hours

### Twice Daily
```bash
# At 9 AM and 5 PM daily
0 9,17 * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Use case:** Balanced monitoring

---

## 🔒 Safety Features

### 1. Lock File (Prevents Overlapping Runs)
```
hound_core/data/.cron_lock
```
If a cron job is still running when the next one starts:
- New job detects lock file
- Exits with code 3 (SKIP)
- Logs: "Another instance is running"

### 2. Exit Codes
| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | ✅ Continue scheduling |
| 1 | Runtime Error | ⚠️ Check logs, alert if persists |
| 2 | Config Error | ❌ No targets configured |
| 3 | Lock Active | ⏭️ Skip (overlapping run) |

### 3. Max Runtime Protection
- Default: 30 minutes max per run
- Prevents stuck processes
- Logs timeout and exits

---

## 📊 Monitoring

### Check Last Run Status
```bash
python3 hound_core/cron_hunt.py --status
```

Output:
```json
{
  "success": true,
  "timestamp": "2026-02-27T08:30:00",
  "duration_seconds": 45.2,
  "targets_hunted": 10,
  "strikes_forged": 3,
  "pending_total": 15,
  "pipeline_value": 45000,
  "exit_code": 0
}
```

### View Logs
```bash
# Real-time
tail -f hound_core/data/logs/cron.log

# Last 100 lines
tail -n 100 hound_core/data/logs/cron.log

# Search for errors
grep "ERROR" hound_core/data/logs/cron.log
```

### Cron Email Alerts
```bash
# Add MAILTO to crontab
MAILTO=admin@yourcompany.com
*/30 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
**Sends email on any output (success or error)**

---

## 🚨 Failure Alerts

### Webhook Alerts
```bash
export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```
Sends POST on failure with:
```json
{
  "text": "🚨 Cyberhound Cron Alert\nCron hunt failed: Connection timeout",
  "timestamp": "2026-02-27T08:30:00"
}
```

### Telegram Alerts
Already configured if you set:
```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

---

## 🔄 Migration: Loop → Cron

### Step 1: Stop Continuous Loop
```bash
# If running in background
pkill -f sovereign_loop.py

# Or press Ctrl+C if in terminal
```

### Step 2: Setup Cron
```bash
./scripts/setup_cron.sh
```

### Step 3: Verify
```bash
# Check cron is installed
crontab -l | grep cyberhound

# Force run once
python3 hound_core/cron_hunt.py

# Check status
python3 hound_core/cron_hunt.py --status
```

---

## 📁 Log Rotation

### Linux (logrotate)
Create `/etc/logrotate.d/cyberhound`:
```
/path/to/cyberhounds-/hound_core/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user user
}
```

### Manual Rotation
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/cyberhounds-/hound_core/data/logs && find . -name "*.log" -mtime +30 -delete
```

---

## 🎯 Production Checklist

### Before Enabling Cron:
- [ ] Targets configured in `targets.txt`
- [ ] Rate limiting appropriate (1 req/sec default)
- [ ] Telegram bot configured (optional)
- [ ] Webhook URL set for alerts (optional)
- [ ] Log directory exists and writable
- [ ] Dry run passes: `python3 hound_core/cron_hunt.py --dry-run`

### After Enabling Cron:
- [ ] Check first run completes: `--status`
- [ ] Verify logs are writing: `tail -f cron.log`
- [ ] Test alert channels (force error)
- [ ] Monitor for 24 hours
- [ ] Check LE_BUTIN.json is updating

---

## 🔧 Advanced Configuration

### Custom Schedule (Crontab Guru)
Use [crontab.guru](https://crontab.guru/) for help:

| Schedule | Description |
|----------|-------------|
| `*/15 * * * *` | Every 15 minutes |
| `0 */6 * * *` | Every 6 hours |
| `0 9,17 * * 1-5` | 9 AM & 5 PM, weekdays |
| `0 0 * * 0` | Weekly (Sundays at midnight) |

### Environment Variables in Cron
```bash
# Add to top of crontab
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
ALERT_WEBHOOK_URL=https://hooks.slack.com/...

# Then your cron job
*/30 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```

### Multiple Cron Jobs
```bash
# High-priority targets (every 30 min)
*/30 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py --high-priority

# All targets (every 4 hours)
0 */4 * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py
```
*(Requires code modification to support --high-priority)*

---

## 🐛 Troubleshooting

### "Lock file exists"
```bash
# Check if process is actually running
ps aux | grep cron_hunt

# If stuck, manually remove lock
rm hound_core/data/.cron_lock

# Or use --force (not recommended for cron)
python3 hound_core/cron_hunt.py --force
```

### "No targets configured"
```bash
# Add targets
echo "stripe.com" >> hound_core/data/targets.txt

# Validate
python3 hound_core/cron_hunt.py --dry-run
```

### "Python not found"
```bash
# Use full path in crontab
*/30 * * * * cd /path/to/cyberhounds- && /usr/bin/python3 hound_core/cron_hunt.py
```

### High Memory Usage
- Reduce target batch size
- Increase cron interval
- Add swap space

---

## 📊 Performance Tuning

### For Large Target Lists (1000+):
```bash
# Every 4 hours with 2 second delays
0 */4 * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py

# Edit swarm.py: DEFAULT_DELAY_BETWEEN_REQUESTS = 2.0
```

### For Fast Scanning (Small Lists):
```bash
# Every 15 minutes with faster rate limiting
*/15 * * * * cd /path/to/cyberhounds- && python3 hound_core/cron_hunt.py

# Edit swarm.py: DEFAULT_DELAY_BETWEEN_REQUESTS = 0.5
```

---

**Cron is the recommended production deployment method. It's reliable, efficient, and industry-standard.**
