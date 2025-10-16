# WeChat Work API SDK

A Python SDK for interacting with the WeChat Work API. This library provides a simple and efficient way to integrate your Python applications with WeChat Work, supporting key features like user management, authentication, and more. The SDK features a clean modular architecture with static imports.

## Features

- **Static Modular Architecture**: Separate modules for configuration, common functions (access_token), and user management
- **Environment Configuration**: Support for .env files and environment variables with python-dotenv
- **Easy Access Token Management**: Automatic retrieval and caching of access tokens with TTL (Time To Live) support
- **User Management**: Get user information, update user profiles, and convert mobile numbers to user IDs
- **Comprehensive Error Handling**: Proper exception handling for API errors
- **Type Hints**: Full type annotation support for better IDE experience
- **Thread-Safe**: Safe for concurrent usage in multi-threaded applications
- **Caching**: Uses `cachetools` for efficient token caching

## Installation

Install the package using pip:

```bash
pip install weixin-work-reborn
```

## Quick Start

```python
from weixin_work_reborn import WeChatWorkClient, Config

# Initialize the client with configuration
config = Config()  # Loads from .env file or environment variables
client = WeChatWorkClient(config=config)

# Get user information
user_info = client.get_user("user_id_here")
print(user_info)

# Update user information
result = client.update_user(
    user_id="user_id_here",
    name="New Name",
    mobile="13800138000",
    email="newemail@example.com"
)
print(result)

# Convert mobile to user ID
userid_result = client.mobile_to_userid("13800138000")
print(userid_result)
```

## Configuration

### Using .env File (Recommended)

Create a `.env` file in your project root:

```bash
WEIXIN_WORK_BASE_URL=https://qyapi.weixin.qq.com/
WEIXIN_WORK_CORP_ID=your_corp_id_here
WEIXIN_WORK_APP_SECRET=your_app_secret_here
WEIXIN_WORK_CONTACTS_SYNC_SECRET=your_contacts_sync_secret_here
WEIXIN_WORK_AGENT_ID=your_agent_id_here
```

**Note:** WeChat Work API requires different secrets for different API endpoints:
- `WEIXIN_WORK_APP_SECRET` is used for general API operations (e.g., getting user information, mobile to userid conversion)
- `WEIXIN_WORK_CONTACTS_SYNC_SECRET` is specifically required for user management operations (e.g., update_user)

Then in your code:

```python
from weixin_work_reborn import WeChatWorkClient, Config

config = Config()  # Automatically loads from .env file
client = WeChatWorkClient(config=config)
```

### Environment Variables

Alternatively, you can set environment variables:

```bash
export WEIXIN_WORK_BASE_URL="https://qyapi.weixin.qq.com/"
export WEIXIN_WORK_CORP_ID="your_corp_id_here"
export WEIXIN_WORK_APP_SECRET="your_app_secret_here"
export WEIXIN_WORK_CONTACTS_SYNC_SECRET="your_contacts_sync_secret_here"
export WEIXIN_WORK_AGENT_ID="your_agent_id_here"
```

**Note:** WeChat Work API requires different secrets for different API endpoints:
- `WEIXIN_WORK_APP_SECRET` is used for general API operations (e.g., getting user information, mobile to userid conversion)
- `WEIXIN_WORK_CONTACTS_SYNC_SECRET` is specifically required for user management operations (e.g., update_user)

## API Reference

### Config

Handles configuration loading from environment variables and .env files.

#### Constructor

```python
Config(env_file=None)
```

- `env_file` (str, optional): Path to a specific .env file to load

#### Properties

- `base_url` (str): The base URL for WeChat Work API (default: "https://qyapi.weixin.qq.com/")
- `corp_id` (str): Your WeChat Work corporate ID
- `corp_secret` (str): Your application secret
- `agent_id` (str): Your application agent ID

### WeChatWorkClient

The main client class for interacting with the WeChat Work API.

#### Constructor

```python
WeChatWorkClient(config=None, config_file=None, token_cache_size=100, token_cache_ttl=7000)
```

- `config` (Config, optional): Config object with API settings
- `config_file` (str, optional): Path to .env file
- `token_cache_size` (int): Size of the token cache (default: 100)
- `token_cache_ttl` (int): Time-to-live for cached tokens in seconds (default: 7000, just under the 7200s token expiry)

#### Methods

##### get_user(user_id)

Get user information by user ID.

- `user_id` (str): The user ID to retrieve information for
- Returns: User information as a dictionary

##### update_user(userid, **kwargs)

Update user information.

- `userid` (str): Required. User ID. Corresponds to the account in the management console, must be unique within the enterprise. Case-insensitive, 1-64 bytes long
- `name` (str, optional): Member name, 1-64 UTF8 characters
- `alias` (str, optional): Alias, 1-64 UTF8 characters
- `mobile` (str, optional): Mobile number. Must be unique within the enterprise
- `department` (list, optional): List of department IDs the member belongs to, up to 100
- `order` (list, optional): Sorting value within the department, defaults to 0. Effective when department is provided. Number must match department, larger number means higher priority. Valid range is [0, 2^32)
- `position` (str, optional): Position information, 0-128 UTF8 characters
- `gender` (str, optional): Gender. 1 for male, 2 for female
- `email` (str, optional): Email address. 6-64 bytes and valid email format, must be unique within enterprise
- `biz_mail` (str, optional): If the enterprise has activated Tencent Corporate Mail (Enterprise WeChat Mail), setting this creates a corporate email account. 6-63 bytes and valid corporate email format, must be unique within enterprise
- `biz_mail_alias` (dict, optional): Corporate email alias. 6-63 bytes and valid corporate email format, must be unique within enterprise, up to 5 aliases can be set. Updates are overwritten. Passing empty structure or empty array clears current corporate email aliases
- `telephone` (str, optional): Landline. Composed of 1-32 digits, "-", "+", or "," 
- `is_leader_in_dept` (list, optional): Department head field, count must match department, indicates whether the member is a head in the department. 0-False, 1-True
- `direct_leader` (list, optional): Direct supervisor, can set members within the enterprise as direct supervisor, max 1 can be set
- `avatar_mediaid` (str, optional): Member's avatar mediaid, obtained through media management API upload
- `enable` (int, optional): Enable/disable member. 1 for enabled, 0 for disabled
- `extattr` (dict, optional): Extended attributes. Fields need to be added in WEB management first
- `external_profile` (dict, optional): Member's external attributes
- `external_position` (str, optional): External position. If set, used as the displayed position, otherwise use position. Up to 12 Chinese characters
- `nickname` (str, optional): Video account name (after setting, the member will display this video account externally). Must be selected from the video account bound to the enterprise WeChat, accessible in the "My Enterprise" page
- `address` (str, optional): Address. Max 128 characters
- `main_department` (int, optional): Main department
- Returns: API response as a dictionary

##### mobile_to_userid(mobile)

Convert mobile number to user ID.

- `mobile` (str): The mobile number to convert
- Returns: API response containing user ID as a dictionary

## Examples

More examples can be found in the `examples/` directory:

- `basic_usage.py`: Basic usage examples
- `advanced_usage.py`: Advanced usage with environment variables
- `modular_demo.py`: Demonstration of the static modular architecture

## Development

### Setup

1. Clone the repository
2. Install dependencies with `uv` (or `pip`):
   ```bash
   # Using uv (recommended)
   uv venv
   uv pip install -e ".[dev]"
   ```

### Running Tests

```bash
python -m pytest tests/
```

### Code Formatting

```bash
black .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please file a bug report on the [GitHub issues page](https://github.com/liudonghua123/weixin-work/issues).

## About WeChat Work API

For more information about the WeChat Work API, visit the [official documentation](https://developer.work.weixin.qq.com/document/path/90197).