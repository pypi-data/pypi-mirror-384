from typing import Any, Dict, List, Optional

import click

from .animations import (
    AnimatedEffects,
    BarAnimations,
    BoxDrawer,
    CounterAnimations,
    LoadingAnimations,
    NotificationEffects,
    ProgressBar,
    Spinner,
    StatusDisplay,
    StatusIndicators,
    TableDisplay,
    WelcomeBanner,
)
from .constants import (
    DOOSERVICE_LOGO,
    DOOSERVICE_LOGO_MINIMAL,
    Colors,
    Icons,
)
from .messaging import MessageInterface, MessageLevel


class ClickMessenger(MessageInterface):
    """Enhanced Click-based messenger with rich animations and visual effects."""

    def __init__(self):
        self._level_colors = {
            MessageLevel.DEBUG: Colors.DEBUG,
            MessageLevel.INFO: Colors.INFO,
            MessageLevel.WARNING: Colors.WARNING,
            MessageLevel.ERROR: Colors.ERROR,
            MessageLevel.SUCCESS: Colors.SUCCESS,
        }
        self._active_spinner: Optional[Spinner] = None

    # ==================== Basic Messaging ====================

    def send_message(
        self, message: str, level: MessageLevel = MessageLevel.INFO, **kwargs: Any
    ) -> None:
        """Send a basic message with level-based coloring."""
        color = self._level_colors.get(level, "white")
        prefix = f"[{level.value.upper()}]"

        if level == MessageLevel.ERROR:
            click.echo(
                click.style(f"{prefix} {message}", fg=color, bold=True), err=True
            )
        else:
            click.echo(click.style(f"{prefix} {message}", fg=color))

    def send_debug(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.DEBUG, **kwargs)

    def send_info(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.INFO, **kwargs)

    def send_warning(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.WARNING, **kwargs)

    def send_error(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.ERROR, **kwargs)

    def send_success(self, message: str, **kwargs: Any) -> None:
        self.send_message(message, MessageLevel.SUCCESS, **kwargs)

    # ==================== Spinner Methods ====================

    def start_spinner(
        self, message: str, color: str = Colors.PRIMARY, show_time: bool = False
    ) -> Spinner:
        """Start an animated spinner."""
        if self._active_spinner:
            self._active_spinner.stop()
        self._active_spinner = Spinner(message, color, show_time)
        self._active_spinner.start()
        return self._active_spinner

    def stop_spinner(
        self, final_message: Optional[str] = None, success: bool = True
    ) -> None:
        """Stop the active spinner."""
        if self._active_spinner:
            self._active_spinner.stop(final_message, success)
            self._active_spinner = None

    def spinner_context(
        self, message: str, color: str = Colors.PRIMARY, show_time: bool = False
    ) -> Spinner:
        """Get a spinner as a context manager."""
        return Spinner(message, color, show_time)

    # ==================== Progress Bar Methods ====================

    def create_progress_bar(
        self, total: int, description: str = "Progress"
    ) -> ProgressBar:
        """Create a progress bar."""
        return ProgressBar(total, description)

    # ==================== Animated Effects ====================

    def show_success_animation(self, message: str) -> None:
        """Show success message with animation."""
        AnimatedEffects.success_animation(message)

    def show_error_animation(self, message: str) -> None:
        """Show error message with animation."""
        AnimatedEffects.error_animation(message)

    def show_typing_effect(self, text: str, color: Optional[str] = None) -> None:
        """Show typing effect animation."""
        AnimatedEffects.typing_effect(text, color=color)

    def show_pulse_text(
        self, text: str, color: str = Colors.PRIMARY, pulses: int = 3
    ) -> None:
        """Show pulsing text effect."""
        AnimatedEffects.pulse_text(text, color, pulses)

    # ==================== Box Drawing Methods ====================

    def draw_single_box(
        self, content: str, width: Optional[int] = None, color: str = Colors.PRIMARY
    ) -> None:
        """Draw a single-line box around content."""
        BoxDrawer.single_line(content, width, color)

    def draw_double_box(
        self, content: str, width: Optional[int] = None, color: str = Colors.SECONDARY
    ) -> None:
        """Draw a double-line box around content."""
        BoxDrawer.double_line(content, width, color)

    def draw_section(self, title: str, color: str = Colors.WARNING) -> None:
        """Draw a section separator."""
        BoxDrawer.section(title, color)

    # ==================== Status Display Methods ====================

    def show_instance_status(self, name: str, status: str, details: dict) -> None:
        """Display instance status in formatted view."""
        StatusDisplay.show_instance_status(name, status, details)

    def show_list(self, items: list, title: str = "Items") -> None:
        """Display a list of items with status indicators."""
        StatusDisplay.show_list(items, title)

    # ==================== Welcome Banner Methods ====================

    def show_welcome_banner(
        self, title: str, subtitle: Optional[str] = None, use_minimal_logo: bool = False
    ) -> None:
        """Show welcome banner with logo."""
        logo = DOOSERVICE_LOGO_MINIMAL if use_minimal_logo else DOOSERVICE_LOGO
        WelcomeBanner.show(title, subtitle, logo)

    def show_banner(
        self, title: str, subtitle: Optional[str] = None, logo: Optional[str] = None
    ) -> None:
        """Show custom banner."""
        WelcomeBanner.show(title, subtitle, logo)

    # ==================== Loading Animation Methods ====================

    def show_dots_loading(
        self, message: str, duration: float = 3.0, color: str = Colors.PRIMARY
    ) -> None:
        """Show animated dots loading effect."""
        LoadingAnimations.dots_loading(message, duration, color)

    def show_bounce_loading(
        self, message: str, duration: float = 3.0, color: str = Colors.PRIMARY
    ) -> None:
        """Show bouncing ball loading animation."""
        LoadingAnimations.bounce_loading(message, duration, color)

    def show_progress_dots(self, total: int, message: str = "Processing") -> None:
        """Show progress using incrementing dots."""
        LoadingAnimations.progress_dots(total, message)

    # ==================== Counter Animation Methods ====================

    def show_count_up(
        self,
        target: int,
        duration: float = 2.0,
        label: str = "Count",
        color: str = Colors.SUCCESS,
    ) -> None:
        """Show animated count up to target number."""
        CounterAnimations.count_up(target, duration, label, color)

    def show_countdown(
        self, seconds: int, message: str = "Starting in", color: str = Colors.WARNING
    ) -> None:
        """Show countdown timer."""
        CounterAnimations.countdown(seconds, message, color)

    # ==================== Bar Animation Methods ====================

    def show_loading_bar(
        self, duration: float = 3.0, color: str = Colors.PRIMARY
    ) -> None:
        """Show animated loading bar."""
        BarAnimations.loading_bar(duration, color=color)

    def show_wave_bar(
        self, cycles: int = 3, width: int = 40, color: str = Colors.PRIMARY
    ) -> None:
        """Show wave animation in a bar."""
        BarAnimations.wave_bar(cycles, width, color)

    # ==================== Status Indicator Methods ====================

    def show_status_badge(self, label: str, status: str, success: bool = True) -> None:
        """Display a status badge."""
        StatusIndicators.show_status_badge(label, status, success)

    def show_metric(
        self, label: str, value: str, icon: str = Icons.BULLET, color: str = Colors.INFO
    ) -> None:
        """Display a metric with icon."""
        StatusIndicators.show_metric(label, value, icon, color)

    def show_step(
        self, step_num: int, total_steps: int, description: str, status: str = "pending"
    ) -> None:
        """Show step in a multi-step process."""
        StatusIndicators.show_step(step_num, total_steps, description, status)

    # ==================== Table Display Methods ====================

    def show_table(
        self, headers: List[str], rows: List[List[str]], title: Optional[str] = None
    ) -> None:
        """Display a formatted table."""
        TableDisplay.show_table(headers, rows, title)

    def show_key_value_list(
        self,
        items: Dict[str, Any],
        title: Optional[str] = None,
        color: str = Colors.PRIMARY,
    ) -> None:
        """Display key-value pairs in a formatted list."""
        TableDisplay.show_key_value_list(items, title, color)

    # ==================== Notification Methods ====================

    def show_notification(
        self, message: str, notification_type: str = "info", duration: float = 2.0
    ) -> None:
        """Show a temporary notification."""
        NotificationEffects.show_notification(message, notification_type, duration)

    def show_alert_box(
        self, message: str, alert_type: str = "warning", width: int = 60
    ) -> None:
        """Show alert in a box."""
        NotificationEffects.show_alert_box(message, alert_type, width)

    # ==================== Convenience Methods ====================

    def success_with_animation(self, message: str) -> None:
        """Show success message with full animation."""
        self.show_success_animation(message)

    def error_with_animation(self, message: str) -> None:
        """Show error message with full animation."""
        self.show_error_animation(message)

    def info_with_icon(self, message: str) -> None:
        """Show info message with icon."""
        click.echo(f"{click.style(Icons.INFO, fg=Colors.INFO)} {message}")

    def warning_with_icon(self, message: str) -> None:
        """Show warning message with icon."""
        click.echo(f"{click.style(Icons.WARNING, fg=Colors.WARNING)} {message}")

    def success_with_icon(self, message: str) -> None:
        """Show success message with icon."""
        click.echo(f"{click.style(Icons.SUCCESS, fg=Colors.SUCCESS)} {message}")

    def error_with_icon(self, message: str) -> None:
        """Show error message with icon."""
        click.echo(f"{click.style(Icons.ERROR, fg=Colors.ERROR)} {message}")

    # ==================== Multi-Step Progress Display ====================

    def show_steps_header(self, steps: List[str], title: str = "Progress") -> None:
        """Show all steps at the beginning with pending status."""
        click.echo()
        BoxDrawer.section(title)
        click.echo()
        self._current_step_states = {}
        for idx, step in enumerate(steps, 1):
            self._current_step_states[idx] = "pending"
            StatusIndicators.show_step(idx, len(steps), step, status="pending")
        click.echo()

    def update_step_status(
        self, step_num: int, total_steps: int, description: str, status: str
    ) -> None:
        """Update the status of a specific step (in_progress, completed, failed)."""
        self._current_step_states[step_num] = status
        # Move cursor up to the step line and update it
        # For now, show it again (in a real implementation, use cursor control)  # noqa: E501
        StatusIndicators.show_step(step_num, total_steps, description, status=status)
