#!/bin/bash
#
# 🐺 CYBERHOUND CRON SETUP
# Sets up scheduled hunting via cron
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CRON_HUNTER="$PROJECT_DIR/hound_core/cron_hunt.py"

echo "🐺 Cyberhound Cron Setup"
echo "========================"

# Check if cron hunter exists
if [ ! -f "$CRON_HUNTER" ]; then
    echo "❌ cron_hunt.py not found at $CRON_HUNTER"
    exit 1
fi

echo "✅ Found cron_hunt.py"

# Detect cron service
if command -v crontab &> /dev/null; then
    CRON_TYPE="crontab"
elif command -v systemctl &> /dev/null && systemctl list-units --type=service | grep -q cron; then
    CRON_TYPE="systemd"
else
    echo "⚠️  No cron service detected"
    echo "   You may need to install cron:"
    echo "   Ubuntu/Debian: sudo apt-get install cron"
    echo "   CentOS/RHEL:   sudo yum install cronie"
    exit 1
fi

echo "✅ Detected: $CRON_TYPE"

# Validate configuration
echo ""
echo "🔍 Validating configuration..."
cd "$PROJECT_DIR"
python3 "$CRON_HUNTER" --dry-run

if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed"
    echo "   Please configure targets in hound_core/data/targets.txt"
    exit 1
fi

echo "✅ Configuration valid"

# Setup options
echo ""
echo "📅 Cron Schedule Options:"
echo "  1) Every 30 minutes (recommended for active hunting)"
echo "  2) Every hour"
echo "  3) Every 4 hours"
echo "  4) Daily at 9 AM"
echo "  5) Custom (advanced)"
echo ""
read -p "Select option (1-5): " SCHEDULE_OPTION

case $SCHEDULE_OPTION in
    1)
        CRON_SCHEDULE="*/30 * * * *"
        echo "Selected: Every 30 minutes"
        ;;
    2)
        CRON_SCHEDULE="0 * * * *"
        echo "Selected: Every hour"
        ;;
    3)
        CRON_SCHEDULE="0 */4 * * *"
        echo "Selected: Every 4 hours"
        ;;
    4)
        CRON_SCHEDULE="0 9 * * *"
        echo "Selected: Daily at 9 AM"
        ;;
    5)
        echo ""
        echo "Enter custom cron schedule:"
        echo "Format: minute hour day month weekday"
        echo "Examples:"
        echo "  */15 * * * *  = Every 15 minutes"
        echo "  0 */6 * * *   = Every 6 hours"
        echo "  0 9,17 * * *  = At 9 AM and 5 PM"
        read -p "Schedule: " CRON_SCHEDULE
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

# Setup cron job
CRON_CMD="cd $PROJECT_DIR && /usr/bin/python3 $CRON_HUNTER >> $PROJECT_DIR/hound_core/data/logs/cron.log 2>&1"
CRON_JOB="$CRON_SCHEDULE $CRON_CMD"

echo ""
echo "📝 Cron job to add:"
echo "  Schedule: $CRON_SCHEDULE"
echo "  Command:  $CRON_CMD"
echo ""
read -p "Add this cron job? (y/N): " CONFIRM

if [[ $CONFIRM =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null || echo "") | grep -v "cron_hunt.py" | { cat; echo "$CRON_JOB"; } | crontab -
    
    echo "✅ Cron job added"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "cron_hunt" || echo "  (not found - check crontab manually)"
    
    echo ""
    echo "📊 To check status:"
    echo "  python3 hound_core/cron_hunt.py --status"
    echo ""
    echo "📜 To view logs:"
    echo "  tail -f hound_core/data/logs/cron.log"
    
else
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "✅ Cron setup complete!"
echo ""
echo "Next steps:"
echo "  1. Ensure targets are configured"
echo "  2. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (optional)"
echo "  3. Set ALERT_WEBHOOK_URL for failure alerts (optional)"
echo "  4. Monitor hound_core/data/logs/cron.log"
