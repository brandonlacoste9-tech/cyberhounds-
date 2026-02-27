#!/usr/bin/env python3
"""
🖥️ CYBERHOUND CLI DASHBOARD
Terminal-based dashboard for quick stats without opening browser.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
    "white": "\033[97m",
}

DATA_DIR = Path(__file__).parent / "data"


def color(text: str, color_name: str) -> str:
    """Add color to text."""
    return f"{COLORS.get(color_name, '')}{text}{COLORS['reset']}"


def box(title: str, content: str, width: int = 50) -> str:
    """Create a boxed section."""
    lines = [
        f"┌{'─' * (width - 2)}┐",
        f"│ {color(title, 'bold'):<{width-4}} │",
        f"├{'─' * (width - 2)}┤",
    ]
    for line in content.split('\n'):
        lines.append(f"│ {line:<{width-4}} │")
    lines.append(f"└{'─' * (width - 2)}┘")
    return '\n'.join(lines)


def load_json_file(filename: str) -> Optional[Dict]:
    """Load a JSON file from data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def format_currency(value: int) -> str:
    """Format number as currency."""
    if value >= 1000000:
        return f"${value/1000000:.1f}M"
    elif value >= 1000:
        return f"${value/1000:.1f}K"
    return f"${value}"


def format_time_ago(timestamp: str) -> str:
    """Format ISO timestamp as 'X minutes ago'."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return "unknown"


def show_dashboard():
    """Display the CLI dashboard."""
    # Clear screen (cross-platform)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print()
    print(color("🐺  CYBERHOUND DASHBOARD", "bold"))
    print(color("   B2B Compliance Hunting System", "gray"))
    print()
    
    # Load data
    butin = load_json_file("LE_BUTIN.json")
    pending = load_json_file("pending_strikes.json")
    settled = load_json_file("settled_strikes.json")
    cron_state = load_json_file("cron_state.json")
    
    # Header stats
    if butin:
        print(color("📊 HUNT STATISTICS", "cyan"))
        print(f"  Last Hunt:     {format_time_ago(butin.get('timestamp', ''))}")
        print(f"  Cycle:         #{butin.get('cycle', 0)}")
        print(f"  Targets:       {butin.get('targets_hunted', 0)}")
        print(f"  Strikes:       {butin.get('strikes_forged', 0)}")
        print()
    
    # Pipeline
    pipeline_value = 0
    if pending:
        pipeline_value = sum(p.get('proposed_price', 0) for p in pending)
    
    print(color("💰 PIPELINE", "green"))
    print(f"  Pending:       {len(pending) if pending else 0} strikes")
    print(f"  Value:         {color(format_currency(pipeline_value), 'green')}")
    print(f"  Settled:       {len(settled) if settled else 0} deals")
    print()
    
    # Latest strikes
    if pending and len(pending) > 0:
        print(color("🚨 LATEST STRIKES", "red"))
        for strike in pending[-5:]:  # Show last 5
            severity = strike.get('severity', 'MEDIUM')
            sev_color = "red" if severity == "CRITICAL" else "yellow" if severity == "HIGH" else "gray"
            
            print(f"  {color('●', sev_color)} {strike.get('company', 'Unknown')[:20]:<20} "
                  f"{strike.get('gap_type', 'unknown').upper():<12} "
                  f"{format_currency(strike.get('proposed_price', 0)):>8}")
        print()
    
    # Cron status
    if cron_state:
        status = "✅" if cron_state.get('success') else "❌"
        status_text = color("Healthy", "green") if cron_state.get('success') else color("Failed", "red")
        print(color("🕐 CRON STATUS", "cyan"))
        print(f"  Last Run:      {format_time_ago(cron_state.get('timestamp', ''))}")
        print(f"  Status:        {status} {status_text}")
        print(f"  Duration:      {cron_state.get('duration_seconds', 0):.1f}s")
        print()
    
    # Quick actions
    print(color("⚡ QUICK ACTIONS", "white"))
    print("  make quick      - Run quick hunt")
    print("  make cron-run   - Run cron hunt")
    print("  make dashboard  - Start web dashboard")
    print("  make test       - Run tests")
    print()


def show_mini_status():
    """Show one-line status for shell prompts."""
    butin = load_json_file("LE_BUTIN.json")
    pending = load_json_file("pending_strikes.json")
    
    if not butin:
        print("🐺 No hunts yet")
        return
    
    pending_count = len(pending) if pending else 0
    pipeline = sum(p.get('proposed_price', 0) for p in pending) if pending else 0
    
    print(f"🐺 Cycle #{butin.get('cycle', 0)} | "
          f"Pending: {pending_count} | "
          f"Pipeline: {format_currency(pipeline)}")


def watch_mode():
    """Continuously update dashboard (like top command)."""
    import time
    
    try:
        while True:
            show_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--mini":
            show_mini_status()
        elif sys.argv[1] == "--watch":
            watch_mode()
        else:
            show_dashboard()
    else:
        show_dashboard()
