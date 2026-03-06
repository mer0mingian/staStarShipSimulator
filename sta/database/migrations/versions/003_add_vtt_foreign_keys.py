"""Add VTT foreign keys to campaign associations

Revision ID: 003_add_vtt_foreign_keys
Revises: 002_add_campaign_resources
Create Date: 2026-03-06 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "003_add_vtt_foreign_keys"
down_revision = "002_add_campaign_resources"
branch_labels = None
depends_on = None


def upgrade():
    # Add vtt_character_id to campaign_players table
    op.add_column(
        "campaign_players",
        sa.Column("vtt_character_id", sa.Integer(), nullable=True),
    )

    # Add vtt_ship_id to campaign_ships table
    op.add_column(
        "campaign_ships",
        sa.Column("vtt_ship_id", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("campaign_ships", "vtt_ship_id")
    op.drop_column("campaign_players", "vtt_character_id")
