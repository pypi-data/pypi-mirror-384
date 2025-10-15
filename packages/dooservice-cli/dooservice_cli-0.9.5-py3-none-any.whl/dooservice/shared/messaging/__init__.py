"""Unified messaging module for DooService.

This module contains all messaging-related components:
- MessageInterface: Abstract interface for messaging
- MessageLevel: Enumeration of message levels
- ClickMessenger: CLI implementation using Click
"""

from .click_messenger import ClickMessenger
from .messaging import MessageInterface, MessageLevel

__all__ = ["MessageInterface", "MessageLevel", "ClickMessenger"]
