"""Animation components for messaging module.

This module contains all animation-related classes:
- Spinner: Animated spinner for long-running operations
- ProgressBar: Progress bar with visual feedback
- AnimatedEffects: Collection of animated visual effects
"""

import sys
import threading
import time
from typing import Optional

import click

from .constants import BoxStyles, Colors, Dimensions, Icons, StatusColors, Timing


class Spinner:
    """Animated spinner for long-running operations."""

    FRAMES = Icons.SPINNER_DOTS

    def __init__(
        self,
        message: str = "Working",
        color: str = Colors.PRIMARY,
        show_time: bool = False,
    ):
        self.message = message
        self.color = color
        self.show_time = show_time
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._start_time = None
        self._last_line_length = 0

    def _animate(self):
        """Animation loop."""
        idx = 0
        self._start_time = time.time()
        while self._running:
            frame = self.FRAMES[idx % len(self.FRAMES)]

            # Build message
            if self.show_time:
                elapsed = time.time() - self._start_time
                time_str = f" [{elapsed:.1f}s]"
            else:
                time_str = ""

            msg = f"{click.style(frame, fg=self.color)} {self.message}...{time_str}"

            # Clear previous line completely
            sys.stdout.write(f"\r{' ' * self._last_line_length}\r")
            sys.stdout.write(msg)
            sys.stdout.flush()

            self._last_line_length = len(msg)
            time.sleep(Timing.SPINNER_FRAME_DELAY)
            idx += 1

    def start(self):
        """Start the spinner animation."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._animate, daemon=True)
            self._thread.start()

    def stop(self, final_message: Optional[str] = None, success: bool = True):
        """Stop the spinner and show final message."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

        # Clear the entire line thoroughly
        sys.stdout.write(f"\r{' ' * (self._last_line_length + 10)}\r")
        sys.stdout.flush()

        if final_message:
            icon = Icons.SUCCESS if success else Icons.ERROR
            color = Colors.SUCCESS if success else Colors.ERROR

            # Show elapsed time if enabled
            if self.show_time and self._start_time:
                elapsed = time.time() - self._start_time
                time_str = click.style(f" ({elapsed:.1f}s)", fg=Colors.MUTED)
            else:
                time_str = ""

            click.echo(
                click.style(f"{icon} {final_message}", fg=color, bold=True) + time_str
            )

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        success = exc_type is None
        self.stop(success=success)
        return False


class ProgressBar:
    """Progress bar with visual feedback."""

    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.current = 0
        self.description = description

    def update(self, amount: int = 1):
        """Update progress by the specified amount."""
        self.current += amount
        self._render()

    def _render(self):
        """Render the progress bar."""
        percentage = (self.current / self.total) * 100
        bar_width = Dimensions.PROGRESS_BAR_WIDTH
        filled = int((percentage / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        msg = f"\r{self.description}: [{click.style(bar, fg=Colors.PRIMARY)}] {percentage:.0f}%"  # noqa: E501
        sys.stdout.write(msg)
        sys.stdout.flush()

        if self.current >= self.total:
            click.echo()  # New line when complete

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.current < self.total:
            self.current = self.total
            self._render()
        return False


class AnimatedEffects:
    """Collection of animated visual effects."""

    @staticmethod
    def success_animation(message: str):
        """Show success message with animation."""
        frames = Icons.SPINNER_CIRCLE
        for frame in frames * 2:
            sys.stdout.write(f"\r{click.style(frame, fg=Colors.SUCCESS)} {message}")
            sys.stdout.flush()
            time.sleep(Timing.SPINNER_FRAME_DELAY)
        sys.stdout.write(
            f"\r{click.style(Icons.SUCCESS, fg=Colors.SUCCESS, bold=True)} {click.style(message, fg=Colors.SUCCESS, bold=True)}"  # noqa: E501
        )
        click.echo()

    @staticmethod
    def error_animation(message: str):
        """Show error message with animation."""
        for _ in range(3):
            sys.stdout.write(
                f"\r{click.style(Icons.ERROR, fg=Colors.ERROR, bold=True)} {message}"
            )
            sys.stdout.flush()
            time.sleep(Timing.ERROR_BLINK_ON)
            sys.stdout.write(
                f"\r{click.style(Icons.ERROR, fg=Colors.ERROR, dim=True)} {message}"
            )
            sys.stdout.flush()
            time.sleep(Timing.ERROR_BLINK_OFF)
        sys.stdout.write(
            f"\r{click.style(Icons.ERROR, fg=Colors.ERROR, bold=True)} {click.style(message, fg=Colors.ERROR, bold=True)}"  # noqa: E501
        )
        click.echo()

    @staticmethod
    def typing_effect(
        text: str,
        delay: float = Timing.TYPING_EFFECT_DELAY,
        color: Optional[str] = None,
    ):
        """Simulate typing effect."""
        for char in text:
            if color:
                sys.stdout.write(click.style(char, fg=color))
            else:
                sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        click.echo()

    @staticmethod
    def pulse_text(text: str, color: str = Colors.PRIMARY, pulses: int = 3):
        """Create pulsing text effect."""
        for _ in range(pulses):
            sys.stdout.write(f"\r{click.style(text, fg=color, bold=True)}")
            sys.stdout.flush()
            time.sleep(Timing.PULSE_ON_DURATION)
            sys.stdout.write(f"\r{click.style(text, fg=color, dim=True)}")
            sys.stdout.flush()
            time.sleep(Timing.PULSE_OFF_DURATION)
        sys.stdout.write(f"\r{click.style(text, fg=color, bold=True)}")
        click.echo()


class BoxDrawer:
    """Draw beautiful boxes around content."""

    @staticmethod
    def single_line(
        content: str, width: Optional[int] = None, color: str = Colors.PRIMARY
    ):
        """Draw a single-line box around content."""
        lines = content.split("\n")

        if width is None:
            width = max(len(line) for line in lines) + 4

        box = BoxStyles.SINGLE
        top = box["top_left"] + box["horizontal"] * (width - 2) + box["top_right"]
        bottom = (
            box["bottom_left"] + box["horizontal"] * (width - 2) + box["bottom_right"]
        )

        click.echo(click.style(top, fg=color))
        for line in lines:
            padding = " " * (width - len(line) - 4)
            click.echo(
                click.style(
                    f"{box['vertical']} {line}{padding} {box['vertical']}", fg=color
                )
            )
        click.echo(click.style(bottom, fg=color))

    @staticmethod
    def double_line(
        content: str, width: Optional[int] = None, color: str = Colors.SECONDARY
    ):
        """Draw a double-line box around content."""
        lines = content.split("\n")

        if width is None:
            width = max(len(line) for line in lines) + 4

        box = BoxStyles.DOUBLE
        top = box["top_left"] + box["horizontal"] * (width - 2) + box["top_right"]
        bottom = (
            box["bottom_left"] + box["horizontal"] * (width - 2) + box["bottom_right"]
        )

        click.echo(click.style(top, fg=color, bold=True))
        for line in lines:
            padding = " " * (width - len(line) - 4)
            click.echo(
                click.style(
                    f"{box['vertical']} {line}{padding} {box['vertical']}",
                    fg=color,
                    bold=True,
                )
            )
        click.echo(click.style(bottom, fg=color, bold=True))

    @staticmethod
    def section(
        title: str,
        color: str = Colors.WARNING,
        width: int = Dimensions.DEFAULT_SECTION_WIDTH,
    ):
        """Draw a section separator."""
        padding = (width - len(title) - 2) // 2
        line = (
            BoxStyles.SINGLE["horizontal"] * padding
            + f" {title} "
            + BoxStyles.SINGLE["horizontal"] * (width - padding - len(title) - 2)
        )
        click.echo(click.style(line, fg=color, bold=True))


class StatusDisplay:
    """Beautiful status displays for instances and lists."""

    @staticmethod
    def show_instance_status(name: str, status: str, details: dict):
        """Show instance status in a beautiful format."""
        BoxDrawer.section(f"Instance: {name}")

        # Status indicator
        color = StatusColors.INSTANCE_STATUS.get(status.lower(), "white")
        status_icon = Icons.RUNNING

        click.echo(
            f"\n  {click.style(status_icon, fg=color)} Status: {click.style(status.upper(), fg=color, bold=True)}"  # noqa: E501
        )

        # Details
        if details:
            click.echo("\n  Details:")
            for key, value in details.items():
                click.echo(
                    f"    {Icons.BULLET} {click.style(key, fg=Colors.PRIMARY)}: {value}"
                )

        click.echo()

    @staticmethod
    def show_list(items: list, title: str = "Items"):
        """Show a list of items in table format."""
        if not items:
            click.echo(click.style(f"\n  No {title.lower()} found.", fg=Colors.WARNING))
            return

        BoxDrawer.section(title)
        click.echo()

        for item in items:
            name = item.get("name", "Unknown")
            status = item.get("status", "unknown")

            color = StatusColors.INSTANCE_STATUS.get(status.lower(), "white")
            icon = Icons.RUNNING

            click.echo(
                f"  {click.style(icon, fg=color)} {click.style(name, bold=True)} - {click.style(status, fg=color)}"  # noqa: E501
            )

        click.echo()


class WelcomeBanner:
    """Display welcome banners with logo."""

    @staticmethod
    def show(title: str, subtitle: Optional[str] = None, logo: Optional[str] = None):
        """Show welcome banner with logo."""
        # Clear screen effect (optional)
        click.echo("\n" * 2)

        # Show logo if provided
        if logo:
            click.echo(click.style(logo, fg=Colors.SECONDARY, bold=True))
            click.echo()

        # Show title
        BoxDrawer.double_line(
            title, width=Dimensions.BANNER_WIDTH, color=Colors.SECONDARY
        )

        if subtitle:
            click.echo()
            click.echo(click.style(f"  {subtitle}", fg=Colors.MUTED, italic=True))

        click.echo()


class LoadingAnimations:
    """Advanced loading animations for various purposes."""

    @staticmethod
    def dots_loading(message: str, duration: float = 3.0, color: str = Colors.PRIMARY):
        """Show animated dots loading effect."""
        start_time = time.time()
        dots = ""
        while time.time() - start_time < duration:
            dots = "." * ((len(dots) + 1) % 4)
            sys.stdout.write(f"\r{click.style(message, fg=color)}{dots}   ")
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write(f"\r{' ' * (len(message) + 10)}\r")
        sys.stdout.flush()

    @staticmethod
    def bounce_loading(
        message: str, duration: float = 3.0, color: str = Colors.PRIMARY
    ):
        """Show bouncing ball loading animation."""
        frames = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
        start_time = time.time()
        idx = 0
        while time.time() - start_time < duration:
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r{click.style(frame, fg=color)} {message}")
            sys.stdout.flush()
            time.sleep(Timing.SPINNER_FRAME_DELAY)
            idx += 1
        sys.stdout.write(f"\r{' ' * (len(message) + 10)}\r")
        sys.stdout.flush()

    @staticmethod
    def progress_dots(total: int, message: str = "Processing"):
        """Show progress using incrementing dots."""
        for i in range(total + 1):
            percentage = (i / total) * 100
            dots = Icons.BULLET * (i % 10)
            sys.stdout.write(f"\r{message}: {percentage:.0f}% {dots}   ")
            sys.stdout.flush()
            time.sleep(0.2)
        click.echo()


class CounterAnimations:
    """Animated counters and number effects."""

    @staticmethod
    def count_up(
        target: int,
        duration: float = 2.0,
        label: str = "Count",
        color: str = Colors.SUCCESS,
    ):
        """Animate counting up to a target number."""
        steps = 20
        increment = target / steps
        current = 0
        sleep_time = duration / steps

        for _ in range(steps):
            current += increment
            sys.stdout.write(
                f"\r{click.style(f'{label}: {int(current):,}', fg=color, bold=True)}"
            )
            sys.stdout.flush()
            time.sleep(sleep_time)

        sys.stdout.write(
            f"\r{click.style(f'{label}: {target:,}', fg=color, bold=True)}"
        )
        click.echo()

    @staticmethod
    def countdown(
        seconds: int, message: str = "Starting in", color: str = Colors.WARNING
    ):
        """Show countdown timer."""
        for i in range(seconds, 0, -1):
            sys.stdout.write(
                f"\r{click.style(f'{message} {i}s...', fg=color, bold=True)}"
            )
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write(f"\r{' ' * 50}\r")
        click.echo(
            click.style(f"{Icons.SUCCESS} Started!", fg=Colors.SUCCESS, bold=True)
        )


class BarAnimations:
    """Various bar-style animations."""

    @staticmethod
    def loading_bar(
        duration: float = 3.0,
        width: int = Dimensions.PROGRESS_BAR_WIDTH,
        color: str = Colors.PRIMARY,
    ):
        """Animated loading bar that fills over time."""
        steps = 30
        sleep_time = duration / steps

        for i in range(steps + 1):
            filled = int((i / steps) * width)
            bar = "█" * filled + "░" * (width - filled)
            percentage = (i / steps) * 100
            sys.stdout.write(f"\r[{click.style(bar, fg=color)}] {percentage:.0f}%")
            sys.stdout.flush()
            time.sleep(sleep_time)
        click.echo()

    @staticmethod
    def wave_bar(cycles: int = 3, width: int = 40, color: str = Colors.PRIMARY):
        """Show wave animation in a bar."""
        frames = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]

        for _ in range(cycles):
            for i in range(width):
                bar = ""
                for j in range(width):
                    frame_idx = (i + j) % len(frames)
                    bar += frames[frame_idx]
                sys.stdout.write(f"\r{click.style(bar, fg=color)}")
                sys.stdout.flush()
                time.sleep(0.05)
        sys.stdout.write(f"\r{' ' * width}\r")
        sys.stdout.flush()


class StatusIndicators:
    """Visual status indicators and badges."""

    @staticmethod
    def show_status_badge(label: str, status: str, success: bool = True):
        """Display a status badge."""
        color = Colors.SUCCESS if success else Colors.ERROR
        icon = Icons.SUCCESS if success else Icons.ERROR
        badge = f"[{status.upper()}]"
        click.echo(
            f"{click.style(icon, fg=color)} {label}: {click.style(badge, fg=color, bold=True)}"  # noqa: E501
        )

    @staticmethod
    def show_metric(
        label: str, value: str, icon: str = Icons.BULLET, color: str = Colors.INFO
    ):
        """Display a metric with icon."""
        click.echo(
            f"  {click.style(icon, fg=color)} {click.style(label, bold=True)}: {value}"
        )

    @staticmethod
    def show_step(
        step_num: int, total_steps: int, description: str, status: str = "pending"
    ):
        """Show step in a multi-step process."""
        color_map = {
            "pending": Colors.MUTED,
            "in_progress": Colors.PRIMARY,
            "completed": Colors.SUCCESS,
            "failed": Colors.ERROR,
        }
        icon_map = {
            "pending": Icons.CIRCLE,
            "in_progress": Icons.LOADING,
            "completed": Icons.SUCCESS,
            "failed": Icons.ERROR,
        }

        color = color_map.get(status, Colors.MUTED)
        icon = icon_map.get(status, Icons.CIRCLE)
        step_text = f"Step {step_num}/{total_steps}"

        click.echo(
            f"{click.style(icon, fg=color)} {click.style(step_text, fg=color, bold=True)}: {description}"  # noqa: E501
        )


class TableDisplay:
    """Display data in table format with animations."""

    @staticmethod
    def show_table(headers: list, rows: list, title: Optional[str] = None):
        """Display a formatted table."""
        if title:
            BoxDrawer.section(title)
            click.echo()

        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Create separator
        separator = "─" * (sum(col_widths) + len(headers) * 3 + 1)

        # Print header
        header_row = " │ ".join(
            click.style(str(h).ljust(w), fg=Colors.PRIMARY, bold=True)
            for h, w in zip(headers, col_widths)
        )
        click.echo(f"  {header_row}")
        click.echo(f"  {click.style(separator, fg=Colors.MUTED)}")

        # Print rows
        for row in rows:
            row_str = " │ ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            click.echo(f"  {row_str}")

        click.echo()

    @staticmethod
    def show_key_value_list(
        items: dict, title: Optional[str] = None, color: str = Colors.PRIMARY
    ):
        """Display key-value pairs in a formatted list."""
        if title:
            click.echo(click.style(f"\n{title}", fg=color, bold=True))
            click.echo(click.style("─" * len(title), fg=Colors.MUTED))

        max_key_length = max(len(str(k)) for k in items)

        for key, value in items.items():
            key_str = str(key).ljust(max_key_length)
            click.echo(f"  {click.style(key_str, fg=color)}: {value}")

        click.echo()


class NotificationEffects:
    """Various notification and alert effects."""

    @staticmethod
    def show_notification(
        message: str, notification_type: str = "info", duration: float = 2.0
    ):
        """Show a temporary notification."""
        type_config = {
            "info": (Colors.INFO, Icons.INFO),
            "success": (Colors.SUCCESS, Icons.SUCCESS),
            "warning": (Colors.WARNING, Icons.WARNING),
            "error": (Colors.ERROR, Icons.ERROR),
        }

        color, icon = type_config.get(notification_type, (Colors.INFO, Icons.INFO))

        # Show notification
        msg = (
            f"{click.style(icon, fg=color, bold=True)} {click.style(message, fg=color)}"
        )
        click.echo(msg)
        time.sleep(duration)

    @staticmethod
    def show_alert_box(
        message: str,
        alert_type: str = "warning",
        width: int = Dimensions.DEFAULT_BOX_WIDTH,
    ):
        """Show alert in a box."""
        type_config = {
            "info": (Colors.INFO, Icons.INFO),
            "success": (Colors.SUCCESS, Icons.SUCCESS),
            "warning": (Colors.WARNING, Icons.WARNING),
            "error": (Colors.ERROR, Icons.ERROR),
        }

        color, icon = type_config.get(alert_type, (Colors.WARNING, Icons.WARNING))

        lines = message.split("\n")
        box = BoxStyles.HEAVY

        # Top border
        top = box["top_left"] + box["horizontal"] * (width - 2) + box["top_right"]
        click.echo(click.style(top, fg=color, bold=True))

        # Content with icon
        for i, line in enumerate(lines):
            prefix = f"{icon} " if i == 0 else "  "
            padding = " " * (width - len(line) - len(prefix) - 4)
            click.echo(
                click.style(
                    f"{box['vertical']} {prefix}{line}{padding} {box['vertical']}",
                    fg=color,
                    bold=True,
                )
            )

        # Bottom border
        bottom = (
            box["bottom_left"] + box["horizontal"] * (width - 2) + box["bottom_right"]
        )
        click.echo(click.style(bottom, fg=color, bold=True))
