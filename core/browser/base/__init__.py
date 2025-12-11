"""
Базовые модули для браузерных операций
"""

from .base import BasePage
from .error_handler import (
    BaseBrowserError,
    CriticalBrowserError,
    handle_critical_error,
    handle_browser_error
)

__all__ = [
    'BasePage',
    'BaseBrowserError',
    'CriticalBrowserError', 
    'handle_critical_error',
    'handle_browser_error'
]
