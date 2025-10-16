"""
User module for WeChat Work API SDK.
Contains user management functionality.
"""

import json
import logging
from typing import Dict, Any, Optional
import requests
from .common import AccessTokenManager


class UserManager:
    """
    Manages user operations for WeChat Work API.
    """
    
    def __init__(self, base_url: str, access_token_manager: AccessTokenManager):
        """
        Initialize the user manager.
        
        Args:
            base_url: Base URL for WeChat Work API
            access_token_manager: Instance of AccessTokenManager
        """
        self.base_url = base_url.rstrip('/')
        self.access_token_manager = access_token_manager
        self.api_base = f"{self.base_url}/cgi-bin"
        
        self.logger = logging.getLogger(__name__)
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information by user ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User information as a dictionary
        """
        endpoint = "/user/get"
        params = {
            'access_token': self.access_token_manager.get_app_access_token(),
            'userid': user_id
        }
        
        try:
            response = requests.get(f"{self.api_base}{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'errcode' in result and result['errcode'] != 0:
                raise Exception(f"WeChat Work API error {result['errcode']}: {result.get('errmsg', 'Unknown error')}")
            
            return result
            
        except requests.RequestException as e:
            raise Exception(f"Network error while getting user: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from WeChat Work API")
    
    def update_user(self, 
                   userid: str,  # Required
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
        endpoint = "/user/update"
        
        user_data = {'userid': userid}
        
        if name is not None:
            user_data['name'] = name
        if alias is not None:
            user_data['alias'] = alias
        if mobile is not None:
            user_data['mobile'] = mobile
        if department is not None:
            user_data['department'] = department
        if order is not None:
            user_data['order'] = order
        if position is not None:
            user_data['position'] = position
        if gender is not None:
            user_data['gender'] = gender
        if email is not None:
            user_data['email'] = email
        if biz_mail is not None:
            user_data['biz_mail'] = biz_mail
        if biz_mail_alias is not None:
            user_data['biz_mail_alias'] = biz_mail_alias
        if telephone is not None:
            user_data['telephone'] = telephone
        if is_leader_in_dept is not None:
            user_data['is_leader_in_dept'] = is_leader_in_dept
        if direct_leader is not None:
            user_data['direct_leader'] = direct_leader
        if avatar_mediaid is not None:
            user_data['avatar_mediaid'] = avatar_mediaid
        if enable is not None:
            user_data['enable'] = enable
        if extattr is not None:
            user_data['extattr'] = extattr
        if external_profile is not None:
            user_data['external_profile'] = external_profile
        if external_position is not None:
            user_data['external_position'] = external_position
        if nickname is not None:
            user_data['nickname'] = nickname
        if address is not None:
            user_data['address'] = address
        if main_department is not None:
            user_data['main_department'] = main_department
        
        try:
            params = {'access_token': self.access_token_manager.get_contacts_sync_access_token()}
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(f"{self.api_base}{endpoint}", params=params, json=user_data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'errcode' in result and result['errcode'] != 0:
                raise Exception(f"WeChat Work API error {result['errcode']}: {result.get('errmsg', 'Unknown error')}")
            
            return result
            
        except requests.RequestException as e:
            raise Exception(f"Network error while updating user: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from WeChat Work API")
    
    def mobile_to_userid(self, mobile: str) -> Dict[str, Any]:
        """
        Convert mobile number to user ID.
        
        Args:
            mobile: The mobile number
            
        Returns:
            API response containing user ID as a dictionary
        """
        endpoint = "/user/getuserid"
        data = {'mobile': mobile}
        
        try:
            params = {'access_token': self.access_token_manager.get_app_access_token()}
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(f"{self.api_base}{endpoint}", params=params, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'errcode' in result and result['errcode'] != 0:
                raise Exception(f"WeChat Work API error {result['errcode']}: {result.get('errmsg', 'Unknown error')}")
            
            return result
            
        except requests.RequestException as e:
            raise Exception(f"Network error while getting userid: {str(e)}")
        except ValueError:
            raise Exception("Invalid JSON response from WeChat Work API")