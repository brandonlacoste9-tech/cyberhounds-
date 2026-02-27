#!/usr/bin/env python3
"""
🐺 CYBERHOUND 20-HOUND SWARM v2.0
REAL scraping - no simulated data.
"""

import asyncio
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("Swarm")


@dataclass
class Lead:
    """A real compliance gap lead."""
    company: str
    domain: str
    gap_type: str
    description: str
    fine_risk: int
    jurisdiction: str
    evidence: str
    severity: str
    found_at: str
    confidence: float  # 0.0 - 1.0


class WebScraper:
    """Base web scraper with real HTTP requests."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch(self, url: str) -> Optional[str]:
        """Fetch real HTML from a URL."""
        try:
            async with self.session.get(url, ssl=False) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning(f"HTTP {resp.status} for {url}")
                return None
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None
    
    async def fetch_privacy_pages(self, domain: str) -> Dict[str, str]:
        """Fetch privacy policy, terms, and contact pages."""
        base_url = f"https://{domain}" if not domain.startswith('http') else domain
        pages = {}
        
        paths = [
            '/privacy',
            '/privacy-policy',
            '/legal/privacy',
            '/terms',
            '/terms-of-service',
            '/contact',
            '/about',
        ]
        
        for path in paths:
            url = urljoin(base_url, path)
            content = await self.fetch(url)
            if content:
                pages[path] = content.lower()
        
        # Also fetch homepage
        homepage = await self.fetch(base_url)
        if homepage:
            pages['homepage'] = homepage.lower()
        
        return pages


class LoI25Hound:
    """
    Quebec Law 25 Compliance Hound.
    Checks for: DPO designation, privacy policy compliance, consent mechanisms.
    """
    
    def __init__(self, scraper: WebScraper):
        self.name = "Québec"
        self.scraper = scraper
        self.fine_range = (25000, 100000)
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Real check for Law 25 compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for Law 25 gaps...")
        
        pages = await self.scraper.fetch_privacy_pages(domain)
        if not pages:
            return None
        
        all_text = ' '.join(pages.values())
        gaps = []
        confidence = 0.0
        
        # Check 1: Data Protection Officer (required since Sept 2023)
        dpo_patterns = [
            r'data protection officer',
            r'privacy officer',
            r'délégué à la protection des données',
            r'responsable de la protection des données',
            r'dpo[@]',
            r'privacy[@]',
        ]
        has_dpo = any(re.search(p, all_text) for p in dpo_patterns)
        if not has_dpo:
            gaps.append("Missing Data Protection Officer designation")
            confidence += 0.3
        
        # Check 2: Consent mechanism
        consent_patterns = [
            r'consent',
            r'consentement',
            r'cookie.{0,20}consent',
            r'accept.{0,20}privacy',
        ]
        has_consent = any(re.search(p, all_text) for p in consent_patterns)
        if not has_consent:
            gaps.append("No clear consent mechanism")
            confidence += 0.2
        
        # Check 3: Data retention policy
        retention_patterns = [
            r'retain.{0,50}data',
            r'retention.{0,30}period',
            r'conservation.{0,30}données',
            r'delete.{0,30}data',
        ]
        has_retention = any(re.search(p, all_text) for p in retention_patterns)
        if not has_retention:
            gaps.append("No data retention policy stated")
            confidence += 0.2
        
        # Check 4: Right to deletion/rectification
        rights_patterns = [
            r'right to deletion',
            r'right to be forgotten',
            r'droit à l\'effacement',
            r'rectification',
        ]
        has_rights = any(re.search(p, all_text) for p in rights_patterns)
        if not has_rights:
            gaps.append("Missing data subject rights info")
            confidence += 0.2
        
        if gaps and confidence >= 0.3:
            company = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0]
            return Lead(
                company=company.title(),
                domain=domain,
                gap_type="loi_25",
                description="; ".join(gaps[:2]),
                fine_risk=25000,
                jurisdiction="Quebec",
                evidence=f"Checked {len(pages)} pages: {', '.join(pages.keys())}",
                severity="HIGH" if len(gaps) >= 3 else "MEDIUM",
                found_at=datetime.now().isoformat(),
                confidence=round(confidence, 2)
            )
        return None


class Bill96Hound:
    """
    Quebec Bill 96 AI Disclosure Hound.
    Checks for: AI system disclosures, chatbot notices.
    """
    
    def __init__(self, scraper: WebScraper):
        self.name = "Loi 96"
        self.scraper = scraper
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Real check for Bill 96 AI disclosure gaps."""
        logger.info(f"  {self.name} hunting {domain} for AI disclosure gaps...")
        
        pages = await self.scraper.fetch_privacy_pages(domain)
        if not pages:
            return None
        
        all_text = ' '.join(pages.values())
        homepage = pages.get('homepage', '')
        
        # Check if site has AI/chatbot features
        ai_patterns = [
            r'chatbot',
            r'virtual assistant',
            r'ai assistant',
            r'\bchat\b.{0,50}support',
            r'assistant.{0,30}24/7',
            r'intercom',
            r'drift',
            r'crisp',
            r'tidio',
        ]
        has_ai = any(re.search(p, homepage) for p in ai_patterns)
        
        if not has_ai:
            return None  # No AI detected, no gap
        
        # Check for AI disclosure
        disclosure_patterns = [
            r'powered by ai',
            r'uses artificial intelligence',
            r'chatbot powered by',
            r'assistant automatisé',
            r'intelligence artificielle',
            r'\.ai',
        ]
        has_disclosure = any(re.search(p, all_text) for p in disclosure_patterns)
        
        if not has_disclosure:
            company = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0]
            return Lead(
                company=company.title(),
                domain=domain,
                gap_type="bill_96",
                description="AI system detected but no disclosure to users",
                fine_risk=50000,
                jurisdiction="Quebec",
                evidence="Chatbot/AI detected on site; no disclosure in privacy/terms",
                severity="CRITICAL",
                found_at=datetime.now().isoformat(),
                confidence=0.85
            )
        return None


class CCPAHound:
    """
    California CCPA/CPRA Compliance Hound.
    Checks for: Do Not Sell link, privacy rights page.
    """
    
    def __init__(self, scraper: WebScraper):
        self.name = "Cali"
        self.scraper = scraper
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Real check for CCPA compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for CCPA gaps...")
        
        pages = await self.scraper.fetch_privacy_pages(domain)
        if not pages:
            return None
        
        all_text = ' '.join(pages.values())
        gaps = []
        confidence = 0.0
        
        # Check 1: "Do Not Sell My Personal Information" link
        dns_patterns = [
            r'do not sell',
            r'opt out of sale',
            r'california privacy rights',
            r'ccpa.{0,30}rights',
            r'your privacy choices',
        ]
        has_dns = any(re.search(p, all_text) for p in dns_patterns)
        if not has_dns:
            gaps.append("Missing 'Do Not Sell My Info' link")
            confidence += 0.4
        
        # Check 2: Privacy Policy mentions California
        ca_patterns = [
            r'california.{0,50}resident',
            r'california.{0,50}consumer',
            r'ccpa',
            r'cpra',
        ]
        has_ca = any(re.search(p, all_text) for p in ca_patterns)
        if not has_ca:
            gaps.append("No California-specific privacy section")
            confidence += 0.3
        
        if gaps and confidence >= 0.3:
            company = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0]
            return Lead(
                company=company.title(),
                domain=domain,
                gap_type="ccpa",
                description="; ".join(gaps),
                fine_risk=7500,
                jurisdiction="California",
                evidence=f"Missing required CCPA disclosures",
                severity="MEDIUM",
                found_at=datetime.now().isoformat(),
                confidence=round(confidence, 2)
            )
        return None


class GDPRHound:
    """
    EU GDPR Compliance Hound.
    Checks for: Cookie consent, data controller info, DPO.
    """
    
    def __init__(self, scraper: WebScraper):
        self.name = "Euro"
        self.scraper = scraper
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Real check for GDPR compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for GDPR gaps...")
        
        pages = await self.scraper.fetch_privacy_pages(domain)
        if not pages:
            return None
        
        all_text = ' '.join(pages.values())
        homepage = pages.get('homepage', '')
        gaps = []
        confidence = 0.0
        
        # Check 1: Cookie consent banner/mechanism
        cookie_patterns = [
            r'cookie.{0,30}consent',
            r'cookie.{0,30}settings',
            r'we use cookies',
            r'accept cookies',
            r'cookie policy',
        ]
        has_cookie = any(re.search(p, all_text) for p in cookie_patterns)
        if not has_cookie:
            gaps.append("No cookie consent mechanism")
            confidence += 0.3
        
        # Check 2: Data controller identification
        controller_patterns = [
            r'data controller',
            r'controller.{0,30}information',
            r'responsible for data',
        ]
        has_controller = any(re.search(p, all_text) for p in controller_patterns)
        if not has_controller:
            gaps.append("Missing data controller identification")
            confidence += 0.3
        
        # Check 3: Legal basis for processing
        legal_patterns = [
            r'legal basis',
            r'lawful basis',
            r'legitimate interest',
        ]
        has_legal = any(re.search(p, all_text) for p in legal_patterns)
        if not has_legal:
            gaps.append("No legal basis for processing stated")
            confidence += 0.2
        
        if gaps and confidence >= 0.3:
            company = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0]
            return Lead(
                company=company.title(),
                domain=domain,
                gap_type="gdpr",
                description="; ".join(gaps[:2]),
                fine_risk=20000000,  # Up to €20M or 4% revenue
                jurisdiction="EU-GDPR",
                evidence=f"GDPR gaps found across {len(pages)} pages",
                severity="CRITICAL" if len(gaps) >= 3 else "HIGH",
                found_at=datetime.now().isoformat(),
                confidence=round(confidence, 2)
            )
        return None


class Swarm:
    """The 20-Hound Swarm - deploys REAL compliance hunters."""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.hounds = []
        self._initialize_hounds()
    
    def _initialize_hounds(self):
        """Deploy 20 real compliance hounds."""
        # Deploy multiple of each type for parallel coverage
        for i in range(5):
            self.hounds.append(LoI25Hound(self.scraper))
            self.hounds.append(Bill96Hound(self.scraper))
            self.hounds.append(CCPAHound(self.scraper))
            self.hounds.append(GDPRHound(self.scraper))
        
        logger.info(f"🐺 {len(self.hounds)}-Hound Swarm deployed (REAL scrapers)")
    
    async def hunt_target(self, domain: str) -> List[Lead]:
        """Deploy all hounds on a single target in parallel."""
        logger.info(f"\n🎯 SWARM ATTACK: {domain}")
        
        async with self.scraper:
            tasks = [hound.sniff(domain) for hound in self.hounds]
            results = await asyncio.gather(*tasks)
        
        leads = [r for r in results if r is not None]
        
        # Remove duplicates by gap_type
        seen_types = set()
        unique_leads = []
        for lead in leads:
            key = f"{lead.domain}:{lead.gap_type}"
            if key not in seen_types:
                seen_types.add(key)
                unique_leads.append(lead)
        
        logger.info(f"✅ Swarm found {len(unique_leads)} unique gaps at {domain}")
        return unique_leads
    
    async def hunt_targets(self, domains: List[str]) -> Dict[str, List[Lead]]:
        """Hunt multiple targets sequentially."""
        results = {}
        for domain in domains:
            results[domain] = await self.hunt_target(domain)
        return results


if __name__ == "__main__":
    # Demo with real domains
    swarm = Swarm()
    
    # Test targets - replace with your B2B prospect list
    targets = [
        "example-startup.com",  # Will likely have gaps
    ]
    
    async def demo():
        print("="*60)
        print("🐺 CYBERHOUND REAL SCRAPER DEMO")
        print("="*60)
        print("\n⚠️  Using REAL HTTP requests - no simulated data\n")
        
        for target in targets:
            leads = await swarm.hunt_target(target)
            
            if leads:
                print(f"\n📊 RESULTS for {target}:")
                for lead in leads:
                    print(f"\n  🔴 {lead.gap_type.upper()}")
                    print(f"     Company: {lead.company}")
                    print(f"     Gap: {lead.description}")
                    print(f"     Risk: ${lead.fine_risk:,}")
                    print(f"     Confidence: {lead.confidence}")
            else:
                print(f"\n✅ {target} - No gaps detected")
    
    asyncio.run(demo())
