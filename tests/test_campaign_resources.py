"""Tests for campaign resource pool management (Milestone 2, Task 2.1)."""

import pytest
from sta.database.schema import CampaignRecord


@pytest.mark.campaign_resources
class TestCampaignResources:
    """Tests for campaign momentum and threat tracking."""

    @pytest.mark.asyncio
    async def test_get_campaign_resources(self, client, sample_campaign, test_session):
        """GET /campaigns/api/campaign/<id>/resources should return momentum and threat."""
        campaign = sample_campaign["campaign"]
        campaign.momentum = 3
        campaign.threat = 2
        await test_session.commit()

        response = client.get(
            f"/campaigns/api/campaign/{campaign.campaign_id}/resources"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 3
        assert data["threat"] == 2
        assert data["momentum_max"] == 6

    @pytest.mark.asyncio
    async def test_get_resources_nonexistent_campaign(self, client):
        """GET /campaigns/api/campaign/<id>/resources should return 404 for nonexistent campaign."""
        response = client.get("/campaigns/api/campaign/nonexistent/resources")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_momentum(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/momentum should add to momentum pool."""
        campaign = sample_campaign["campaign"]
        campaign.momentum = 2
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/momentum",
            json={"amount": 1},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 3

    @pytest.mark.asyncio
    async def test_add_momentum_max_cap(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/momentum should cap at max of 6."""
        campaign = sample_campaign["campaign"]
        campaign.momentum = 5
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/momentum",
            json={"amount": 5},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 6

    @pytest.mark.asyncio
    async def test_subtract_momentum(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/momentum should subtract when amount is negative."""
        campaign = sample_campaign["campaign"]
        campaign.momentum = 4
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/momentum",
            json={"amount": -2},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 2

    @pytest.mark.asyncio
    async def test_momentum_not_below_zero(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/momentum should not go below 0."""
        campaign = sample_campaign["campaign"]
        campaign.momentum = 1
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/momentum",
            json={"amount": -5},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 0

    @pytest.mark.asyncio
    async def test_add_threat(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/threat should add to threat pool."""
        campaign = sample_campaign["campaign"]
        campaign.threat = 3
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/threat",
            json={"amount": 2},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["threat"] == 5

    @pytest.mark.asyncio
    async def test_subtract_threat(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/threat should subtract when amount is negative."""
        campaign = sample_campaign["campaign"]
        campaign.threat = 4
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/threat",
            json={"amount": -1},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["threat"] == 3

    @pytest.mark.asyncio
    async def test_threat_not_below_zero(self, client, sample_campaign, test_session):
        """POST /campaigns/api/campaign/<id>/threat should not go below 0."""
        campaign = sample_campaign["campaign"]
        campaign.threat = 1
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/threat",
            json={"amount": -5},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["threat"] == 0

    @pytest.mark.asyncio
    async def test_default_values(self, client, sample_campaign, test_session):
        """Campaign resources should default to 0."""
        campaign = sample_campaign["campaign"]

        response = client.get(
            f"/campaigns/api/campaign/{campaign.campaign_id}/resources"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["momentum"] == 0
        assert data["threat"] == 0
