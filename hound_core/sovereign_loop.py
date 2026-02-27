#!/usr/bin/env python3
"""
🐺 CYBERHOUND SOVEREIGN LOOP v2.0
B2B Compliance Hunting with Human-on-the-Loop (HOTL)
REAL leads only - no simulation, no fake data.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    from swarm import Swarm, Lead
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

from target_discovery import TargetDiscovery

# Configuration
CYCLE_INTERVAL_SECONDS = 30 * 60  # 30 minutes between hunts
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
BUTIN_PATH = DATA_DIR / "LE_BUTIN.json"
PENDING_PATH = DATA_DIR / "pending_strikes.json"
SETTLED_PATH = DATA_DIR / "settled_strikes.json"
TARGETS_FILE = DATA_DIR / "targets.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Sovereign")


class DecisionPack:
    """A forged deal ready for executive approval."""
    
    def __init__(self, lead: Lead):
        self.pack_id = f"PACK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{lead.company[:8].upper()}"
        self.lead = lead
        self.forge_timestamp = datetime.now().isoformat()
        self._calculate_price()
    
    def _calculate_price(self):
        """Price the deal based on severity and risk."""
        if self.lead.severity == "CRITICAL":
            base_price = min(25000, self.lead.fine_risk * 0.1)
        elif self.lead.severity == "HIGH":
            base_price = min(18000, self.lead.fine_risk * 0.15)
        else:
            base_price = min(12000, self.lead.fine_risk * 0.2)
        
        self.proposed_price = int(base_price)
        self.roi = f"{self.lead.fine_risk / self.proposed_price:.1f}x"
    
    def to_dict(self) -> Dict:
        return {
            "pack_id": self.pack_id,
            "company": self.lead.company,
            "domain": self.lead.domain,
            "gap_type": self.lead.gap_type,
            "gap_description": self.lead.description,
            "fine_risk": self.lead.fine_risk,
            "severity": self.lead.severity,
            "proposed_price": self.proposed_price,
            "roi_for_client": self.roi,
            "jurisdiction": self.lead.jurisdiction,
            "evidence": self.lead.evidence,
            "confidence": self.lead.confidence,
            "found_at": self.lead.found_at,
            "forged_at": self.forge_timestamp,
            "status": "PENDING_APPROVAL"
        }


class SovereignLoop:
    """Master controller for REAL B2B compliance hunting."""
    
    def __init__(self):
        self.swarm = None  # Initialized per-cycle to handle errors
        self.pending_strikes: List[Dict] = []
        self.settled_strikes: List[Dict] = []
        self.discovery = TargetDiscovery()
        self.load_data()
    
    def load_data(self):
        """Load persisted hunting data."""
        if PENDING_PATH.exists():
            with open(PENDING_PATH) as f:
                self.pending_strikes = json.load(f)
        if SETTLED_PATH.exists():
            with open(SETTLED_PATH) as f:
                self.settled_strikes = json.load(f)
    
    def save_data(self):
        """Persist hunting data."""
        with open(PENDING_PATH, 'w') as f:
            json.dump(self.pending_strikes, f, indent=2)
        with open(SETTLED_PATH, 'w') as f:
            json.dump(self.settled_strikes, f, indent=2)
    
    async def run_hunt_cycle(self) -> List[DecisionPack]:
        """Run one complete hunt cycle on REAL targets."""
        targets = self.discovery.load_and_validate_targets()
        
        if not targets:
            logger.error("="*70)
            logger.error("❌ NO TARGETS CONFIGURED")
            logger.error("="*70)
            logger.error("")
            logger.error("Add real B2B domains to: hound_core/data/targets.txt")
            logger.error("")
            logger.error("Run this for prospecting guidance:")
            logger.error("  python target_discovery.py")
            logger.error("")
            logger.error("="*70)
            return []
        
        logger.info(f"🎯 Hunting {len(targets)} REAL targets")
        
        # Initialize swarm fresh each cycle (handles connection issues)
        self.swarm = Swarm()
        all_packs = []
        
        async with self.swarm.scraper:
            for i, target in enumerate(targets, 1):
                logger.info(f"\n[{i}/{len(targets)}] Hunting {target}...")
                
                try:
                    # Deploy swarm on this target
                    leads = await self.swarm.hunt_target(target)
                    
                    # Forge Decision Packs for each lead
                    for lead in leads:
                        pack = DecisionPack(lead)
                        all_packs.append(pack)
                        
                        # Add to pending
                        self.pending_strikes.append(pack.to_dict())
                        
                        # Log the strike
                        logger.info(f"🔨 FORGED: {pack.pack_id}")
                        logger.info(f"   Company: {pack.lead.company}")
                        logger.info(f"   Gap: {pack.lead.description[:60]}...")
                        logger.info(f"   Price: ${pack.proposed_price:,} | ROI: {pack.roi}")
                        logger.info(f"   Confidence: {pack.lead.confidence:.0%}")
                    
                except Exception as e:
                    logger.error(f"❌ Error hunting {target}: {e}")
                
                # Small delay between targets (be polite)
                if i < len(targets):
                    await asyncio.sleep(2)
        
        self.save_data()
        return all_packs
    
    def print_strike_board(self, packs: List[DecisionPack]):
        """Print summary of forged strikes."""
        if not packs:
            logger.info("📭 No strikes forged this cycle")
            return
        
        print("\n" + "="*70)
        print("🐺 STRIKE BOARD - Ready for Deployment")
        print("="*70)
        
        total_value = sum(p.proposed_price for p in packs)
        total_risk = sum(p.lead.fine_risk for p in packs)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Strikes Forged: {len(packs)}")
        print(f"   Pipeline Value: ${total_value:,}")
        print(f"   Client Risk Avoided: ${total_risk:,}")
        
        print(f"\n📋 PENDING APPROVAL:")
        for pack in packs:
            status_emoji = "🔴" if pack.lead.severity == "CRITICAL" else "🟠" if pack.lead.severity == "HIGH" else "🟡"
            print(f"\n   {status_emoji} {pack.pack_id}")
            print(f"      {pack.lead.company} | {pack.lead.gap_type.upper()}")
            print(f"      ${pack.proposed_price:,} deal | {pack.roi} ROI | {pack.lead.confidence:.0%} confidence")
        
        print("\n💬 Approve via Telegram or edit pending_strikes.json")
        print("="*70 + "\n")
    
    async def sovereign_loop(self):
        """Main hunting loop - runs forever on REAL targets."""
        logger.info("="*70)
        logger.info("🐺 CYBERHOUND SOVEREIGN LOOP v2.0")
        logger.info("   B2B Compliance Hunting | Human-on-the-Loop")
        logger.info("   REAL scrapers | REAL targets | NO fake data")
        logger.info("="*70)
        
        # Check for targets before starting
        targets = self.discovery.load_and_validate_targets()
        
        if not targets:
            print("\n" + "="*70)
            print("🚨 CANNOT START: No targets configured")
            print("="*70)
            print("\nStep 1: Create your target list")
            print("  Edit: hound_core/data/targets.txt")
            print("\nStep 2: Add real B2B domains (one per line)")
            print("  Example:")
            print("    stripe.com")
            print("    plaid.com")
            print("    your-prospect.com")
            print("\nStep 3: Get prospecting help")
            print("  python target_discovery.py")
            print("="*70)
            return
        
        logger.info(f"📁 Loaded {len(targets)} targets from targets.txt")
        
        cycle = 0
        while True:
            cycle += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 HUNT CYCLE #{cycle} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*70}")
            
            try:
                # Run the hunt
                packs = await self.run_hunt_cycle()
                
                # Display results
                self.print_strike_board(packs)
                
                # Update LE_BUTIN
                butin = {
                    "cycle": cycle,
                    "timestamp": datetime.now().isoformat(),
                    "targets_hunted": len(targets),
                    "strikes_forged": len(packs),
                    "pending_count": len(self.pending_strikes),
                    "settled_count": len(self.settled_strikes),
                    "pipeline_value": sum(p['proposed_price'] for p in self.pending_strikes),
                    "latest_strikes": [p.to_dict() for p in packs]
                }
                
                with open(BUTIN_PATH, 'w') as f:
                    json.dump(butin, f, indent=2)
                
                logger.info(f"💾 LE_BUTIN updated: {BUTIN_PATH}")
                
            except Exception as e:
                logger.error(f"❌ Hunt cycle failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Sleep until next cycle
            logger.info(f"💤 Sleeping {CYCLE_INTERVAL_SECONDS/60} minutes until next hunt...")
            await asyncio.sleep(CYCLE_INTERVAL_SECONDS)


async def quick_hunt(domains: List[str]):
    """One-off hunt for specific domains - REAL scrapes."""
    logger.info("🐺 QUICK HUNT MODE - REAL SCRAPING")
    
    sovereign = SovereignLoop()
    
    # Validate domains
    valid_domains = [d for d in domains if sovereign.discovery.validate_domain(d)]
    invalid = set(domains) - set(valid_domains)
    
    if invalid:
        logger.warning(f"⚠️  Invalid domains skipped: {invalid}")
    
    if not valid_domains:
        logger.error("❌ No valid domains to hunt")
        return
    
    logger.info(f"🎯 Hunting {len(valid_domains)} domains")
    
    # Initialize swarm
    sovereign.swarm = Swarm()
    all_packs = []
    
    async with sovereign.swarm.scraper:
        for domain in valid_domains:
            logger.info(f"\n🎯 Hunting {domain}...")
            try:
                leads = await sovereign.swarm.hunt_target(domain)
                for lead in leads:
                    pack = DecisionPack(lead)
                    all_packs.append(pack)
            except Exception as e:
                logger.error(f"❌ Error with {domain}: {e}")
    
    sovereign.print_strike_board(all_packs)
    
    # Save to LE_BUTIN
    butin = {
        "mode": "quick_hunt",
        "timestamp": datetime.now().isoformat(),
        "targets": valid_domains,
        "strikes": [p.to_dict() for p in all_packs]
    }
    
    DATA_DIR.mkdir(exist_ok=True)
    with open(BUTIN_PATH, 'w') as f:
        json.dump(butin, f, indent=2)
    
    logger.info(f"💾 Results saved to {BUTIN_PATH}")
    
    return all_packs


def main():
    """Entry point with argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='🐺 Cyberhound B2B Compliance Hunter')
    parser.add_argument('--quick', nargs='+', help='Quick hunt specific domains')
    parser.add_argument('--discover', action='store_true', help='Show prospecting guide')
    
    args = parser.parse_args()
    
    if args.discover:
        # Just show prospecting guide
        discovery = TargetDiscovery()
        print(discovery.generate_prospecting_report())
    elif args.quick:
        # Quick hunt mode
        asyncio.run(quick_hunt(args.quick))
    else:
        # Full sovereign loop
        sovereign = SovereignLoop()
        asyncio.run(sovereign.sovereign_loop())


if __name__ == "__main__":
    main()
