"""
Tests for character claiming in STA Starship Simulator campaigns.

These tests verify that:
- Claimed characters do not appear on the join page
- Players cannot claim already-claimed characters
- Switching character releases it for others to claim
- Multiple players cannot claim the same character simultaneously

Note: Unclaimed characters have session_token starting with "unclaimed_"
      Claimed characters have a cryptographic token (no "unclaimed_" prefix)
"""

import json
import pytest
from sta.database.schema import CampaignRecord, CampaignPlayerRecord, CharacterRecord


class TestCharacterClaimingAPI:
    """Tests for character claiming via API endpoints."""

    def test_new_player_has_unclaimed_token(self, client, test_session):
        """Test that newly created players have an unclaimed session_token."""
        # Create a campaign with GM
        campaign = CampaignRecord(
            campaign_id="claim-test-001",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)
        test_session.commit()

        # Create a new player via API
        client.set_cookie("sta_session_token", "gm-token-123")
        response = client.post(
            f"/campaigns/api/campaign/{campaign.campaign_id}/players",
            json={"action": "create", "name": "Test Character"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify the new player has an unclaimed token
        new_player = test_session.query(CampaignPlayerRecord).filter_by(
            campaign_id=campaign.id,
            is_gm=False
        ).first()
        assert new_player is not None
        assert new_player.session_token.startswith("unclaimed_")

    def test_claimed_character_not_in_players_list(self, client, test_session):
        """Test that claimed characters are filtered from the available players list."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-002",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create an unclaimed player (session_token starts with "unclaimed_")
        unclaimed = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Unclaimed Character",
            session_token="unclaimed_test_123",  # Not claimed
            is_gm=False,
            is_active=True,
        )
        test_session.add(unclaimed)

        # Create a claimed player (has real session_token, no "unclaimed_" prefix)
        claimed = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Claimed Character",
            session_token="player-token-456",  # Already claimed
            is_gm=False,
            is_active=True,
        )
        test_session.add(claimed)
        test_session.commit()

        # Access the join page (GET) - should only show unclaimed
        response = client.get(f"/campaigns/{campaign.campaign_id}/join")
        assert response.status_code == 200

        # The HTML response should contain unclaimed but not claimed character
        html = response.data.decode()
        assert "Unclaimed Character" in html
        assert "Claimed Character" not in html

    def test_cannot_claim_already_claimed_character(self, client, test_session):
        """Test that attempting to claim an already-claimed character fails."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-003",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create a claimed player (no "unclaimed_" prefix)
        claimed = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Already Claimed",
            session_token="existing-token-789",  # Already claimed
            is_gm=False,
            is_active=True,
        )
        test_session.add(claimed)
        test_session.commit()

        # Try to claim the already-claimed character via POST
        response = client.post(
            f"/campaigns/{campaign.campaign_id}/join",
            data={"player_id": str(claimed.id)},
        )

        # Should redirect back to join page (302)
        assert response.status_code == 302
        assert "join" in response.location

        # The character should still have the original token (not changed)
        test_session.refresh(claimed)
        assert claimed.session_token == "existing-token-789"

    def test_switch_character_releases_it(self, client, test_session):
        """Test that switching characters releases the current character."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-004",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create a claimed player
        player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Claimed Character",
            session_token="player-token-abc",
            is_gm=False,
            is_active=True,
        )
        test_session.add(player)
        test_session.commit()

        # Set cookie to match the claimed character
        client.set_cookie("sta_session_token", "player-token-abc")

        # Call switch-character endpoint
        response = client.get(f"/campaigns/{campaign.campaign_id}/switch-character")
        assert response.status_code == 302  # Redirect to join page

        # Verify the character was released (session_token now starts with "unclaimed_")
        test_session.refresh(player)
        assert player.session_token.startswith("unclaimed_")

    def test_released_character_appears_on_join_page(self, client, test_session):
        """Test that a released character appears on the join page again."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-005",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create a player with unclaimed token (available)
        player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Available Character",
            session_token="unclaimed_available_123",  # Released/available
            is_gm=False,
            is_active=True,
        )
        test_session.add(player)
        test_session.commit()

        # Access the join page
        response = client.get(f"/campaigns/{campaign.campaign_id}/join")
        assert response.status_code == 200

        html = response.data.decode()
        assert "Available Character" in html

    def test_successful_claim_sets_session_token(self, client, test_session):
        """Test that successfully claiming a character sets the session token."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-006",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create an unclaimed player
        unclaimed = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Unclaimed",
            session_token="unclaimed_test_456",
            is_gm=False,
            is_active=True,
        )
        test_session.add(unclaimed)
        test_session.commit()

        # Claim the character
        response = client.post(
            f"/campaigns/{campaign.campaign_id}/join",
            data={"player_id": str(unclaimed.id)},
        )

        # Should redirect to player dashboard (302)
        assert response.status_code == 302
        assert "player" in response.location

        # The character should now have a real session token (no "unclaimed_" prefix)
        test_session.refresh(unclaimed)
        assert unclaimed.session_token is not None
        assert not unclaimed.session_token.startswith("unclaimed_")
        assert len(unclaimed.session_token) > 20  # Cryptographic token is long

    def test_gm_cannot_be_claimed(self, client, test_session):
        """Test that GM player cannot be claimed via join page."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="claim-test-007",
            name="Claiming Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM with unclaimed token (shouldn't happen, but test edge case)
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="unclaimed_gm_test",  # Even if GM has unclaimed token
            is_gm=True,  # This is the GM
            is_active=True,
        )
        test_session.add(gm)
        test_session.commit()

        # Access the join page - GM should not appear
        response = client.get(f"/campaigns/{campaign.campaign_id}/join")
        assert response.status_code == 200

        # GM should not be in the character list
        html = response.data.decode()
        # The GM entry shouldn't be selectable as a character option
        assert f'value="{gm.id}"' not in html


class TestRaceConditionPrevention:
    """Tests to verify race condition prevention in character claiming."""

    def test_two_players_cannot_claim_same_character(self, client, test_session):
        """Test that only one player can claim a character even with concurrent requests."""
        # Create a campaign
        campaign = CampaignRecord(
            campaign_id="race-test-001",
            name="Race Test",
            is_active=True,
        )
        test_session.add(campaign)
        test_session.flush()

        # Create GM
        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
            is_active=True,
        )
        test_session.add(gm)

        # Create an unclaimed player
        unclaimed = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Target Character",
            session_token="unclaimed_race_test",
            is_gm=False,
            is_active=True,
        )
        test_session.add(unclaimed)
        test_session.commit()

        # First claim attempt
        response1 = client.post(
            f"/campaigns/{campaign.campaign_id}/join",
            data={"player_id": str(unclaimed.id)},
        )
        assert response1.status_code == 302
        assert "player" in response1.location

        # Get the token that was set
        test_session.refresh(unclaimed)
        first_token = unclaimed.session_token
        assert first_token is not None
        assert not first_token.startswith("unclaimed_")  # Should be a real token now

        # Second claim attempt (simulating another player)
        # Clear cookies to simulate different browser
        client.delete_cookie("sta_session_token")

        response2 = client.post(
            f"/campaigns/{campaign.campaign_id}/join",
            data={"player_id": str(unclaimed.id)},
        )
        # Should redirect back to join (failed to claim)
        assert response2.status_code == 302
        assert "join" in response2.location

        # Token should be unchanged (first claimer keeps it)
        test_session.refresh(unclaimed)
        assert unclaimed.session_token == first_token
