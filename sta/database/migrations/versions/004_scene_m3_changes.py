"""Add M3 scene management tables and columns

Revision ID: 004_scene_m3_changes
Revises: 003_add_vtt_foreign_keys
Create Date: 2026-03-06 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004_scene_m3_changes"
down_revision = "003_add_vtt_foreign_keys"
branch_labels = None
depends_on = None


def upgrade():
    # ============== Add new columns to scenes table ==============
    op.add_column(
        "scenes",
        sa.Column("next_scene_ids_json", sa.Text(), nullable=True, default="[]"),
    )
    op.add_column(
        "scenes",
        sa.Column("previous_scene_ids_json", sa.Text(), nullable=True, default="[]"),
    )
    op.add_column(
        "scenes",
        sa.Column("encounter_config_json", sa.Text(), nullable=True, default="{}"),
    )

    # ============== Create scene_participants table ==============
    op.create_table(
        "scene_participants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("scene_id", sa.Integer, sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column(
            "character_id",
            sa.Integer,
            sa.ForeignKey("vtt_characters.id"),
            nullable=False,
        ),
        sa.Column(
            "player_id", sa.Integer, sa.ForeignKey("campaign_players.id"), nullable=True
        ),
        sa.Column("is_visible_to_players", sa.Boolean, default=False),
        sa.UniqueConstraint("scene_id", "character_id", name="uq_scene_participant"),
    )
    op.create_index(
        "ix_scene_participants_scene_id", "scene_participants", ["scene_id"]
    )
    op.create_index(
        "ix_scene_participants_character_id", "scene_participants", ["character_id"]
    )

    # ============== Create scene_ships table ==============
    op.create_table(
        "scene_ships",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("scene_id", sa.Integer, sa.ForeignKey("scenes.id"), nullable=False),
        sa.Column("ship_id", sa.Integer, sa.ForeignKey("starships.id"), nullable=False),
        sa.Column("is_visible_to_players", sa.Boolean, default=False),
        sa.UniqueConstraint("scene_id", "ship_id", name="uq_scene_ship"),
    )
    op.create_index("ix_scene_ships_scene_id", "scene_ships", ["scene_id"])
    op.create_index("ix_scene_ships_ship_id", "scene_ships", ["ship_id"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_scene_ships_ship_id", table_name="scene_ships")
    op.drop_index("ix_scene_ships_scene_id", table_name="scene_ships")
    op.drop_index("ix_scene_participants_character_id", table_name="scene_participants")
    op.drop_index("ix_scene_participants_scene_id", table_name="scene_participants")

    # Drop tables
    op.drop_table("scene_ships")
    op.drop_table("scene_participants")

    # Drop new columns from scenes
    op.drop_column("scenes", "encounter_config_json")
    op.drop_column("scenes", "previous_scene_ids_json")
    op.drop_column("scenes", "next_scene_ids_json")
