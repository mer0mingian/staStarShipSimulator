"""Unit tests for MomentumManager mechanics."""

import pytest
from sta.mechanics.momentum_manager import MomentumManager, MomentumChange
from sta.database.schema import CampaignRecord


@pytest.mark.asyncio
class TestMomentumManager:
    """Tests for MomentumManager class."""

    async def test_gain_momentum_success(self, test_session, sample_campaign):
        """test_gain_momentum_success - add momentum."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]

        result = await manager.gain_momentum(campaign.campaign_id, 3, "task_success")

        assert result is True
        current, max_momentum = await manager.get_momentum(campaign.campaign_id)
        assert current == 3

    async def test_gain_momentum_campaign_not_found(self, test_session):
        """test_gain_momentum_campaign_not_found - return False for bad ID."""
        manager = MomentumManager(test_session)

        result = await manager.gain_momentum("nonexistent-id", 3, "task_success")

        assert result is False

    async def test_gain_momentum_invalid_amount(self, test_session, sample_campaign):
        """test_gain_momentum_invalid_amount - zero or negative returns False."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]

        result_zero = await manager.gain_momentum(campaign.campaign_id, 0, "test")
        result_negative = await manager.gain_momentum(campaign.campaign_id, -2, "test")

        assert result_zero is False
        assert result_negative is False

    async def test_spend_momentum_success(self, test_session, sample_campaign):
        """test_spend_momentum_success - spend momentum."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 5
        await test_session.commit()

        result = await manager.spend_momentum(
            campaign.campaign_id, 3, "keep_initiative"
        )

        assert result is True
        current, _ = await manager.get_momentum(campaign.campaign_id)
        assert current == 2

    async def test_spend_momentum_insufficient(self, test_session, sample_campaign):
        """test_spend_momentum_insufficient - fail when not enough."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 2
        await test_session.commit()

        result = await manager.spend_momentum(
            campaign.campaign_id, 4, "keep_initiative"
        )

        assert result is False
        current, _ = await manager.get_momentum(campaign.campaign_id)
        assert current == 2

    async def test_spend_momentum_exact(self, test_session, sample_campaign):
        """test_spend_momentum_exact - spend exact amount leaves zero."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 4
        await test_session.commit()

        result = await manager.spend_momentum(campaign.campaign_id, 4, "repeat_attack")

        assert result is True
        current, _ = await manager.get_momentum(campaign.campaign_id)
        assert current == 0

    async def test_momentum_max_cap(self, test_session, sample_campaign):
        """test_momentum_max_cap - cannot exceed 6."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 4
        await test_session.commit()

        result = await manager.gain_momentum(campaign.campaign_id, 5, "task_success")

        assert result is True
        current, max_momentum = await manager.get_momentum(campaign.campaign_id)
        assert current == 6
        assert max_momentum == 6

    async def test_momentum_at_max_no_gain(self, test_session, sample_campaign):
        """test_momentum_at_max_no_gain - adding to full pool stays at max."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 6
        await test_session.commit()

        await manager.gain_momentum(campaign.campaign_id, 3, "task_success")

        current, _ = await manager.get_momentum(campaign.campaign_id)
        assert current == 6

    async def test_get_momentum(self, test_session, sample_campaign):
        """test_get_momentum - returns (current, 6)."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]
        campaign.momentum = 4
        await test_session.commit()

        current, max_momentum = await manager.get_momentum(campaign.campaign_id)

        assert current == 4
        assert max_momentum == 6

    async def test_get_momentum_not_found(self, test_session):
        """test_get_momentum_not_found - returns (0, 0) for bad ID."""
        manager = MomentumManager(test_session)

        result = await manager.get_momentum("nonexistent-id")

        assert result == (0, 0)

    async def test_history_tracking(self, test_session, sample_campaign):
        """test_history_tracking - verify change history recorded."""
        manager = MomentumManager(test_session)
        campaign = sample_campaign["campaign"]

        await manager.gain_momentum(campaign.campaign_id, 3, "task_success")
        await manager.gain_momentum(campaign.campaign_id, 2, "task_success")
        await manager.spend_momentum(campaign.campaign_id, 2, "keep_initiative")

        history = manager.get_history(campaign.campaign_id)

        assert len(history) == 3
        assert history[0].amount == 3
        assert history[0].reason == "task_success"
        assert history[0].previous_total == 0
        assert history[0].new_total == 3
        assert history[1].amount == 2
        assert history[1].previous_total == 3
        assert history[1].new_total == 5
        assert history[2].amount == -2
        assert history[2].reason == "keep_initiative"
        assert history[2].previous_total == 5
        assert history[2].new_total == 3
