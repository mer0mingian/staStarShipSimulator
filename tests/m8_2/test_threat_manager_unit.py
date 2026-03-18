"""Unit tests for ThreatManager mechanics."""

import pytest
from sta.mechanics.threat_manager import ThreatManager, ThreatChange
from sta.database.schema import CampaignRecord


@pytest.mark.asyncio
class TestThreatManager:
    """Tests for ThreatManager class."""

    async def test_gain_threat_success(self, test_session, sample_campaign):
        """test_gain_threat_success - add threat to existing campaign."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]

        result = await manager.gain_threat(campaign.campaign_id, 5, "complication")

        assert result is True
        current, max_threat = await manager.get_threat(campaign.campaign_id)
        assert current == 5

    async def test_gain_threat_campaign_not_found(self, test_session):
        """test_gain_threat_campaign_not_found - return False for bad ID."""
        manager = ThreatManager(test_session)

        result = await manager.gain_threat("nonexistent-id", 5, "complication")

        assert result is False

    async def test_gain_threat_invalid_amount(self, test_session, sample_campaign):
        """test_gain_threat_invalid_amount - zero or negative returns False."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]

        result_zero = await manager.gain_threat(campaign.campaign_id, 0, "test")
        result_negative = await manager.gain_threat(campaign.campaign_id, -3, "test")

        assert result_zero is False
        assert result_negative is False

    async def test_spend_threat_success(self, test_session, sample_campaign):
        """test_spend_threat_success - spend threat when sufficient."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.threat = 10
        await test_session.commit()

        result = await manager.spend_threat(campaign.campaign_id, 4, "hazard")

        assert result is True
        current, _ = await manager.get_threat(campaign.campaign_id)
        assert current == 6

    async def test_spend_threat_insufficient(self, test_session, sample_campaign):
        """test_spend_threat_insufficient - return False when not enough threat."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.threat = 3
        await test_session.commit()

        result = await manager.spend_threat(campaign.campaign_id, 5, "hazard")

        assert result is False
        current, _ = await manager.get_threat(campaign.campaign_id)
        assert current == 3

    async def test_spend_threat_exact(self, test_session, sample_campaign):
        """test_spend_threat_exact - spend exact amount leaves zero."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.threat = 7
        await test_session.commit()

        result = await manager.spend_threat(campaign.campaign_id, 7, "reinforcement")

        assert result is True
        current, _ = await manager.get_threat(campaign.campaign_id)
        assert current == 0

    async def test_get_threat(self, test_session, sample_campaign):
        """test_get_threat - returns current and max (24)."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.threat = 12
        await test_session.commit()

        current, max_threat = await manager.get_threat(campaign.campaign_id)

        assert current == 12
        assert max_threat == 24

    async def test_get_threat_not_found(self, test_session):
        """test_get_threat_not_found - returns (0, 0) for bad ID."""
        manager = ThreatManager(test_session)

        result = await manager.get_threat("nonexistent-id")

        assert result == (0, 0)

    async def test_history_tracking(self, test_session, sample_campaign):
        """test_history_tracking - verify change history recorded."""
        manager = ThreatManager(test_session)
        campaign = sample_campaign["campaign"]

        await manager.gain_threat(campaign.campaign_id, 5, "task_failure")
        await manager.gain_threat(campaign.campaign_id, 3, "complication")
        await manager.spend_threat(campaign.campaign_id, 2, "hazard")

        history = manager.get_history(campaign.campaign_id)

        assert len(history) == 3
        assert history[0].amount == 5
        assert history[0].reason == "task_failure"
        assert history[0].previous_total == 0
        assert history[0].new_total == 5
        assert history[1].amount == 3
        assert history[1].previous_total == 5
        assert history[1].new_total == 8
        assert history[2].amount == -2
        assert history[2].reason == "hazard"
        assert history[2].previous_total == 8
        assert history[2].new_total == 6
