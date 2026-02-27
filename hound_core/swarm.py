#!/usr/bin/env python3
"""
🐺 CYBERHOUND 20-HOUND SWARM v2.1
REAL scraping with rate limiting and enhanced error handling.
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urljoin

logger = logging.getLogger("Swarm")

# Rate limiting config
DEFAULT_DELAY_BETWEEN_REQUESTS = 1.0  # seconds
DEFAULT_DELAY_BETWEEN_DOMAINS = 2.0   # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2.0


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
    confidence: float


class RateLimiter:
    """Rate limiter for polite web scraping."""
    
    def __init__(self, delay: float = DEFAULT_DELAY_BETWEEN_REQUESTS):
        self.delay = delay
        self.last_request_time: Dict[str, float] = {}
        self.global_last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def wait(self, domain: str):
        """Wait appropriate time before next request to domain."""
        async with self._lock:
            now = time.time()
            
            # Global rate limit
            time_since_global = now - self.global_last_request
            if time_since_global < self.delay:
                wait_time = self.delay - time_since_global
                logger.debug(f"⏱️  Global rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            # Per-domain rate limit
            if domain in self.last_request_time:
                time_since_domain = now - self.last_request_time[domain]
                if time_since_domain < DEFAULT_DELAY_BETWEEN_DOMAINS:
                    wait_time = DEFAULT_DELAY_BETWEEN_DOMAINS - time_since_domain
                    logger.debug(f"⏱️  Domain rate limit for {domain}: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            now = time.time()
            self.global_last_request = now
            self.last_request_time[domain] = now


class WebScraper:
    """Base web scraper with real HTTP requests and rate limiting."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = rate_limiter or RateLimiter()
        self.request_count = 0
        self.error_count = 0
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=3,
            ttl_dns_cache=300,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
            },
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        
        # Log stats
        logger.info(f"📊 Scraper stats: {self.request_count} requests, {self.error_count} errors")
    
    async def fetch(self, url: str, domain: str = "", retry: int = 0) -> Optional[str]:
        """Fetch real HTML from a URL with retry logic."""
        if not domain:
            domain = url.split('/')[2] if '://' in url else url
        
        # Apply rate limiting
        await self.rate_limiter.wait(domain)
        
        try:
            async with self.session.get(url, ssl=False, allow_redirects=True) as resp:
                self.request_count += 1
                
                if resp.status == 200:
                    content = await resp.text()
                    logger.debug(f"✅ Fetched {url} ({len(content)} bytes)")
                    return content
                
                elif resp.status in (429, 503, 502, 504):  # Rate limited or server error
                    if retry < MAX_RETRIES:
                        logger.warning(f"⚠️  HTTP {resp.status} for {url}, retrying...")
                        await asyncio.sleep(RETRY_DELAY * (retry + 1))
                        return await self.fetch(url, domain, retry + 1)
                    else:
                        logger.error(f"❌ Max retries exceeded for {url}")
                        self.error_count += 1
                        return None
                
                else:
                    logger.warning(f"⚠️  HTTP {resp.status} for {url}")
                    self.error_count += 1
                    return None
                    
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Connection error for {url}: {e}")
            self.error_count += 1
            return None
            
        except aiohttp.ClientResponseError as e:
            logger.error(f"❌ Response error for {url}: {e.status} - {e.message}")
            self.error_count += 1
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Timeout fetching {url}")
            self.error_count += 1
            return None
            
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {url}: {type(e).__name__}: {e}")
            self.error_count += 1
            return None
    
    async def fetch_privacy_pages(self, domain: str) -> Dict[str, str]:
        """Fetch privacy policy, terms, and contact pages with error handling."""
        base_url = f"https://{domain}" if not domain.startswith('http') else domain
        pages = {}
        
        paths = [
            '/privacy',
            '/privacy-policy',
            '/legal/privacy',
            '/terms',
            '/terms-of-service',
            '/legal/terms',
            '/contact',
            '/about',
            '/company',
        ]
        
        # Fetch homepage first
        logger.info(f"  📡 Fetching {base_url}")
        homepage = await self.fetch(base_url, domain)
        if homepage:
            pages['homepage'] = homepage.lower()
        else:
            logger.warning(f"  ⚠️  Could not fetch homepage for {domain}")
            return pages  # If homepage fails, don't try other pages
        
        # Fetch other pages
        for path in paths:
            url = urljoin(base_url, path)
            content = await self.fetch(url, domain)
            if content:
                pages[path] = content.lower()
        
        logger.info(f"  📄 Fetched {len(pages)} pages from {domain}")
        return pages


class ComplianceHound:
    """Base class for compliance hounds with common utilities."""
    
    def __init__(self, scraper: WebScraper, name: str, gap_type: str, jurisdiction: str):
        self.scraper = scraper
        self.name = name
        self.gap_type = gap_type
        self.jurisdiction = jurisdiction
    
    def check_patterns(self, text: str, patterns: List[str]) -> tuple[bool, List[str]]:
        """Check which patterns are found in text."""
        found = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, found
    
    def create_lead(self, domain: str, description: str, fine_risk: int, 
                    evidence: str, severity: str, confidence: float) -> Lead:
        """Create a Lead with proper formatting."""
        company = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0]
        
        return Lead(
            company=company.title(),
            domain=domain,
            gap_type=self.gap_type,
            description=description,
            fine_risk=fine_risk,
            jurisdiction=self.jurisdiction,
            evidence=evidence,
            severity=severity,
            found_at=datetime.now().isoformat(),
            confidence=round(confidence, 2)
        )


class LoI25Hound(ComplianceHound):
    """Quebec Law 25 Compliance Hound."""
    
    def __init__(self, scraper: WebScraper):
        super().__init__(scraper, "Québec", "loi_25", "Quebec")
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Check for Law 25 compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for Law 25 gaps...")
        
        try:
            pages = await self.scraper.fetch_privacy_pages(domain)
            if not pages:
                logger.debug(f"    No pages fetched for {domain}")
                return None
            
            all_text = ' '.join(pages.values())
            gaps = []
            confidence = 0.0
            
            # Check 1: Data Protection Officer
            dpo_patterns = [
                r'data protection officer',
                r'privacy officer',
                r'délégué à la protection des données',
                r'responsable de la protection des données',
                r'dpo[@]',
                r'privacy[@]',
                r'protection des renseignements personnels',
            ]
            has_dpo, _ = self.check_patterns(all_text, dpo_patterns)
            if not has_dpo:
                gaps.append("Missing Data Protection Officer designation")
                confidence += 0.3
            
            # Check 2: Consent mechanism
            consent_patterns = [
                r'consent',
                r'consentement',
                r'cookie.{0,20}consent',
                r'accept.{0,20}privacy',
                r'privacy settings',
            ]
            has_consent, _ = self.check_patterns(all_text, consent_patterns)
            if not has_consent:
                gaps.append("No clear consent mechanism")
                confidence += 0.2
            
            # Check 3: Data retention policy
            retention_patterns = [
                r'retain.{0,50}data',
                r'retention.{0,30}period',
                r'conservation.{0,30}données',
                r'delete.{0,30}data',
                r'supprimer.{0,30}données',
            ]
            has_retention, _ = self.check_patterns(all_text, retention_patterns)
            if not has_retention:
                gaps.append("No data retention policy stated")
                confidence += 0.2
            
            # Check 4: Right to deletion/rectification
            rights_patterns = [
                r'right to deletion',
                r'right to be forgotten',
                r'droit à l\'effacement',
                r'rectification',
                r'access your data',
                r'accéder à vos données',
            ]
            has_rights, _ = self.check_patterns(all_text, rights_patterns)
            if not has_rights:
                gaps.append("Missing data subject rights info")
                confidence += 0.2
            
            if gaps and confidence >= 0.3:
                severity = "HIGH" if len(gaps) >= 3 else "MEDIUM"
                return self.create_lead(
                    domain=domain,
                    description="; ".join(gaps[:2]),
                    fine_risk=25000,
                    evidence=f"Checked {len(pages)} pages",
                    severity=severity,
                    confidence=confidence
                )
            
            logger.debug(f"    No Law 25 gaps found at {domain}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error in LoI25Hound.sniff({domain}): {e}")
            return None


class Bill96Hound(ComplianceHound):
    """Quebec Bill 96 AI Disclosure Hound."""
    
    def __init__(self, scraper: WebScraper):
        super().__init__(scraper, "Loi 96", "bill_96", "Quebec")
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Check for Bill 96 AI disclosure gaps."""
        logger.info(f"  {self.name} hunting {domain} for AI disclosure gaps...")
        
        try:
            pages = await self.scraper.fetch_privacy_pages(domain)
            if not pages or 'homepage' not in pages:
                return None
            
            homepage = pages['homepage']
            all_text = ' '.join(pages.values())
            
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
                r'powered by ai',
                r'artificial intelligence',
            ]
            
            has_ai, found_ai = self.check_patterns(homepage, ai_patterns)
            
            if not has_ai:
                logger.debug(f"    No AI detected at {domain}")
                return None
            
            # Check for AI disclosure
            disclosure_patterns = [
                r'powered by ai',
                r'uses artificial intelligence',
                r'chatbot powered by',
                r'assistant automatisé',
                r'intelligence artificielle',
                r'\.ai',
                r'bot disclosure',
            ]
            
            has_disclosure, _ = self.check_patterns(all_text, disclosure_patterns)
            
            if not has_disclosure:
                return self.create_lead(
                    domain=domain,
                    description="AI system detected but no disclosure to users",
                    fine_risk=50000,
                    evidence=f"AI indicators: {', '.join(found_ai[:3])}",
                    severity="CRITICAL",
                    confidence=0.85
                )
            
            logger.debug(f"    AI properly disclosed at {domain}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error in Bill96Hound.sniff({domain}): {e}")
            return None


class CCPAHound(ComplianceHound):
    """California CCPA/CPRA Compliance Hound."""
    
    def __init__(self, scraper: WebScraper):
        super().__init__(scraper, "Cali", "ccpa", "California")
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Check for CCPA compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for CCPA gaps...")
        
        try:
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
                r'do not share',
            ]
            has_dns, _ = self.check_patterns(all_text, dns_patterns)
            if not has_dns:
                gaps.append("Missing 'Do Not Sell My Info' link")
                confidence += 0.4
            
            # Check 2: Privacy Policy mentions California
            ca_patterns = [
                r'california.{0,50}resident',
                r'california.{0,50}consumer',
                r'ccpa',
                r'cpra',
                r'california privacy',
            ]
            has_ca, _ = self.check_patterns(all_text, ca_patterns)
            if not has_ca:
                gaps.append("No California-specific privacy section")
                confidence += 0.3
            
            if gaps and confidence >= 0.3:
                return self.create_lead(
                    domain=domain,
                    description="; ".join(gaps),
                    fine_risk=7500,
                    evidence="Missing required CCPA disclosures",
                    severity="MEDIUM",
                    confidence=confidence
                )
            
            logger.debug(f"    No CCPA gaps found at {domain}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error in CCPAHound.sniff({domain}): {e}")
            return None


class GDPRHound(ComplianceHound):
    """EU GDPR Compliance Hound."""
    
    def __init__(self, scraper: WebScraper):
        super().__init__(scraper, "Euro", "gdpr", "EU-GDPR")
    
    async def sniff(self, domain: str) -> Optional[Lead]:
        """Check for GDPR compliance gaps."""
        logger.info(f"  {self.name} hunting {domain} for GDPR gaps...")
        
        try:
            pages = await self.scraper.fetch_privacy_pages(domain)
            if not pages:
                return None
            
            all_text = ' '.join(pages.values())
            gaps = []
            confidence = 0.0
            
            # Check 1: Cookie consent banner/mechanism
            cookie_patterns = [
                r'cookie.{0,30}consent',
                r'cookie.{0,30}settings',
                r'we use cookies',
                r'accept cookies',
                r'cookie policy',
                r'cookie preferences',
            ]
            has_cookie, _ = self.check_patterns(all_text, cookie_patterns)
            if not has_cookie:
                gaps.append("No cookie consent mechanism")
                confidence += 0.3
            
            # Check 2: Data controller identification
            controller_patterns = [
                r'data controller',
                r'controller.{0,30}information',
                r'responsible for data',
                r'privacy controller',
            ]
            has_controller, _ = self.check_patterns(all_text, controller_patterns)
            if not has_controller:
                gaps.append("Missing data controller identification")
                confidence += 0.3
            
            # Check 3: Legal basis for processing
            legal_patterns = [
                r'legal basis',
                r'lawful basis',
                r'legitimate interest',
                r'consent.{0,30}processing',
            ]
            has_legal, _ = self.check_patterns(all_text, legal_patterns)
            if not has_legal:
                gaps.append("No legal basis for processing stated")
                confidence += 0.2
            
            # Check 4: DPO for public authorities/large scale
            dpo_patterns = [
                r'data protection officer',
                r'dpo[@]',
                r'privacy officer',
            ]
            has_dpo, _ = self.check_patterns(all_text, dpo_patterns)
            if not has_dpo:
                gaps.append("No DPO information (may be required)")
                confidence += 0.1
            
            if gaps and confidence >= 0.3:
                severity = "CRITICAL" if len(gaps) >= 3 else "HIGH"
                return self.create_lead(
                    domain=domain,
                    description="; ".join(gaps[:2]),
                    fine_risk=20000000,  # Up to €20M
                    evidence=f"GDPR gaps found across {len(pages)} pages",
                    severity=severity,
                    confidence=confidence
                )
            
            logger.debug(f"    No GDPR gaps found at {domain}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error in GDPRHound.sniff({domain}): {e}")
            return None


class Swarm:
    """The 20-Hound Swarm - deploys REAL compliance hunters with rate limiting."""
    
    def __init__(self, delay: float = DEFAULT_DELAY_BETWEEN_REQUESTS):
        self.rate_limiter = RateLimiter(delay)
        self.scraper = WebScraper(self.rate_limiter)
        self.hounds: List[ComplianceHound] = []
        self._initialize_hounds()
    
    def _initialize_hounds(self):
        """Deploy 20 real compliance hounds."""
        # Deploy multiple of each type for parallel coverage
        for i in range(5):
            self.hounds.append(LoI25Hound(self.scraper))
            self.hounds.append(Bill96Hound(self.scraper))
            self.hounds.append(CCPAHound(self.scraper))
            self.hounds.append(GDPRHound(self.scraper))
        
        logger.info(f"🐺 {len(self.hounds)}-Hound Swarm deployed with rate limiting")
    
    async def hunt_target(self, domain: str) -> List[Lead]:
        """Deploy all hounds on a single target in parallel."""
        logger.info(f"\n🎯 SWARM ATTACK: {domain}")
        
        tasks = []
        for hound in self.hounds:
            # Add staggered delays to avoid overwhelming the target
            task = self._run_hound_with_delay(hound, domain)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        leads = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"  ❌ Hound {i} failed: {result}")
            elif result is not None:
                leads.append(result)
        
        # Remove duplicates by gap_type
        seen_types: Set[str] = set()
        unique_leads = []
        for lead in leads:
            key = f"{lead.domain}:{lead.gap_type}"
            if key not in seen_types:
                seen_types.add(key)
                unique_leads.append(lead)
        
        logger.info(f"✅ Swarm found {len(unique_leads)} unique gaps at {domain}")
        return unique_leads
    
    async def _run_hound_with_delay(self, hound: ComplianceHound, domain: str) -> Optional[Lead]:
        """Run a hound with a small random delay to spread load."""
        # Small random delay (0-0.5s) to spread out requests
        await asyncio.sleep(0.1)
        return await hound.sniff(domain)
    
    async def hunt_targets(self, domains: List[str]) -> Dict[str, List[Lead]]:
        """Hunt multiple targets sequentially."""
        results = {}
        for i, domain in enumerate(domains):
            results[domain] = await self.hunt_target(domain)
            # Delay between targets
            if i < len(domains) - 1:
                await asyncio.sleep(DEFAULT_DELAY_BETWEEN_DOMAINS)
        return results


if __name__ == "__main__":
    # Demo with rate limiting
    swarm = Swarm(delay=0.5)  # Faster for demo
    
    targets = ["example.com"]
    
    async def demo():
        print("="*60)
        print("🐺 CYBERHOUND SWARM v2.1 DEMO")
        print("   With rate limiting and enhanced error handling")
        print("="*60)
        
        async with swarm.scraper:
            for target in targets:
                leads = await swarm.hunt_target(target)
                
                print(f"\n📊 RESULTS for {target}:")
                if leads:
                    for lead in leads:
                        print(f"\n  🔴 {lead.gap_type.upper()}")
                        print(f"     Company: {lead.company}")
                        print(f"     Gap: {lead.description}")
                        print(f"     Risk: ${lead.fine_risk:,}")
                        print(f"     Confidence: {lead.confidence:.0%}")
                else:
                    print(f"\n  ✅ {target} - No gaps detected")
    
    asyncio.run(demo())
