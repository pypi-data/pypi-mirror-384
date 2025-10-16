"""
Tests for the WeChat Work API client.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from weixin_work_reborn.client import WeChatWorkClient, WeChatWorkException
from weixin_work_reborn.config import Config


class TestWeChatWorkClient(unittest.TestCase):
    """Test cases for the WeChat Work client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.corp_id = "test_corp_id"
        self.secret = "test_secret"
        self.base_url = "https://qyapi.weixin.qq.com/"
        
        # Create a mock config
        self.config = MagicMock(spec=Config)
        self.config.base_url = self.base_url
        self.config.corp_id = self.corp_id
        self.config.corp_secret = self.secret
        self.config.agent_id = "test_agent_id"
        
        self.client = WeChatWorkClient(config=self.config)
    
    @patch('weixin_work_reborn.common.AccessTokenManager.get_access_token')
    def test_get_user_success(self, mock_get_token):
        """Test successful user retrieval."""
        # Mock the access token
        mock_get_token.return_value = 'test_access_token'
        
        # Mock the API response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'errcode': 0,
                'errmsg': 'ok',
                'userid': 'test_user',
                'name': 'Test User'
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = self.client.get_user('test_user')
            
            self.assertEqual(result['userid'], 'test_user')
            self.assertEqual(result['name'], 'Test User')
            mock_get.assert_called_once()
    
    @patch('weixin_work_reborn.common.AccessTokenManager.get_access_token')
    def test_update_user_success(self, mock_get_token):
        """Test successful user update."""
        # Mock the access token
        mock_get_token.return_value = 'test_access_token'
        
        # Mock the API response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                'errcode': 0,
                'errmsg': 'updated'
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = self.client.update_user(userid='test_user', name='New Name', mobile='13800138000', biz_mail_alias={'item': ['test@example.com']})
            
            self.assertEqual(result['errcode'], 0)
            mock_post.assert_called_once()
    
    @patch('weixin_work_reborn.common.AccessTokenManager.get_access_token')
    def test_mobile_to_userid_success(self, mock_get_token):
        """Test successful mobile to userid conversion."""
        # Mock the access token
        mock_get_token.return_value = 'test_access_token'
        
        # Mock the API response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                'errcode': 0,
                'errmsg': 'ok',
                'userid': 'test_userid'
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = self.client.mobile_to_userid('13800138000')
            
            self.assertEqual(result['userid'], 'test_userid')
            mock_post.assert_called_once()

    def test_client_initialization_with_config(self):
        """Test client initialization with config object."""
        client = WeChatWorkClient(config=self.config)
        
        self.assertIsNotNone(client.config)
        self.assertIsNotNone(client.token_manager)
        self.assertIsNotNone(client.user_manager)


if __name__ == '__main__':
    unittest.main()