"""
WeChat Work API Client
Implements the core functionality for interacting with WeChat Work API.
This is the main entry point that uses the modular architecture.
"""

import logging
from typing import Dict, Any, Optional
from .config import Config
from .common import AccessTokenManager
from .user import UserManager


class WeChatWorkException(Exception):
    """Base exception for WeChat Work API errors."""
    pass


class WeChatWorkClient:
    """
    WeChat Work API Client
    Provides methods to interact with the WeChat Work API using a modular architecture.
    """
    
    def __init__(self, 
                 config: Optional[Config] = None,
                 config_file: Optional[str] = None,
                 token_cache_size: int = 100,
                 token_cache_ttl: int = 7000):  # Token expires in 7200 seconds, so cache for 7000
        """
        Initialize the WeChat Work client.
        
        Args:
            config: Config object with API settings (optional)
            config_file: Path to .env file (optional)
            token_cache_size: Size of the token cache
            token_cache_ttl: Time-to-live for cached tokens in seconds
        """
        # Initialize configuration
        if config:
            self.config = config
        else:
            self.config = Config(config_file)
        
        # Initialize the access token manager
        self.token_manager = AccessTokenManager(
            base_url=self.config.base_url,
            corp_id=self.config.corp_id,
            app_secret=self.config.app_secret,
            contacts_sync_secret=self.config.contacts_sync_secret,
            token_cache_size=token_cache_size,
            token_cache_ttl=token_cache_ttl
        )
        
        # Initialize user manager
        self.user_manager = UserManager(
            base_url=self.config.base_url,
            access_token_manager=self.token_manager
        )
        
        self.logger = logging.getLogger(__name__)
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information by user ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User information as a dictionary
        """
        return self.user_manager.get_user(user_id)
    
    def update_user(self, 
                   userid: str,  # Required parameter
                   name: Optional[str] = None, 
                   alias: Optional[str] = None,
                   mobile: Optional[str] = None,
                   department: Optional[list] = None,
                   order: Optional[list] = None,
                   position: Optional[str] = None,
                   gender: Optional[str] = None,
                   email: Optional[str] = None,
                   biz_mail: Optional[str] = None,
                   biz_mail_alias: Optional[Dict[str, Any]] = None,
                   telephone: Optional[str] = None,
                   is_leader_in_dept: Optional[list] = None,
                   direct_leader: Optional[list] = None,
                   avatar_mediaid: Optional[str] = None,
                   enable: Optional[int] = None,
                   extattr: Optional[Dict[str, Any]] = None,
                   external_profile: Optional[Dict[str, Any]] = None,
                   external_position: Optional[str] = None,
                   nickname: Optional[str] = None,
                   address: Optional[str] = None,
                   main_department: Optional[int] = None) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            userid: Required. User ID. Corresponds to the account in the management console, must be unique within the enterprise. Case-insensitive, 1-64 bytes long
            name: Optional. Member name, 1-64 UTF8 characters
            alias: Optional. Alias, 1-64 UTF8 characters
            mobile: Optional. Mobile number. Must be unique within the enterprise
            department: Optional. List of department IDs the member belongs to, up to 100
            order: Optional. Sorting value within the department, defaults to 0. Effective when department is provided. Number must match department, larger number means higher priority. Valid range is [0, 2^32)
            position: Optional. Position information, 0-128 UTF8 characters
            gender: Optional. Gender. 1 for male, 2 for female
            email: Optional. Email address. 6-64 bytes and valid email format, must be unique within enterprise
            biz_mail: Optional. If the enterprise has activated Tencent Corporate Mail (Enterprise WeChat Mail), setting this creates a corporate email account. 6-63 bytes and valid corporate email format, must be unique within enterprise
            biz_mail_alias: Optional. Corporate email alias. 6-63 bytes and valid corporate email format, must be unique within enterprise, up to 5 aliases can be set. Updates are overwritten. Passing empty structure or empty array clears current corporate email aliases
            telephone: Optional. Landline. Composed of 1-32 digits, "-", "+", or "," 
            is_leader_in_dept: Optional. Department head field, count must match department, indicates whether the member is a head in the department. 0-False, 1-True
            direct_leader: Optional. Direct supervisor, can set members within the enterprise as direct supervisor, max 1 can be set
            avatar_mediaid: Optional. Member's avatar mediaid, obtained through media management API upload
            enable: Optional. Enable/disable member. 1 for enabled, 0 for disabled
            extattr: Optional. Extended attributes. Fields need to be added in WEB management first
            external_profile: Optional. Member's external attributes
            external_position: Optional. External position. If set, used as the displayed position, otherwise use position. Up to 12 Chinese characters
            nickname: Optional. Video account name (after setting, the member will display this video account externally). Must be selected from the video account bound to the enterprise WeChat, accessible in the "My Enterprise" page
            address: Optional. Address. Max 128 characters
            main_department: Optional. Main department
            
        Returns:
            API response as a dictionary
        """
        return self.user_manager.update_user(
            userid=userid,
            name=name,
            alias=alias,
            mobile=mobile,
            department=department,
            order=order,
            position=position,
            gender=gender,
            email=email,
            biz_mail=biz_mail,
            biz_mail_alias=biz_mail_alias,
            telephone=telephone,
            is_leader_in_dept=is_leader_in_dept,
            direct_leader=direct_leader,
            avatar_mediaid=avatar_mediaid,
            enable=enable,
            extattr=extattr,
            external_profile=external_profile,
            external_position=external_position,
            nickname=nickname,
            address=address,
            main_department=main_department
        )
    
    def mobile_to_userid(self, mobile: str) -> Dict[str, Any]:
        """
        Convert mobile number to user ID.
        
        Args:
            mobile: The mobile number
            
        Returns:
            API response containing user ID as a dictionary
        """
        return self.user_manager.mobile_to_userid(mobile)