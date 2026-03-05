"""Create VTT tables

Revision ID: 001_create_vtt_tables
Revises: None
Create Date: 2026-03-05 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_create_vtt_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create VTT Characters table
    op.create_table(
        "vtt_characters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("species", sa.String(length=50), nullable=True),
        sa.Column("rank", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("attributes_json", sa.Text(), nullable=False),
        sa.Column("disciplines_json", sa.Text(), nullable=False),
        sa.Column("talents_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("focuses_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("stress", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("stress_max", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("determination", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "determination_max", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "character_type",
            sa.String(length=20),
            nullable=True,
            server_default="support",
        ),
        sa.Column("pronouns", sa.String(length=50), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("values_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("equipment_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("environment", sa.String(length=100), nullable=True),
        sa.Column("upbringing", sa.String(length=100), nullable=True),
        sa.Column("career_path", sa.String(length=100), nullable=True),
        sa.Column("token_url", sa.String(length=500), nullable=True),
        sa.Column("token_scale", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "is_visible_to_players", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column("vtt_position_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "vtt_status_effects_json", sa.Text(), nullable=False, server_default="[]"
        ),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("scene_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scene_id"],
            ["scenes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create VTT Ships table
    op.create_table(
        "vtt_ships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("ship_class", sa.String(length=50), nullable=False),
        sa.Column("ship_registry", sa.String(length=20), nullable=True),
        sa.Column("scale", sa.Integer(), nullable=False),
        sa.Column("systems_json", sa.Text(), nullable=False),
        sa.Column("departments_json", sa.Text(), nullable=False),
        sa.Column("weapons_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("talents_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("traits_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("breaches_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("shields", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shields_max", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resistance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "has_reserve_power", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column("shields_raised", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("weapons_armed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("crew_quality", sa.String(length=20), nullable=True),
        sa.Column("token_url", sa.String(length=500), nullable=True),
        sa.Column("token_scale", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "is_visible_to_players", sa.Boolean(), nullable=False, server_default="1"
        ),
        sa.Column("vtt_position_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "vtt_status_effects_json", sa.Text(), nullable=False, server_default="[]"
        ),
        sa.Column("vtt_facing_direction", sa.String(length=20), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("scene_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scene_id"],
            ["scenes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Universe Library table
    op.create_table(
        "universe_library",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "reference_data_json", sa.Text(), nullable=False, server_default="{}"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create Traits table
    op.create_table(
        "traits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trait_type", sa.String(length=50), nullable=False),
        sa.Column("game_effects_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_positive", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create Talents table
    op.create_table(
        "talents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("game_effects_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create Weapons table
    op.create_table(
        "weapons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("weapon_type", sa.String(length=20), nullable=False),
        sa.Column("damage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "range", sa.String(length=20), nullable=False, server_default="medium"
        ),
        sa.Column("qualities_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "requires_calibration", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("delivery_system", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create indexes for performance
    op.create_index(
        op.f("ix_vtt_characters_campaign_id"),
        "vtt_characters",
        ["campaign_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_vtt_characters_scene_id"), "vtt_characters", ["scene_id"], unique=False
    )
    op.create_index(
        op.f("ix_vtt_ships_campaign_id"), "vtt_ships", ["campaign_id"], unique=False
    )
    op.create_index(
        op.f("ix_vtt_ships_scene_id"), "vtt_ships", ["scene_id"], unique=False
    )
    op.create_index(
        op.f("ix_universe_library_category"),
        "universe_library",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_traits_trait_type"), "traits", ["trait_type"], unique=False
    )
    op.create_index(
        op.f("ix_talents_discipline"), "talents", ["discipline"], unique=False
    )
    op.create_index(
        op.f("ix_weapons_weapon_type"), "weapons", ["weapon_type"], unique=False
    )


def downgrade():
    # Drop indexes first
    op.drop_index(op.f("ix_weapons_weapon_type"), table_name="weapons")
    op.drop_index(op.f("ix_talents_discipline"), table_name="talents")
    op.drop_index(op.f("ix_traits_trait_type"), table_name="traits")
    op.drop_index(op.f("ix_universe_library_category"), table_name="universe_library")
    op.drop_index(op.f("ix_vtt_ships_scene_id"), table_name="vtt_ships")
    op.drop_index(op.f("ix_vtt_ships_campaign_id"), table_name="vtt_ships")
    op.drop_index(op.f("ix_vtt_characters_scene_id"), table_name="vtt_characters")
    op.drop_index(op.f("ix_vtt_characters_campaign_id"), table_name="vtt_characters")

    # Drop tables
    op.drop_table("weapons")
    op.drop_table("talents")
    op.drop_table("traits")
    op.drop_table("universe_library")
    op.drop_table("vtt_ships")
    op.drop_table("vtt_characters")
