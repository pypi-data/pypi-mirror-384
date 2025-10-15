"""Constants and visual elements for messaging module.

This module contains all constants used across the messaging system:
- Colors: Standard color definitions
- Icons: Unicode icons for different states
- Styles: Predefined visual styles
- DOOSERVICE_LOGO: ASCII art logo
"""


class Colors:
    """Standard color palette for messaging."""

    # Basic colors
    PRIMARY = "cyan"
    SECONDARY = "blue"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "blue"
    DEBUG = "bright_black"

    # Extended colors
    HIGHLIGHT = "bright_cyan"
    MUTED = "bright_black"
    ACCENT = "magenta"

    # Status colors
    RUNNING = "green"
    STOPPED = "red"
    PAUSED = "yellow"
    CREATED = "cyan"


class Icons:
    """Unicode icons for different states and purposes."""

    # Status icons
    SUCCESS = "✓"
    CHECK = "✓"
    ERROR = "✗"
    CROSS = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    QUESTION = "?"

    # State icons
    RUNNING = "●"
    STOPPED = "○"
    PAUSED = "◐"
    LOADING = "⟳"

    # Arrow icons
    ARROW = "→"
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    ARROW_UP = "↑"
    ARROW_DOWN = "↓"

    # Bullet points
    BULLET = "•"
    CIRCLE = "◦"
    SQUARE = "▪"

    # Spinner frames
    SPINNER_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    SPINNER_CIRCLE = ["◐", "◓", "◑", "◒"]
    SPINNER_LINE = ["-", "\\", "|", "/"]


class BoxStyles:
    """Box drawing character sets."""

    SINGLE = {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "horizontal": "─",
        "vertical": "│",
    }

    DOUBLE = {
        "top_left": "╔",
        "top_right": "╗",
        "bottom_left": "╚",
        "bottom_right": "╝",
        "horizontal": "═",
        "vertical": "║",
    }

    ROUNDED = {
        "top_left": "╭",
        "top_right": "╮",
        "bottom_left": "╰",
        "bottom_right": "╯",
        "horizontal": "─",
        "vertical": "│",
    }

    HEAVY = {
        "top_left": "┏",
        "top_right": "┓",
        "bottom_left": "┗",
        "bottom_right": "┛",
        "horizontal": "━",
        "vertical": "┃",
    }


class StatusColors:
    """Predefined color mappings for different statuses."""

    INSTANCE_STATUS = {
        "running": Colors.RUNNING,
        "stopped": Colors.STOPPED,
        "paused": Colors.PAUSED,
        "created": Colors.CREATED,
        "unknown": "white",
    }

    MESSAGE_LEVEL = {
        "debug": Colors.DEBUG,
        "info": Colors.INFO,
        "warning": Colors.WARNING,
        "error": Colors.ERROR,
        "success": Colors.SUCCESS,
    }


# DooService ASCII Logo
# fmt: off
# ruff: noqa: E501
DOOSERVICE_LOGO = r"""
/$$$$$$$                       /$$$$$$                                 /$$
| $$__  $$                     /$$__  $$                               |__/
| $$  \ $$  /$$$$$$   /$$$$$$ | $$  \__/  /$$$$$$   /$$$$$$  /$$    /$$ /$$  /$$$$$$$  /$$$$$$
| $$  | $$ /$$__  $$ /$$__  $$|  $$$$$$  /$$__  $$ /$$__  $$|  $$  /$$/| $$ /$$_____/ /$$__  $$
| $$  | $$| $$  \ $$| $$  \ $$ \____  $$| $$$$$$$$| $$  \__/ \  $$/$$/ | $$| $$      | $$$$$$$$
| $$  | $$| $$  | $$| $$  | $$ /$$  \ $$| $$_____/| $$        \  $$$/  | $$| $$      | $$_____/
| $$$$$$$/|  $$$$$$/|  $$$$$$/|  $$$$$$/|  $$$$$$$| $$         \  $/   | $$|  $$$$$$$|  $$$$$$$
|_______/  \______/  \______/  \______/  \_______/|__/          \_/    |__/ \_______/ \_______/
"""
# fmt: on

# Alternative minimal logo
DOOSERVICE_LOGO_MINIMAL = r"""
    ____              _____                 _
   / __ \____  ____  / ___/___  ______   __(_)________
  / / / / __ \/ __ \ \__ \/ _ \/ ___/ | / / / ___/ _ \
 / /_/ / /_/ / /_/ /___/ /  __/ /   | |/ / / /__/  __/
/_____/\____/\____//____/\___/_/    |___/_/\___/\___/
"""

# Version and branding
BRANDING = {
    "name": "DooService",
    "tagline": "Professional Docker Service Management",
    "version_prefix": "v",
}


# Default widths and sizes
class Dimensions:
    """Default dimensions for visual elements."""

    DEFAULT_BOX_WIDTH = 60
    DEFAULT_SECTION_WIDTH = 60
    BANNER_WIDTH = 66
    PROGRESS_BAR_WIDTH = 50


# Timing constants (in seconds)
class Timing:
    """Timing constants for animations."""

    SPINNER_FRAME_DELAY = 0.1
    TYPING_EFFECT_DELAY = 0.03
    PULSE_ON_DURATION = 0.3
    PULSE_OFF_DURATION = 0.3
    ERROR_BLINK_ON = 0.2
    ERROR_BLINK_OFF = 0.2


# Additional constants from ui/constants.py
class Defaults:
    """Default configuration values."""

    CONFIG_FILE = "dooservice.yml"
    DATA_DIR = "/opt/odoo-data"
    ODOO_VERSION = "19.0"
    POSTGRES_VERSION = "17"
    HTTP_PORT = 8069
    LONGPOLLING_PORT = 8072


class HelpText:
    """Reusable help text snippets."""

    CONFIG_OPTION = "Configuration file path (default: dooservice.yml)"
    INTERACTIVE_OPTION = "Select from available options interactively"
    FORCE_OPTION = "Force operation without confirmation"
    VERBOSE_OPTION = "Show detailed output"

    INSTANCE_REQUIRED = "Instance must be created first. Use 'dooservice create <name>'"
    CONFIG_NOT_FOUND = (
        "Configuration file not found. Use 'dooservice init' to create one"
    )


class Links:
    """Important URLs and documentation links."""

    DOCUMENTATION = "https://github.com/apiservicesac/dooservice-cli-py"
    ISSUES = "https://github.com/apiservicesac/dooservice-cli-py/issues"
    DOCKER_INSTALL = "https://docs.docker.com/get-docker/"
    GIT_INSTALL = "https://git-scm.com/downloads"
    ODOO_DOCS = "https://www.odoo.com/documentation"


# Symbols class (alias for Icons for backward compatibility)
class Symbols:
    """Unicode symbols for CLI output (alias for Icons)."""

    CHECK = Icons.CHECK
    CROSS = Icons.CROSS
    ARROW = Icons.ARROW
    BULLET = Icons.BULLET
    WARNING = Icons.WARNING
    INFO = Icons.INFO
