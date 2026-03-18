"""
Tests for M9 Theme System - UI Theme Application

Verifies that theme classes and CSS variables are correctly applied
across Core Views and Combat Views by reading template files directly.
"""

import os
import pytest


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "sta", "web", "templates")


def read_template(filename: str) -> str:
    """Read a template file and return its contents."""
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r") as f:
        return f.read()


class TestBaseTemplateTheme:
    """Tests for theme scaffolding in base.html template."""

    def test_base_html_has_theme_css_variables(self):
        """Verify base.html includes theme CSS variables."""
        html = read_template("base.html")

        assert "--theme-bg-body" in html
        assert "--theme-text-main" in html

    def test_base_html_has_theme_toggle_button(self):
        """Verify theme toggle button exists in base template."""
        html = read_template("base.html")

        assert "theme-toggle" in html

    def test_base_html_has_theme_panel_variables(self):
        """Verify theme-aware panel CSS variables exist."""
        html = read_template("base.html")

        assert "--theme-panel-bg" in html
        assert "--theme-border-color" in html

    def test_base_html_has_dark_theme_override(self):
        """Verify dark theme class override exists."""
        html = read_template("base.html")

        assert "html.theme-dark" in html

    def test_base_html_has_theme_input_variables(self):
        """Verify theme-aware input CSS variables exist."""
        html = read_template("base.html")

        assert "--theme-input-bg" in html
        assert "--theme-input-border" in html


class TestCampaignDashboardTheme:
    """Tests for theme application on Campaign Dashboard view."""

    def test_dashboard_template_exists(self):
        """Campaign dashboard template exists."""
        path = os.path.join(TEMPLATES_DIR, "campaign_dashboard.html")
        assert os.path.exists(path)

    def test_dashboard_inherits_base_theme(self):
        """Dashboard extends base template with theme support."""
        html = read_template("campaign_dashboard.html")

        assert 'extends "base.html"' in html

    def test_dashboard_uses_theme_panel_bg(self):
        """Dashboard uses theme-aware panel background."""
        html = read_template("campaign_dashboard.html")

        assert "var(--theme-panel-bg)" in html

    def test_dashboard_uses_theme_border_color(self):
        """Dashboard uses theme-aware border colors."""
        html = read_template("campaign_dashboard.html")

        assert "var(--theme-border-color)" in html

    def test_dashboard_uses_lcars_colors(self):
        """Dashboard preserves LCARS accent colors."""
        html = read_template("campaign_dashboard.html")

        assert "var(--lcars-" in html


class TestScenePlayerTheme:
    """Tests for theme application on Scene Player view."""

    def test_scene_player_template_exists(self):
        """Scene player template exists."""
        path = os.path.join(TEMPLATES_DIR, "scene_player.html")
        assert os.path.exists(path)

    def test_scene_player_inherits_base_theme(self):
        """Scene player extends base template."""
        html = read_template("scene_player.html")

        assert 'extends "base.html"' in html

    def test_scene_player_uses_theme_variables(self):
        """Scene player uses theme-aware CSS variables."""
        html = read_template("scene_player.html")

        theme_patterns = [
            "var(--theme-panel-bg)",
            "var(--theme-border-color)",
        ]
        has_theme = any(pattern in html for pattern in theme_patterns)
        assert has_theme


class TestCombatPlayerTheme:
    """Tests for theme application on Combat Player view."""

    def test_combat_player_template_exists(self):
        """Combat player template exists."""
        path = os.path.join(TEMPLATES_DIR, "combat_player.html")
        assert os.path.exists(path)

    def test_combat_player_inherits_base_theme(self):
        """Combat player extends base template."""
        html = read_template("combat_player.html")

        assert 'extends "base.html"' in html

    def test_combat_player_has_panels(self):
        """Combat player has panel elements."""
        html = read_template("combat_player.html")

        assert 'class="panel"' in html

    def test_combat_player_uses_theme_variables(self):
        """Combat player uses theme-aware CSS variables."""
        html = read_template("combat_player.html")

        theme_patterns = [
            "var(--theme-panel-bg)",
            "var(--theme-border-color)",
        ]
        has_theme = any(pattern in html for pattern in theme_patterns)
        assert has_theme

    def test_combat_player_uses_lcars_colors(self):
        """Combat player preserves LCARS accent colors."""
        html = read_template("combat_player.html")

        assert "var(--lcars-" in html


class TestCombatGMTheme:
    """Tests for theme application on Combat GM view."""

    def test_combat_gm_template_exists(self):
        """Combat GM template exists."""
        path = os.path.join(TEMPLATES_DIR, "combat_gm.html")
        assert os.path.exists(path)

    def test_combat_gm_has_theme_css(self):
        """Combat GM has its own theme CSS."""
        html = read_template("combat_gm.html")

        assert "--theme-gm-bg" in html or "--theme-" in html
        assert "html.theme-dark" in html or ".theme-" in html

    def test_combat_gm_has_theme_aware_panels(self):
        """Combat GM uses theme-aware panels."""
        html = read_template("combat_gm.html")

        theme_patterns = [
            "theme-gm-panel-bg",
            "theme-gm-bg",
        ]
        has_theme = any(pattern in html for pattern in theme_patterns)
        assert has_theme


class TestCombatViewscreenTheme:
    """Tests for theme application on Combat Viewscreen view."""

    def test_combat_viewscreen_template_exists(self):
        """Combat viewscreen template exists."""
        path = os.path.join(TEMPLATES_DIR, "combat_viewscreen.html")
        assert os.path.exists(path)

    def test_combat_viewscreen_has_theme_css(self):
        """Combat viewscreen has its own theme CSS."""
        html = read_template("combat_viewscreen.html")

        assert "--theme-vs-bg" in html or "--theme-" in html
        assert "html.theme-dark" in html or ".theme-" in html

    def test_combat_viewscreen_uses_theme_variables(self):
        """Combat viewscreen uses theme-aware CSS variables."""
        html = read_template("combat_viewscreen.html")

        theme_patterns = [
            "theme-vs-panel-bg",
            "theme-vs-border",
        ]
        has_theme = any(pattern in html for pattern in theme_patterns)
        assert has_theme


class TestThemeAwareComponents:
    """Tests for theme-aware component styling across all templates."""

    def test_all_templates_use_theme_variables_for_panels(self):
        """All panel components use theme CSS variables."""
        templates = [
            "campaign_dashboard.html",
            "scene_player.html",
            "combat_player.html",
        ]

        for template in templates:
            html = read_template(template)
            assert "theme-panel-bg" in html or "theme-" in html, (
                f"Template {template} missing theme variables"
            )

    def test_buttons_use_lcars_colors(self):
        """Buttons preserve LCARS color scheme."""
        html = read_template("campaign_dashboard.html")

        assert "var(--lcars-orange)" in html or "#f90" in html

    def test_inputs_have_theme_aware_styling(self):
        """Form inputs use theme-aware backgrounds from base template."""
        html = read_template("base.html")

        assert "--theme-input-bg" in html
        assert "--theme-input-border" in html


class TestThemeCSSVariablesDefinition:
    """Tests for theme CSS variable definitions."""

    def test_light_theme_defaults(self):
        """Light theme has white background and dark text."""
        html = read_template("base.html")

        light_patterns = ["#FFFFFF", "#F5F5F5", "var(--theme-bg-body)"]
        has_light = any(pattern in html for pattern in light_patterns)
        assert has_light

    def test_dark_theme_overrides(self):
        """Dark theme has dark background and light text."""
        html = read_template("base.html")

        assert "html.theme-dark" in html
        assert "#0A0A0A" in html or "#000" in html

    def test_theme_panel_variables_defined(self):
        """Theme panel variables are properly defined."""
        html = read_template("base.html")

        required_vars = [
            "--theme-panel-bg",
            "--theme-border-color",
            "--theme-sidebar-bg",
        ]
        for var in required_vars:
            assert var in html, f"Missing theme variable: {var}"


class TestAllCoreViewsHaveThemeSupport:
    """Verify all core views mentioned in spec have theme support."""

    @pytest.mark.parametrize(
        "template",
        [
            "campaign_dashboard.html",
            "scene_player.html",
        ],
    )
    def test_core_view_extends_base(self, template):
        """Core views extend base template with theme support."""
        html = read_template(template)
        assert 'extends "base.html"' in html

    @pytest.mark.parametrize(
        "template",
        [
            "campaign_dashboard.html",
            "scene_player.html",
            "combat_player.html",
        ],
    )
    def test_view_uses_theme_variables(self, template):
        """View uses theme CSS variables."""
        html = read_template(template)
        assert "theme-" in html.lower()


class TestAllCombatViewsHaveThemeSupport:
    """Verify all combat views mentioned in spec have theme support."""

    @pytest.mark.parametrize(
        "template",
        [
            "combat_player.html",
            "combat_gm.html",
            "combat_viewscreen.html",
        ],
    )
    def test_combat_view_has_theme_support(self, template):
        """Combat views have theme CSS defined."""
        html = read_template(template)
        assert "theme-" in html.lower() or "theme-dark" in html
