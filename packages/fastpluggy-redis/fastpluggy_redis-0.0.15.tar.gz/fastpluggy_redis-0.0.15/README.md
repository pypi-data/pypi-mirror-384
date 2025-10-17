# Redis Tools for FastPluggy

![Redis Tools](https://img.shields.io/badge/FastPluggy-Redis%20Tools-red)
![Version](https://img.shields.io/badge/version-0.0.7-blue)

A powerful Redis browser and management plugin for FastPluggy applications. 
This plugin provides a user-friendly interface to browse, search, and manage Redis databases and keys.

## Features

- **Redis Browser UI**: Intuitive web interface to browse and manage Redis data
- **Multi-Database Support**: Switch between Redis databases easily
- **Key Management**: View, search, and delete Redis keys
- **Data Type Support**: Full support for all Redis data types (string, list, hash, set, zset)
- **Pickled Data Handling**: Automatic detection and unpickling of Python pickled data
- **TTL Management**: View time-to-live for keys
- **Database Flushing**: Clear entire databases with confirmation
- **Scheduled Cleanup**: Optional scheduled task to clean expired keys (requires tasks_worker plugin)

## Installation

1. Install the official plugin package:

```bash
pip install fastpluggy-plugins
```
or
```bash
pip install fastpluggy-plugin-redis
```

2. Add the plugin to your FastPluggy application:

There are several ways to add the plugin to your FastPluggy application:

#### Method 1: Using the Admin Interface

1. Navigate to `/admin/plugins` in your FastPluggy application
2. Click on "Install New Plugin"
3. Enter "redis_tools" as the plugin name
4. Click "Install"

#### Method 2: Using the Configuration File

Add the plugin to your FastPluggy configuration file:

```python
# config.py
FASTPLUGGY_PLUGINS = [
    # other plugins...
    "redis_tools",
]
```

#### Method 3: Programmatically

Add the plugin programmatically in your application code:

```python
from fastapi import FastAPI
from fastpluggy import FastPluggy

app = FastAPI()
pluggy = FastPluggy(app)

# Add the Redis Tools plugin
pluggy.add_plugin("redis_tools")
```

For more detailed installation and configuration instructions, see the [Installation Guide](docs/installation.md).

## Configuration

Configure Redis Tools through environment variables or directly in your FastPluggy configuration:

| Setting | Description | Default |
|---------|-------------|---------|
| `REDIS_DSN` | Redis connection string (overrides other connection settings if provided) | `None` |
| `redis_host` | Redis server hostname | `localhost` |
| `redis_port` | Redis server port | `6379` |
| `redis_db` | Default Redis database index | `0` |
| `use_ssl` | Whether to use SSL for Redis connection | `False` |
| `redis_password` | Redis server password | `None` |
| `redis_decode_responses` | Whether to decode Redis responses | `False` |
| `keys_limit` | Maximum number of keys to display | `100` |


## Usage

### Web Interface

Once installed, access the Redis browser at `/redis_tools/` in your FastPluggy application. The interface allows you to:

1. Select and switch between Redis databases
2. Search for keys using patterns (e.g., `user:*`)
3. View key details including type, TTL, and size
4. Examine and format key values based on their data type
5. Delete individual keys
6. Flush entire databases

### Programmatic Usage

You can also use the Redis Tools connector in your code:

```python
from redis_tools.redis_connector import RedisConnection

# Create a connection
redis_conn = RedisConnection()

# Test connection
if redis_conn.test_connection():
    # Get all keys matching a pattern
    keys = redis_conn.get_keys("user:*")

    # Get details for a specific key
    key_details = redis_conn.get_key_details("user:1001")

    # Switch to another database
    redis_conn.select_db(2)

    # Delete a key
    redis_conn.delete_key("temporary_key")
```

## Development

### Requirements

- Python 3.10+
- FastPluggy
- Redis

### Testing

Run tests with pytest:

```bash
cd redis_tools
pip install -r tests/requirements.txt
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
