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
    
    def __init__(self, base_url: str, corp_id: str, app_secret: str, contacts_sync_secret: str,
                 token_cache_size: int = 100, token_cache_ttl: int = 7000):
        """
        Initialize the access token manager.
        
        Args:
            base_url: Base URL for WeChat Work API
            corp_id: Corporate ID
            app_secret: App secret for general API access
            contacts_sync_secret: Secret for contacts sync API access
            token_cache_size: Size of the token cache
            token_cache_ttl: Time-to-live for cached tokens in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.corp_id = corp_id
        self.app_secret = app_secret
        self.contacts_sync_secret = contacts_sync_secret
        self.token_url = f"{self.base_url}/cgi-bin/gettoken"
        
        # Create a TTL cache for access tokens
        self.token_cache = TTLCache(maxsize=token_cache_size, ttl=token_cache_ttl)
        
        self.logger = logging.getLogger(__name__)
    
    def get_app_access_token(self) -> str:
        """
        Get the app access token, either from cache or by requesting a new one.
        
        Returns:
            The access token as a string
        """
        return self._get_access_token(self.app_secret, "app")
    
    def get_contacts_sync_access_token(self) -> str:
        """
        Get the contacts sync access token, either from cache or by requesting a new one.
        
        Returns:
            The access token as a string
        """
        return self._get_access_token(self.contacts_sync_secret, "contacts_sync")
    
    def _get_access_token(self, secret: str, token_type: str) -> str:
        """
        Internal method to get access token with a specific secret.
        
        Args:
            secret: The secret to use for getting the token
            token_type: Type of token (for caching purposes)
        
        Returns:
            The access token as a string
        """
        # Check if we have a cached token
        cache_key = f"{self.corp_id}:{secret}:{token_type}"
        if cache_key in self.token_cache:
            return self.token_cache[cache_key]
        
        # Request a new access token
        params = {
            'corpid': self.corp_id,
            'corpsecret': secret
        }
        
        try:
            response = requests.get(self.token_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'errcode' in data and data['errcode'] != 0:
                raise Exception(f"Error getting {token_type} access token: {data.get('errmsg', 'Unknown error')}")
            
            access_token = data['access_token']
            
            # Cache the token
            self.token_cache[cache_key] = access_token
            
            self.logger.info(f"Successfully obtained new {token_type} access token")
            return access_token
            
        except requests.RequestException as e:
            raise Exception(f"Network error while getting {token_type} access token: {str(e)}")
        except KeyError:
            raise Exception("Invalid response format from WeChat Work API")