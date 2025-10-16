"""
WeChat Work API SDK Reborn
A Python client for interacting with the WeChat Work API.
"""

from .client import WeChatWorkClient
from .exceptions import WeChatWorkException
from .config import Config

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = ["WeChatWorkClient", "WeChatWorkException", "Config"]