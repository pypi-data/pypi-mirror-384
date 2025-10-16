"""
SFHunter - High-performance Salesforce URL scanner

A powerful tool for detecting Salesforce instances across multiple URLs
with support for Discord and Telegram notifications.
"""

__version__ = "1.1.0"
__author__ = "SFHunter"
__email__ = "sfhunter@example.com"
__description__ = "High-performance Salesforce URL scanner with Discord/Telegram integration"

from .core import SFHunter

__all__ = ["SFHunter", "__version__"]
