"""
Configuration module for WeChat Work API SDK.
Handles loading configuration from environment variables and .env files.
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration class to manage WeChat Work API settings."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Optional path to .env file
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from default locations
            load_dotenv(".env")
            load_dotenv(".env.local")
        
        # Load configuration from environment variables with defaults
        self.base_url = os.getenv("WEIXIN_WORK_BASE_URL", "https://qyapi.weixin.qq.com/")
        self.corp_id = os.getenv("WEIXIN_WORK_CORP_ID", "")
        self.app_secret = os.getenv("WEIXIN_WORK_APP_SECRET", "")
        self.contacts_sync_secret = os.getenv("WEIXIN_WORK_CONTACTS_SYNC_SECRET", "")
        self.agent_id = os.getenv("WEIXIN_WORK_AGENT_ID", "")
        
        # Validate required configuration
        if not self.corp_id:
            raise ValueError("WEIXIN_WORK_CORP_ID is required")
        if not self.app_secret:
            raise ValueError("WEIXIN_WORK_APP_SECRET is required")
        if not self.contacts_sync_secret:
            raise ValueError("WEIXIN_WORK_CONTACTS_SYNC_SECRET is required")