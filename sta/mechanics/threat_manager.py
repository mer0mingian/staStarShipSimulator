"""Threat management mechanics for Star Trek Adventures 2nd Edition.

Per Chapter 9 rules, Threat is a GM resource pool used to introduce challenges,
hazards, complications, and reinforcements. It accumulates from failed tasks,
complications, and NPC actions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sta.database.schema import CampaignRecord


class ThreatSpendReason(str, Enum):
    """Reasons for spending Threat as per Chapter 9."""

    HAZARD = "hazard"
    COMPLICATION = "complication"
    REINFORCEMENT = "reinforcement"
    NPC_ACTION = "npc_action"
    SCRAPE = "scrape"
    OTHER = "other"


@dataclass
class ThreatChange:
    """Record of a Threat change."""

    amount: int
    reason: str
    previous_total: int
    new_total: int


@dataclass
class ThreatManager:
    """Manages campaign Threat pool per Chapter 9 rules.

    Threat is a GM-controlled resource pool used to introduce challenges.
    It accumulates through complications, failed tasks, and GM decisions.
    """

    db: AsyncSession
    _change_history: dict[str, list[ThreatChange]] = field(default_factory=dict)

    async def get_threat(self, campaign_id: str) -> tuple[int, int]:
        """Get current and max Threat for a campaign.

        Args:
            campaign_id: The campaign's unique identifier

        Returns:
            Tuple of (current_threat, max_threat)
        """
        stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalars().first()

        if not campaign:
            return (0, 0)

        return (campaign.threat or 0, 24)

    async def gain_threat(self, campaign_id: str, amount: int, reason: str) -> bool:
        """Add Threat to campaign pool.

        Args:
            campaign_id: The campaign's unique identifier
            amount: Amount of Threat to add
            reason: Source/reason for the Threat gain

        Returns:
            True if successful, False if campaign not found
        """
        if amount <= 0:
            return False

        stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalars().first()

        if not campaign:
            return False

        previous_total = campaign.threat or 0
        campaign.threat = previous_total + amount

        self._record_change(
            campaign_id, amount, reason, previous_total, campaign.threat
        )

        await self.db.commit()
        return True

    async def spend_threat(self, campaign_id: str, amount: int, reason: str) -> bool:
        """Spend Threat from campaign pool.

        Args:
            campaign_id: The campaign's unique identifier
            amount: Amount of Threat to spend
            reason: Reason for spending (Hazard, Complication, Reinforcement, etc.)

        Returns:
            True if successful, False if insufficient Threat or campaign not found
        """
        if amount <= 0:
            return False

        stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalars().first()

        if not campaign:
            return False

        current_threat = campaign.threat or 0
        if current_threat < amount:
            return False

        previous_total = current_threat
        campaign.threat = current_threat - amount

        self._record_change(
            campaign_id, -amount, reason, previous_total, campaign.threat
        )

        await self.db.commit()
        return True

    def _record_change(
        self,
        campaign_id: str,
        amount: int,
        reason: str,
        previous_total: int,
        new_total: int,
    ) -> None:
        """Record a Threat change for history tracking."""
        if campaign_id not in self._change_history:
            self._change_history[campaign_id] = []

        self._change_history[campaign_id].append(
            ThreatChange(
                amount=amount,
                reason=reason,
                previous_total=previous_total,
                new_total=new_total,
            )
        )

    def get_history(self, campaign_id: str) -> list[ThreatChange]:
        """Get Threat change history for a campaign."""
        return self._change_history.get(campaign_id, [])
