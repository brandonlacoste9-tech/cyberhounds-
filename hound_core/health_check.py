#!/usr/bin/env python3
"""
🏥 CYBERHOUND HEALTH CHECK
System diagnostics for monitoring and troubleshooting.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR = DATA_DIR / "logs"


def check_file_exists(filepath: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if filepath.exists():
        size = filepath.stat().st_size
        return True, f"✅ {description}: {size} bytes"
    return False, f"❌ {description}: Not found"


def check_json_valid(filepath: Path) -> Tuple[bool, str]:
    """Check if a JSON file is valid."""
    try:
        with open(filepath) as f:
            json.load(f)
        return True, "✅ Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"


def check_env_vars() -> List[Tuple[bool, str]]:
    """Check environment variable configuration."""
    results = []
    
    # Optional but recommended
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_token != "YOUR_BOT_TOKEN":
        masked = telegram_token[:10] + "..." + telegram_token[-4:]
        results.append((True, f"✅ TELEGRAM_BOT_TOKEN: {masked}"))
        if telegram_chat:
            results.append((True, f"✅ TELEGRAM_CHAT_ID: {telegram_chat}"))
        else:
            results.append((False, "❌ TELEGRAM_CHAT_ID: Not set (needed with token)"))
    else:
        results.append((False, "⚠️  TELEGRAM_BOT_TOKEN: Not configured (optional)"))
    
    # Check rate limiting
    rate_limit = os.getenv("RATE_LIMIT_DELAY", "1.0")
    results.append((True, f"ℹ️  RATE_LIMIT_DELAY: {rate_limit}s"))
    
    return results


def check_targets() -> Tuple[bool, str]:
    """Check if targets are configured."""
    targets_file = DATA_DIR / "targets.txt"
    
    if not targets_file.exists():
        return False, "❌ targets.txt: Not found"
    
    lines = targets_file.read_text().strip().split('\n')
    targets = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
    
    if not targets:
        return False, "❌ targets.txt: No valid targets (only comments/empty lines)"
    
    return True, f"✅ targets.txt: {len(targets)} targets configured"


def check_recent_activity() -> Tuple[bool, str]:
    """Check if hunts have run recently."""
    butin_file = DATA_DIR / "LE_BUTIN.json"
    
    if not butin_file.exists():
        return False, "⚠️  No hunts yet (LE_BUTIN.json not found)"
    
    try:
        data = json.loads(butin_file.read_text())
        timestamp = data.get('timestamp')
        
        if not timestamp:
            return False, "❌ LE_BUTIN.json: No timestamp"
        
        last_run = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(last_run.tzinfo) if last_run.tzinfo else datetime.now()
        
        hours_since = (now - last_run).total_seconds() / 3600
        
        if hours_since < 1:
            return True, f"✅ Last hunt: {hours_since:.1f}h ago (recent)"
        elif hours_since < 24:
            return True, f"⚠️  Last hunt: {hours_since:.1f}h ago"
        else:
            return False, f"❌ Last hunt: {hours_since:.1f}h ago (stale)"
            
    except Exception as e:
        return False, f"❌ Error checking activity: {e}"


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space."""
    try:
        stat = os.statvfs(DATA_DIR)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        
        if free_gb < 1:
            return False, f"❌ Disk space: {free_gb:.1f}GB free (low!)"
        elif free_gb < 5:
            return (True, f"⚠️  Disk space: {free_gb:.1f}GB free")
        else:
            return (True, f"✅ Disk space: {free_gb:.1f}GB free")
    except Exception as e:
        return False, f"❌ Cannot check disk space: {e}"


def check_dependencies() -> List[Tuple[bool, str]]:
    """Check if Python dependencies are installed."""
    results = []
    
    required = [
        ("aiohttp", "HTTP client"),
        ("telegram", "Telegram bot (optional)"),
    ]
    
    for module, description in required:
        try:
            __import__(module)
            results.append((True, f"✅ {module}: Installed"))
        except ImportError:
            if "optional" in description:
                results.append((True, f"⚠️  {module}: Not installed ({description})"))
            else:
                results.append((False, f"❌ {module}: Not installed ({description})"))
    
    return results


def check_health() -> Dict:
    """Run all health checks and return results."""
    print("🏥 CYBERHOUND HEALTH CHECK")
    print("=" * 60)
    print()
    
    all_checks = []
    
    # File structure
    print("📁 FILE STRUCTURE:")
    checks = [
        check_file_exists(DATA_DIR / "LE_BUTIN.json", "LE_BUTIN.json"),
        check_file_exists(DATA_DIR / "pending_strikes.json", "pending_strikes.json"),
        check_file_exists(DATA_DIR / "targets.txt", "targets.txt"),
    ]
    for ok, msg in checks:
        print(f"  {msg}")
        all_checks.append(ok)
    print()
    
    # Configuration
    print("⚙️  CONFIGURATION:")
    checks = check_env_vars()
    for ok, msg in checks:
        print(f"  {msg}")
        all_checks.append(ok)
    
    ok, msg = check_targets()
    print(f"  {msg}")
    all_checks.append(ok)
    print()
    
    # Activity
    print("🕐 ACTIVITY:")
    ok, msg = check_recent_activity()
    print(f"  {msg}")
    all_checks.append(ok)
    print()
    
    # System
    print("💻 SYSTEM:")
    ok, msg = check_disk_space()
    print(f"  {msg}")
    all_checks.append(ok)
    
    checks = check_dependencies()
    for ok, msg in checks:
        print(f"  {msg}")
        all_checks.append(ok)
    print()
    
    # Summary
    passed = sum(all_checks)
    total = len(all_checks)
    
    print("=" * 60)
    if passed == total:
        print(color("✅ ALL CHECKS PASSED", "green"))
    elif passed >= total * 0.7:
        print(color(f"⚠️  MOSTLY HEALTHY ({passed}/{total} checks passed)", "yellow"))
    else:
        print(color(f"❌ ISSUES FOUND ({passed}/{total} checks passed)", "red"))
    print()
    
    return {
        "healthy": passed == total,
        "passed": passed,
        "total": total,
        "timestamp": datetime.now().isoformat()
    }


def color(text: str, color_name: str) -> str:
    """Add ANSI color."""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color_name, '')}{text}{colors['reset']}"


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cyberhound Health Check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit 1 on warnings")
    
    args = parser.parse_args()
    
    result = check_health()
    
    if args.json:
        print(json.dumps(result, indent=2))
    
    # Exit code
    if not result["healthy"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
