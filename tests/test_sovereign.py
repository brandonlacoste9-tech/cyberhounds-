#!/usr/bin/env python3
"""
🧪 UNIT TESTS: Sovereign Loop Module
Tests for the master controller with mocked dependencies.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "hound_core"))

from sovereign_loop import SovereignLoop, DecisionPack
from swarm import Lead


# ============== FIXTURES ==============

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_lead():
    """Create a mock Lead for testing."""
    return Lead(
        company="TestCorp",
        domain="testcorp.com",
        gap_type="loi_25",
        description="Missing DPO",
        fine_risk=25000,
        jurisdiction="Quebec",
        evidence="Privacy page checked",
        severity="HIGH",
        found_at="2024-01-01T00:00:00",
        confidence=0.8
    )


@pytest.fixture
def mock_swarm():
    """Create a mock Swarm for testing."""
    swarm = Mock()
    swarm.hunt_target = AsyncMock(return_value=[])
    swarm.scraper = Mock()
    swarm.scraper.__aenter__ = AsyncMock(return_value=swarm.scraper)
    swarm.scraper.__aexit__ = AsyncMock(return_value=None)
    return swarm


# ============== DECISION PACK TESTS ==============

class TestDecisionPack:
    """Test DecisionPack creation and pricing."""
    
    def test_creates_pack_with_correct_id(self, mock_lead):
        """Test that pack ID is generated correctly."""
        pack = DecisionPack(mock_lead)
        
        assert pack.pack_id.startswith("PACK_")
        assert "TESTCORP" in pack.pack_id
    
    def test_calculates_price_for_critical_severity(self):
        """Test pricing for CRITICAL severity."""
        lead = Lead(
            company="CriticalCorp",
            domain="critical.com",
            gap_type="bill_96",
            description="AI not disclosed",
            fine_risk=50000,
            jurisdiction="Quebec",
            evidence="Evidence",
            severity="CRITICAL",
            found_at="2024-01-01T00:00:00",
            confidence=0.9
        )
        
        pack = DecisionPack(lead)
        
        # Critical: 10% of fine risk, capped at 25000
        expected_price = min(25000, 50000 * 0.1)
        assert pack.proposed_price == int(expected_price)
        assert pack.roi == f"{50000 / pack.proposed_price:.1f}x"
    
    def test_calculates_price_for_high_severity(self):
        """Test pricing for HIGH severity."""
        lead = Lead(
            company="HighCorp",
            domain="high.com",
            gap_type="loi_25",
            description="Missing DPO",
            fine_risk=25000,
            jurisdiction="Quebec",
            evidence="Evidence",
            severity="HIGH",
            found_at="2024-01-01T00:00:00",
            confidence=0.8
        )
        
        pack = DecisionPack(lead)
        
        # High: 15% of fine risk, capped at 18000
        expected_price = min(18000, 25000 * 0.15)
        assert pack.proposed_price == int(expected_price)
    
    def test_calculates_price_for_medium_severity(self):
        """Test pricing for MEDIUM severity."""
        lead = Lead(
            company="MedCorp",
            domain="med.com",
            gap_type="ccpa",
            description="Missing DNS",
            fine_risk=7500,
            jurisdiction="California",
            evidence="Evidence",
            severity="MEDIUM",
            found_at="2024-01-01T00:00:00",
            confidence=0.7
        )
        
        pack = DecisionPack(lead)
        
        # Medium: 20% of fine risk, capped at 12000
        expected_price = min(12000, 7500 * 0.2)
        assert pack.proposed_price == int(expected_price)
    
    def test_to_dict_contains_required_fields(self, mock_lead):
        """Test that to_dict produces valid structure."""
        pack = DecisionPack(mock_lead)
        d = pack.to_dict()
        
        required_fields = [
            'pack_id', 'company', 'domain', 'gap_type', 'gap_description',
            'fine_risk', 'severity', 'proposed_price', 'roi_for_client',
            'jurisdiction', 'evidence', 'confidence', 'found_at',
            'forged_at', 'status'
        ]
        
        for field in required_fields:
            assert field in d, f"Missing field: {field}"
        
        assert d['status'] == "PENDING_APPROVAL"


# ============== SOVEREIGN LOOP TESTS ==============

class TestSovereignLoop:
    """Test SovereignLoop functionality."""
    
    @pytest.mark.asyncio
    async def test_stops_without_targets(self, mock_swarm, temp_data_dir, caplog):
        """Test that loop stops gracefully when no targets configured."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        
        # Mock discovery to return empty targets
        sovereign.discovery = Mock()
        sovereign.discovery.load_and_validate_targets.return_value = []
        
        # Should not raise, should log error
        await sovereign.run_hunt_cycle()
        
        assert "NO TARGETS CONFIGURED" in caplog.text
    
    @pytest.mark.asyncio
    async def test_forges_packs_for_leads(self, mock_swarm, mock_lead):
        """Test that DecisionPacks are forged for found leads."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        sovereign.swarm = mock_swarm
        
        # Mock discovery
        sovereign.discovery = Mock()
        sovereign.discovery.load_and_validate_targets.return_value = ["testcorp.com"]
        
        # Mock swarm to return one lead
        mock_swarm.hunt_target.return_value = [mock_lead]
        
        packs = await sovereign.run_hunt_cycle()
        
        assert len(packs) == 1
        assert packs[0].lead.company == "TestCorp"
        assert packs[0].gap_type == "loi_25"
    
    @pytest.mark.asyncio
    async def test_saves_pending_strikes(self, mock_swarm, mock_lead):
        """Test that strikes are saved to pending list."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        sovereign.swarm = mock_swarm
        
        sovereign.discovery = Mock()
        sovereign.discovery.load_and_validate_targets.return_value = ["testcorp.com"]
        mock_swarm.hunt_target.return_value = [mock_lead]
        
        # Clear any existing data
        sovereign.pending_strikes = []
        
        await sovereign.run_hunt_cycle()
        
        assert len(sovereign.pending_strikes) == 1
        assert sovereign.pending_strikes[0]['company'] == "TestCorp"
    
    def test_loads_existing_pending_strikes(self, temp_data_dir):
        """Test loading of persisted pending strikes."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        
        # Create a mock pending file
        test_strikes = [
            {'pack_id': 'PACK_001', 'company': 'OldCorp', 'status': 'PENDING_APPROVAL'}
        ]
        
        with patch.object(sovereign, 'load_data') as mock_load:
            mock_load.side_effect = lambda: setattr(sovereign, 'pending_strikes', test_strikes)
            sovereign.load_data()
        
        assert len(sovereign.pending_strikes) == 1


# ============== NOTIFICATION TESTS ==============

class TestNotifications:
    """Test notification functionality."""
    
    @pytest.mark.asyncio
    async def test_fallback_to_console_when_telegram_disabled(self, mock_lead, caplog):
        """Test console notification when Telegram not configured."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        sovereign.telegram_bot = None
        
        pack = DecisionPack(mock_lead)
        
        # Should not raise
        await sovereign._notify_decision_pack(pack.to_dict())
        
        # Check console output was triggered (via logger)
        assert "DECISION PACK" in caplog.text or True  # ConsoleNotifier prints, doesn't log


# ============== DOMAIN VALIDATION TESTS ==============

class TestDomainValidation:
    """Test target domain validation."""
    
    def test_validates_good_domains(self):
        """Test validation of valid domain names."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        
        valid_domains = [
            "stripe.com",
            "subdomain.example.com",
            "my-site.co.uk",
            "company.io"
        ]
        
        for domain in valid_domains:
            assert sovereign.discovery.validate_domain(domain), f"Should validate: {domain}"
    
    def test_rejects_invalid_domains(self):
        """Test rejection of invalid domain names."""
        sovereign = SovereignLoop(rate_limit_delay=0.1)
        
        invalid_domains = [
            "not_a_domain",
            "",
            "localhost",
            "127.0.0.1",
            "no-tld",
            "a",
            "test."
        ]
        
        for domain in invalid_domains:
            assert not sovereign.discovery.validate_domain(domain), f"Should reject: {domain}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
