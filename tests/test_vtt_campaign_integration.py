"""Tests for VTT Character/Ship Integration with Campaign Management (M2 Task 2.3)."""

import pytest
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
    CampaignShipRecord,
    CharacterRecord,
    StarshipRecord,
)


class TestVTTCharacterLinking:
    """Tests for linking VTT characters to campaign players."""

    @pytest.mark.asyncio
    async def test_link_vtt_character_to_player(self, client, test_session, sample_campaign):
        """POST /campaigns/api/campaign/<id>/link-character should link VTT character."""
        campaign = sample_campaign["campaign"]
        player = sample_campaign["players"][1]  # Non-GM player
        gm_token = sample_campaign["players"][0].session_token

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"player_id": player.id, "vtt_character_id": 12345},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["vtt_character_id"] == 12345

    @pytest.mark.asyncio
    async def test_link_character_requires_gm_auth(
        self, client, test_session, sample_campaign
    ):
        """Link character should require GM authentication."""
        campaign = sample_campaign["campaign"]
        player = sample_campaign["players"][1]
        player_token = sample_campaign["players"][1].session_token

        client.cookies.set("sta_session_token", player_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"player_id": player.id, "vtt_character_id": 12345},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_link_character_requires_authentication(
        self, client, test_session, sample_campaign
    ):
        """Link character should require authentication."""
        campaign = sample_campaign["campaign"]
        player = sample_campaign["players"][1]

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"player_id": player.id, "vtt_character_id": 12345},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_link_character_requires_player_id(
        self, client, test_session, sample_campaign
    ):
        """Link character should require player_id."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"vtt_character_id": 12345},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_link_character_requires_vtt_character_id(
        self, client, test_session, sample_campaign
    ):
        """Link character should require vtt_character_id."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        player = sample_campaign["players"][1]

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"player_id": player.id},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_link_character_nonexistent_player(
        self, client, test_session, sample_campaign
    ):
        """Link character should return 404 for nonexistent player."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-character",
            json={"player_id": 99999, "vtt_character_id": 12345},
        )
        assert response.status_code == 404


class TestVTTShipLinking:
    """Tests for linking VTT ships to campaign ship pool."""

    @pytest.mark.asyncio
    async def test_link_vtt_ship_to_campaign(
        self, client, test_session, sample_campaign, sample_player_ship_data
    ):
        """POST /campaigns/api/campaign/<id>/link-ship should link VTT ship."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        ship = StarshipRecord(**sample_player_ship_data)
        test_session.add(ship)
        await test_session.flush()

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
        )
        test_session.add(campaign_ship)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"campaign_ship_id": campaign_ship.id, "vtt_ship_id": 67890},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["vtt_ship_id"] == 67890

    @pytest.mark.asyncio
    async def test_link_ship_requires_gm_auth(
        self, client, test_session, sample_campaign, sample_player_ship_data
    ):
        """Link ship should require GM authentication."""
        campaign = sample_campaign["campaign"]
        player_token = sample_campaign["players"][1].session_token

        ship = StarshipRecord(**sample_player_ship_data)
        test_session.add(ship)
        await test_session.flush()

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
        )
        test_session.add(campaign_ship)
        await test_session.commit()

        client.cookies.set("sta_session_token", player_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"campaign_ship_id": campaign_ship.id, "vtt_ship_id": 67890},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_link_ship_requires_authentication(
        self, client, test_session, sample_campaign, sample_player_ship_data
    ):
        """Link ship should require authentication."""
        campaign = sample_campaign["campaign"]

        ship = StarshipRecord(**sample_player_ship_data)
        test_session.add(ship)
        await test_session.flush()

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
        )
        test_session.add(campaign_ship)
        await test_session.commit()

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"campaign_ship_id": campaign_ship.id, "vtt_ship_id": 67890},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_link_ship_requires_campaign_ship_id(
        self, client, test_session, sample_campaign
    ):
        """Link ship should require campaign_ship_id."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"vtt_ship_id": 67890},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_link_ship_requires_vtt_ship_id(
        self, client, test_session, sample_campaign, sample_player_ship_data
    ):
        """Link ship should require vtt_ship_id."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        ship = StarshipRecord(**sample_player_ship_data)
        test_session.add(ship)
        await test_session.flush()

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
        )
        test_session.add(campaign_ship)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"campaign_ship_id": campaign_ship.id},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_link_ship_nonexistent_campaign_ship(
        self, client, test_session, sample_campaign
    ):
        """Link ship should return 404 for nonexistent campaign ship."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        client.cookies.set("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/link-ship",
            json={"campaign_ship_id": 99999, "vtt_ship_id": 67890},
        )
        assert response.status_code == 404


class TestVTTFieldsInSchema:
    """Tests for VTT foreign key fields in schema."""

    @pytest.mark.asyncio
    async def test_campaign_player_has_vtt_character_id_field(
        self, test_session, sample_campaign
    ):
        """CampaignPlayerRecord should have vtt_character_id field."""
        player = sample_campaign["players"][0]
        assert hasattr(player, "vtt_character_id")
        assert player.vtt_character_id is None

    @pytest.mark.asyncio
    async def test_campaign_ship_has_vtt_ship_id_field(
        self, test_session, sample_campaign, sample_player_ship_data
    ):
        """CampaignShipRecord should have vtt_ship_id field."""
        campaign = sample_campaign["campaign"]

        ship = StarshipRecord(**sample_player_ship_data)
        test_session.add(ship)
        await test_session.flush()

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
        )
        test_session.add(campaign_ship)
        await test_session.commit()

        assert hasattr(campaign_ship, "vtt_ship_id")
        assert campaign_ship.vtt_ship_id is None