#!/usr/bin/env python3
"""
🧪 UNIT TESTS: Swarm Module
Tests for compliance hounds with mocked HTTP responses.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hound_core"))

from swarm import (
    WebScraper, LoI25Hound, Bill96Hound, CCPAHound, GDPRHound,
    RateLimiter, Swarm, Lead
)


# ============== FIXTURES ==============

@pytest.fixture
def mock_scraper():
    """Create a mock scraper for testing."""
    scraper = Mock(spec=WebScraper)
    scraper.fetch = AsyncMock()
    scraper.fetch_privacy_pages = AsyncMock()
    return scraper


@pytest.fixture
def sample_privacy_pages():
    """Sample privacy page content for testing."""
    return {
        'homepage': '''
            <html>
            <body>
                <h1>Welcome to TestCorp</h1>
                <p>We use cookies to improve your experience.</p>
                <div id="chat-widget">Chat with us!</div>
            </body>
            </html>
        '''.lower(),
        '/privacy': '''
            <h1>Privacy Policy</h1>
            <p>Your privacy is important to us.</p>
            <p>Data Protection Officer: privacy@testcorp.com</p>
            <p>We retain your data for 2 years.</p>
            <p>You have the right to deletion and rectification.</p>
        '''.lower(),
        '/terms': '''
            <h1>Terms of Service</h1>
        '''.lower()
    }


@pytest.fixture
def non_compliant_pages():
    """Non-compliant pages for testing gap detection."""
    return {
        'homepage': '''
            <html>
            <body>
                <h1>BadCorp</h1>
                <p>Welcome to our site.</p>
            </body>
            </html>
        '''.lower(),
        '/privacy': '''
            <h1>Privacy</h1>
            <p>We collect your data.</p>
        '''.lower()
    }


# ============== RATE LIMITER TESTS ==============

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_delays_requests(self):
        """Test that rate limiter enforces delays."""
        limiter = RateLimiter(delay=0.1)
        
        start = asyncio.get_event_loop().time()
        await limiter.wait("example.com")
        await limiter.wait("example.com")
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should have waited at least 0.1s between requests
        assert elapsed >= 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_per_domain_tracking(self):
        """Test that rate limiter tracks per-domain separately."""
        limiter = RateLimiter(delay=0.1)
        
        # Request to different domains should not be delayed
        start = asyncio.get_event_loop().time()
        await limiter.wait("domain1.com")
        await limiter.wait("domain2.com")
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be quick (no delay between different domains)
        assert elapsed < 0.2


# ============== COMPLIANCE HOUND TESTS ==============

class TestLoI25Hound:
    """Test Quebec Law 25 hound."""
    
    @pytest.mark.asyncio
    async def test_detects_missing_dpo(self, mock_scraper, non_compliant_pages):
        """Test detection of missing DPO."""
        mock_scraper.fetch_privacy_pages.return_value = non_compliant_pages
        
        hound = LoI25Hound(mock_scraper)
        lead = await hound.sniff("badcorp.com")
        
        assert lead is not None
        assert lead.gap_type == "loi_25"
        assert "Missing Data Protection Officer" in lead.description
        assert lead.fine_risk == 25000
        assert lead.jurisdiction == "Quebec"
    
    @pytest.mark.asyncio
    async def test_no_gap_when_compliant(self, mock_scraper, sample_privacy_pages):
        """Test that compliant sites return no lead."""
        mock_scraper.fetch_privacy_pages.return_value = sample_privacy_pages
        
        hound = LoI25Hound(mock_scraper)
        lead = await hound.sniff("testcorp.com")
        
        assert lead is None
    
    @pytest.mark.asyncio
    async def test_handles_fetch_failure(self, mock_scraper):
        """Test graceful handling of fetch failures."""
        mock_scraper.fetch_privacy_pages.return_value = {}
        
        hound = LoI25Hound(mock_scraper)
        lead = await hound.sniff("error.com")
        
        assert lead is None


class TestBill96Hound:
    """Test Quebec Bill 96 hound."""
    
    @pytest.mark.asyncio
    async def test_detects_undisclosed_ai(self, mock_scraper):
        """Test detection of undisclosed AI."""
        pages = {
            'homepage': '''
                <html>
                <body>
                    <div class="chatbot">Chat with our AI!</div>
                    <script src="intercom.js"></script>
                </body>
                </html>
            '''.lower(),
            '/privacy': '<h1>Privacy</h1>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = Bill96Hound(mock_scraper)
        lead = await hound.sniff("aicorp.com")
        
        assert lead is not None
        assert lead.gap_type == "bill_96"
        assert "AI system detected but no disclosure" in lead.description
        assert lead.severity == "CRITICAL"
        assert lead.fine_risk == 50000
    
    @pytest.mark.asyncio
    async def test_no_gap_when_ai_disclosed(self, mock_scraper):
        """Test that disclosed AI returns no lead."""
        pages = {
            'homepage': '''
                <div class="chatbot">Powered by AI</div>
            '''.lower(),
            '/privacy': '''
                We use artificial intelligence to power our chatbot.
                This system uses AI technology.
            '''.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = Bill96Hound(mock_scraper)
        lead = await hound.sniff("goodcorp.com")
        
        assert lead is None
    
    @pytest.mark.asyncio
    async def test_no_gap_when_no_ai(self, mock_scraper):
        """Test that sites without AI return no lead."""
        pages = {
            'homepage': '<h1>Regular Corp</h1>'.lower(),
            '/privacy': '<h1>Privacy</h1>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = Bill96Hound(mock_scraper)
        lead = await hound.sniff("regularcorp.com")
        
        assert lead is None


class TestCCPAHound:
    """Test California CCPA hound."""
    
    @pytest.mark.asyncio
    async def test_detects_missing_dns_link(self, mock_scraper):
        """Test detection of missing Do Not Sell link."""
        pages = {
            'homepage': '<h1>California Corp</h1>'.lower(),
            '/privacy': '<h1>Privacy Policy</h1>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = CCPAHound(mock_scraper)
        lead = await hound.sniff("cacorp.com")
        
        assert lead is not None
        assert lead.gap_type == "ccpa"
        assert "Do Not Sell" in lead.description
        assert lead.fine_risk == 7500
    
    @pytest.mark.asyncio
    async def test_no_gap_with_dns_link(self, mock_scraper):
        """Test compliant site returns no lead."""
        pages = {
            '/privacy': '''
                <a href="/dns">Do Not Sell My Personal Information</a>
                California residents have privacy rights under CCPA.
            '''.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = CCPAHound(mock_scraper)
        lead = await hound.sniff("compliantcorp.com")
        
        assert lead is None


class TestGDPRHound:
    """Test EU GDPR hound."""
    
    @pytest.mark.asyncio
    async def test_detects_missing_cookie_consent(self, mock_scraper):
        """Test detection of missing cookie consent."""
        pages = {
            'homepage': '<h1>EU Corp</h1>'.lower(),
            '/privacy': '<h1>Privacy</h1>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = GDPRHound(mock_scraper)
        lead = await hound.sniff("eucorp.com")
        
        assert lead is not None
        assert lead.gap_type == "gdpr"
        assert "cookie consent" in lead.description.lower()
        assert lead.severity in ["HIGH", "CRITICAL"]
    
    @pytest.mark.asyncio
    async def test_detects_critical_multiple_gaps(self, mock_scraper):
        """Test CRITICAL severity for multiple gaps."""
        pages = {
            'homepage': '<h1>Bad EU Corp</h1>'.lower(),
            '/privacy': '<p>We process your data.</p>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        hound = GDPRHound(mock_scraper)
        lead = await hound.sniff("badeucorp.com")
        
        assert lead is not None
        assert lead.severity == "CRITICAL"
        assert lead.fine_risk == 20000000


# ============== SWARM INTEGRATION TESTS ==============

class TestSwarm:
    """Test the Swarm orchestrator."""
    
    @pytest.mark.asyncio
    async def test_swarm_deploys_20_hounds(self):
        """Test that swarm deploys correct number of hounds."""
        swarm = Swarm(delay=0.1)
        assert len(swarm.hounds) == 20
    
    @pytest.mark.asyncio
    async def test_swarm_hunt_deduplicates(self, mock_scraper):
        """Test that swarm deduplicates leads by gap_type."""
        swarm = Swarm(delay=0.1)
        swarm.scraper = mock_scraper
        
        pages = {
            'homepage': '<div class="chatbot">Chat now!</div>'.lower(),
            '/privacy': '<h1>Privacy</h1>'.lower()
        }
        mock_scraper.fetch_privacy_pages.return_value = pages
        
        leads = await swarm.hunt_target("test.com")
        
        gap_types = [l.gap_type for l in leads]
        assert len(gap_types) == len(set(gap_types)), "Duplicate gap types found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
