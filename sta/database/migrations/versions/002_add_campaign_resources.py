"""Add campaign resource pools

Revision ID: 002_add_campaign_resources
Revises: 001_create_vtt_tables
Create Date: 2026-03-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_campaign_resources"
down_revision = "001_create_vtt_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Add momentum and threat columns to campaigns table
    op.add_column(
        "campaigns",
        sa.Column("momentum", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "campaigns",
        sa.Column("threat", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("campaigns", "threat")
    op.drop_column("campaigns", "momentum")
