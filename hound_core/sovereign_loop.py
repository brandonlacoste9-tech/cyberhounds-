#!/usr/bin/env python3
"""
🐺 CYBERHOUND SOVEREIGN LOOP v2.0
B2B Compliance Hunting with Human-on-the-Loop (HOTL)
REAL leads only - no simulation.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from swarm import Swarm, Lead

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
        
        # Calculate pricing based on risk
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
        self.swarm = Swarm()
        self.pending_strikes: List[Dict] = []
        self.settled_strikes: List[Dict] = []
        self.load_data()
        self._ensure_targets_file()
    
    def _ensure_targets_file(self):
        """Create targets file if it doesn't exist."""
        if not TARGETS_FILE.exists():
            default_targets = """# Add B2B prospect domains here (one per line)
# Example:
# fintech-startup.com
# healthapp.io
# saas-company.ca
"""
            TARGETS_FILE.write_text(default_targets)
            logger.info(f"📝 Created {TARGETS_FILE} - add your targets there")
    
    def load_targets(self) -> List[str]:
        """Load target domains from file."""
        if not TARGETS_FILE.exists():
            return []
        
        lines = TARGETS_FILE.read_text().strip().split('\n')
        targets = [
            line.strip() 
            for line in lines 
            if line.strip() and not line.startswith('#')
        ]
        return targets
    
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
        """
        Run one complete hunt cycle:
        1. Load targets
        2. Deploy swarm
        3. Forge Decision Packs
        4. Queue for approval
        """
        targets = self.load_targets()
        
        if not targets:
            logger.warning("⚠️  No targets in targets.txt - add domains to hunt")
            return []
        
        logger.info(f"🎯 Hunting {len(targets)} targets")
        
        all_packs = []
        
        for target in targets:
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
            
            # Small delay between targets
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
        
        print("\n💬 Approve via Telegram or update pending_strikes.json")
        print("="*70 + "\n")
    
    async def sovereign_loop(self):
        """Main hunting loop - runs forever."""
        logger.info("="*70)
        logger.info("🐺 CYBERHOUND SOVEREIGN LOOP v2.0")
        logger.info("   B2B Compliance Hunting | Human-on-the-Loop")
        logger.info("   REAL scrapers | NO simulated data")
        logger.info("="*70)
        
        targets = self.load_targets()
        logger.info(f"📁 Loaded {len(targets)} targets from targets.txt")
        
        if not targets:
            logger.error("❌ No targets configured! Add domains to data/targets.txt")
            return
        
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
            
            # Sleep until next cycle
            logger.info(f"💤 Sleeping {CYCLE_INTERVAL_SECONDS/60} minutes until next hunt...")
            await asyncio.sleep(CYCLE_INTERVAL_SECONDS)


async def quick_hunt(domains: List[str]):
    """One-off hunt for specific domains."""
    logger.info("🐺 QUICK HUNT MODE")
    
    sovereign = SovereignLoop()
    
    # Temporarily override targets
    sovereign.swarm = Swarm()
    
    all_packs = []
    for domain in domains:
        leads = await sovereign.swarm.hunt_target(domain)
        for lead in leads:
            pack = DecisionPack(lead)
            all_packs.append(pack)
    
    sovereign.print_strike_board(all_packs)
    
    # Save to LE_BUTIN
    butin = {
        "mode": "quick_hunt",
        "timestamp": datetime.now().isoformat(),
        "targets": domains,
        "strikes": [p.to_dict() for p in all_packs]
    }
    
    DATA_DIR.mkdir(exist_ok=True)
    with open(BUTIN_PATH, 'w') as f:
        json.dump(butin, f, indent=2)
    
    logger.info(f"💾 Results saved to {BUTIN_PATH}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick hunt mode: python sovereign_loop.py --quick domain1.com domain2.com
        domains = sys.argv[2:]
        if domains:
            asyncio.run(quick_hunt(domains))
        else:
            print("Usage: python sovereign_loop.py --quick domain1.com domain2.com")
    else:
        # Full sovereign loop
        sovereign = SovereignLoop()
        asyncio.run(sovereign.sovereign_loop())
