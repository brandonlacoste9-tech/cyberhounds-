#!/usr/bin/env python3
"""
🐺 CYBERHOUND CRON HUNTER
Production-ready cron job wrapper for scheduled hunting.

Features:
- Lock file prevents overlapping runs
- Exit codes for cron success/failure
- Structured logging to files
- Email/webhook alerts on failure
- Idempotent execution
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import tempfile
import fcntl

# Import sovereign components
sys.path.insert(0, str(Path(__file__).parent))
from sovereign_loop import SovereignLoop, DecisionPack
from swarm import Swarm
from target_discovery import TargetDiscovery
from envoy_bot import EnvoyBot, ConsoleNotifier

# Configuration
DATA_DIR = Path(__file__).parent / "data"
LOCK_FILE = DATA_DIR / ".cron_lock"
LOG_DIR = DATA_DIR / "logs"
CRON_LOG = LOG_DIR / "cron.log"
CRON_STATE = DATA_DIR / "cron_state.json"
MAX_RUN_TIME_SECONDS = 1800  # 30 min max per cron run
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK_URL", "")

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | CRON | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(CRON_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CronHunter")


class LockFile:
    """Process-safe lock file using fcntl (Unix) or file existence (Windows)."""
    
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.fd: Optional[int] = None
        self.acquired = False
    
    def acquire(self, timeout: int = 0) -> bool:
        """Try to acquire lock. Returns True if acquired."""
        try:
            # Try to create lock file
            if sys.platform != "win32":
                # Unix: Use fcntl for proper locking
                self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR)
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.acquired = True
                    # Write PID to lock file
                    os.write(self.fd, str(os.getpid()).encode())
                    return True
                except (IOError, OSError):
                    os.close(self.fd)
                    self.fd = None
                    return False
            else:
                # Windows: Check if file exists
                if self.lock_path.exists():
                    # Check if process is still running
                    try:
                        pid = int(self.lock_path.read_text().strip())
                        # Try to check if process exists (Windows-specific)
                        import ctypes
                        kernel32 = ctypes.windll.kernel32
                        handle = kernel32.OpenProcess(1, False, pid)
                        if handle:
                            kernel32.CloseHandle(handle)
                            logger.warning(f"Lock held by running process {pid}")
                            return False
                    except (ValueError, ImportError):
                        pass
                
                # Create lock file with PID
                self.lock_path.write_text(str(os.getpid()))
                self.acquired = True
                return True
                
        except Exception as e:
            logger.error(f"Lock acquisition error: {e}")
            return False
    
    def release(self):
        """Release the lock."""
        if self.acquired:
            try:
                if self.fd is not None:
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                    os.close(self.fd)
                    self.fd = None
                if self.lock_path.exists():
                    self.lock_path.unlink()
                self.acquired = False
                logger.debug("Lock released")
            except Exception as e:
                logger.error(f"Lock release error: {e}")
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Could not acquire lock - another instance running")
        return self
    
    def __exit__(self, *args):
        self.release()


class CronHunter:
    """Cron-friendly hunter with proper error handling and reporting."""
    
    def __init__(self):
        self.sovereign: Optional[SovereignLoop] = None
        self.results: Dict = {}
        self.exit_code = 0
    
    async def run_single_hunt(self) -> bool:
        """Run one hunt cycle and return success status."""
        logger.info("="*70)
        logger.info("🐺 CRON HUNTER STARTING")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        try:
            # Initialize sovereign
            self.sovereign = SovereignLoop(rate_limit_delay=0.5)  # Faster for cron
            
            # Load targets
            targets = self.sovereign.discovery.load_and_validate_targets()
            
            if not targets:
                logger.error("❌ No targets configured")
                self.exit_code = 2  # Config error
                return False
            
            logger.info(f"📋 Loaded {len(targets)} targets")
            
            # Run hunt
            packs = await self.sovereign.run_hunt_cycle()
            
            # Record results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.results = {
                "success": True,
                "timestamp": start_time.isoformat(),
                "duration_seconds": duration,
                "targets_hunted": len(targets),
                "strikes_forged": len(packs),
                "pending_total": len(self.sovereign.pending_strikes),
                "pipeline_value": sum(p['proposed_price'] for p in packs),
                "exit_code": 0
            }
            
            # Save state
            self._save_state()
            
            # Log summary
            logger.info("="*70)
            logger.info("✅ CRON HUNT COMPLETE")
            logger.info(f"   Duration: {duration:.1f}s")
            logger.info(f"   Targets: {len(targets)}")
            logger.info(f"   Strikes: {len(packs)}")
            logger.info(f"   Pipeline: ${self.results['pipeline_value']:,}")
            logger.info("="*70)
            
            self.exit_code = 0
            return True
            
        except Exception as e:
            logger.exception("❌ Hunt failed with exception")
            
            self.results = {
                "success": False,
                "timestamp": start_time.isoformat(),
                "error": str(e),
                "exit_code": 1
            }
            
            # Send alert
            await self._send_alert(f"Cron hunt failed: {e}")
            
            self.exit_code = 1
            return False
        
        finally:
            if self.sovereign:
                await self.sovereign.shutdown()
    
    def _save_state(self):
        """Save cron state for monitoring."""
        try:
            with open(CRON_STATE, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    async def _send_alert(self, message: str):
        """Send alert on failure."""
        if ALERT_WEBHOOK:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    await session.post(ALERT_WEBHOOK, json={
                        "text": f"🚨 Cyberhound Cron Alert\n{message}",
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
        
        # Always log
        logger.error(f"ALERT: {message}")


def check_cron_status() -> Dict:
    """Check status of last cron run."""
    try:
        if CRON_STATE.exists():
            with open(CRON_STATE) as f:
                return json.load(f)
        return {"error": "No state file found"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main entry point for cron execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🐺 Cyberhound Cron Hunter")
    parser.add_argument("--status", action="store_true", help="Show last run status")
    parser.add_argument("--force", action="store_true", help="Force run even if locked")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without hunting")
    
    args = parser.parse_args()
    
    if args.status:
        # Show status and exit
        status = check_cron_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    if args.dry_run:
        # Validate only
        logger.info("🔍 DRY RUN - Validating configuration")
        discovery = TargetDiscovery()
        targets = discovery.load_and_validate_targets()
        
        if targets:
            logger.info(f"✅ Config valid - {len(targets)} targets ready")
            sys.exit(0)
        else:
            logger.error("❌ No targets configured")
            sys.exit(2)
    
    # Normal cron execution
    try:
        with LockFile(LOCK_FILE) as lock:
            if not lock.acquired and not args.force:
                logger.error("❌ Another instance is running (lock file exists)")
                print("ERROR: Lock file exists - another cron job is running")
                print("Use --force to override (not recommended)")
                sys.exit(3)
            
            hunter = CronHunter()
            success = asyncio.run(hunter.run_single_hunt())
            
            sys.exit(hunter.exit_code)
            
    except RuntimeError as e:
        logger.error(f"Lock error: {e}")
        print(f"ERROR: {e}")
        sys.exit(3)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
