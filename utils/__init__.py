# при добавлении новых модулей - добавлять в __all__
"""Декларация модулей."""
from .hotkey_manager import HotkeyManager
from .clipboard_manager import ClipboardManager

__all__ = ['HotkeyManager', 'ClipboardManager']
