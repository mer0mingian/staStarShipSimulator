"""Momentum management mechanics for Star Trek Adventures 2nd Edition.

Per Chapter 4 rules, Momentum is a player resource pool used to reroll dice,
gain extra actions, and activate abilities. It accumulates from successful tasks
and can be spent for various benefits.
"""

from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sta.database.schema import CampaignRecord


class MomentumSpendReason(str, Enum):
    """Reasons for spending Momentum as per Chapter 4."""

    TASK_SUCCESS = "task_success"
    KEEP_INITIATIVE = "keep_initiative"
    REPEAT_SHIP_ATTACK = "repeat_ship_attack"
    STORE_COMPLICATION = "store_complication"
    OTHER = "other"


@dataclass
class MomentumChange:
    """Record of a Momentum change."""

    amount: int
    reason: str
    previous_total: int
    new_total: int


@dataclass
class MomentumManager:
    """Manages campaign Momentum pool per Chapter 4 rules.

    Momentum is a player-controlled resource pool used for rerolls, extra actions,
    and ability activation. It accumulates through successful tasks.
    """

    db: AsyncSession
    _change_history: dict[str, list[MomentumChange]] = field(default_factory=dict)

    async def get_momentum(self, campaign_id: str) -> tuple[int, int]:
        """Get current and max Momentum for a campaign.

        Args:
            campaign_id: The campaign's unique identifier

        Returns:
            Tuple of (current_momentum, max_momentum=6)
        """
        stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalars().first()

        if not campaign:
            return (0, 0)

        return (campaign.momentum or 0, 6)

    async def gain_momentum(self, campaign_id: str, amount: int, reason: str) -> bool:
        """Add Momentum to campaign pool.

        Args:
            campaign_id: The campaign's unique identifier
            amount: Amount of Momentum to add
            reason: Source/reason for the Momentum gain

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

        previous_total = campaign.momentum or 0
        new_total = min(previous_total + amount, 6)
        campaign.momentum = new_total

        self._record_change(
            campaign_id, new_total - previous_total, reason, previous_total, new_total
        )

        await self.db.commit()
        return True

    async def spend_momentum(self, campaign_id: str, amount: int, reason: str) -> bool:
        """Spend Momentum from campaign pool.

        Args:
            campaign_id: The campaign's unique identifier
            amount: Amount of Momentum to spend
            reason: Reason for spending (Task Success, Keep Initiative, etc.)

        Returns:
            True if successful, False if insufficient Momentum or campaign not found
        """
        if amount <= 0:
            return False

        stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalars().first()

        if not campaign:
            return False

        current_momentum = campaign.momentum or 0
        if current_momentum < amount:
            return False

        previous_total = current_momentum
        campaign.momentum = current_momentum - amount

        self._record_change(
            campaign_id, -amount, reason, previous_total, campaign.momentum
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
        """Record a Momentum change for history tracking."""
        if campaign_id not in self._change_history:
            self._change_history[campaign_id] = []

        self._change_history[campaign_id].append(
            MomentumChange(
                amount=amount,
                reason=reason,
                previous_total=previous_total,
                new_total=new_total,
            )
        )

    def get_history(self, campaign_id: str) -> list[MomentumChange]:
        """Get Momentum change history for a campaign."""
        return self._change_history.get(campaign_id, [])
