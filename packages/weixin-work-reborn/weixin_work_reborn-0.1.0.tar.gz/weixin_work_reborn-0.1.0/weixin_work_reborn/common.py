"""
Common module for WeChat Work API SDK.
Contains shared functionality like access token management.
"""

import json
import logging
from typing import Dict, Any, Optional
import requests
from cachetools import TTLCache


class AccessTokenManager:
    """
    Manages access token retrieval and caching for WeChat Work API.
    """
    
    def __init__(self, base_url: str, corp_id: str, corp_secret: str, 
                 token_cache_size: int = 100, token_cache_ttl: int = 7000):
        """
        Initialize the access token manager.
        
        Args:
            base_url: Base URL for WeChat Work API
            corp_id: Corporate ID
            corp_secret: Corporate secret
            token_cache_size: Size of the token cache
            token_cache_ttl: Time-to-live for cached tokens in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.token_url = f"{self.base_url}/cgi-bin/gettoken"
        
        # Create a TTL cache for access tokens
        self.token_cache = TTLCache(maxsize=token_cache_size, ttl=token_cache_ttl)
        
        self.logger = logging.getLogger(__name__)
    
    def get_access_token(self) -> str:
        """
        Get the access token, either from cache or by requesting a new one.
        
        Returns:
            The access token as a string
        """
        # Check if we have a cached token
        cache_key = f"{self.corp_id}:{self.corp_secret}"
        if cache_key in self.token_cache:
            return self.token_cache[cache_key]
        
        # Request a new access token
        params = {
            'corpid': self.corp_id,
            'corpsecret': self.corp_secret
        }
        
        try:
            response = requests.get(self.token_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'errcode' in data and data['errcode'] != 0:
                raise Exception(f"Error getting access token: {data.get('errmsg', 'Unknown error')}")
            
            access_token = data['access_token']
            
            # Cache the token
            self.token_cache[cache_key] = access_token
            
            self.logger.info("Successfully obtained new access token")
            return access_token
            
        except requests.RequestException as e:
            raise Exception(f"Network error while getting access token: {str(e)}")
        except KeyError:
            raise Exception("Invalid response format from WeChat Work API")