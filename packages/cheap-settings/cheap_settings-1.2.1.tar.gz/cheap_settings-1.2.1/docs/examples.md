# Examples

The best way to understand `cheap-settings` is through examples. All examples are runnable - you can copy and paste them into Python files.

## Basic Usage

The simplest way to use cheap-settings:

```python
from cheap_settings import CheapSettings

class AppSettings(CheapSettings):
    """Application configuration."""
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    app_name: str = "MyApp"

# Access settings directly as class attributes
print(f"Host: {AppSettings.host}")
print(f"Port: {AppSettings.port}")
print(f"Server: http://{AppSettings.host}:{AppSettings.port}")
```

## Environment Variables

Environment variables automatically override defaults with type conversion:

```python
import os
from cheap_settings import CheapSettings

class Settings(CheapSettings):
    database_host: str = "localhost"
    database_port: int = 5432
    connection_timeout: float = 30.0
    use_ssl: bool = False

# Set environment variables
os.environ["DATABASE_HOST"] = "prod.example.com"
os.environ["DATABASE_PORT"] = "3306"  # Converted to int
os.environ["USE_SSL"] = "true"        # Converted to bool

print(f"Database: {Settings.database_host}:{Settings.database_port}")
print(f"SSL: {Settings.use_ssl} ({type(Settings.use_ssl).__name__})")
```

## Command Line Arguments

Automatically create CLI arguments from your settings:

```python
from cheap_settings import CheapSettings

class ServerConfig(CheapSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False

# Parse command line arguments
ServerConfig.set_config_from_command_line()

print(f"Server: {ServerConfig.host}:{ServerConfig.port}")
print(f"Workers: {ServerConfig.workers}")
```

Run with: `python server.py --host localhost --port 3000 --workers 8 --reload`

## Inheritance

Settings classes can inherit from each other:

```python
from cheap_settings import CheapSettings

class BaseConfig(CheapSettings):
    app_name: str = "MyApplication"
    version: str = "1.0.0"
    timeout: int = 30

class DatabaseConfig(BaseConfig):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "myapp"

class ProductionConfig(DatabaseConfig):
    debug: bool = False
    db_host: str = "prod.db.example.com"  # Override parent
    ssl_required: bool = True

print(f"App: {ProductionConfig.app_name} v{ProductionConfig.version}")
print(f"Database: {ProductionConfig.db_host}:{ProductionConfig.db_port}")
```

## Type Conversion

All basic Python types are supported, with or without type annotations:

```python
from pathlib import Path
from typing import Optional
from cheap_settings import CheapSettings

class TypedSettings(CheapSettings):
    # Explicit type annotations
    text: str = "default"
    number: int = 42
    ratio: float = 3.14
    enabled: bool = False

    # Type inference from defaults (no annotations needed!)
    host = "localhost"  # Infers str
    port = 8080  # Infers int
    timeout = 30.5  # Infers float
    debug = False  # Infers bool

    # Path support
    config_dir: Path = Path("/etc/myapp")
    # Or inferred:
    log_dir = Path("/var/log")  # Infers Path

    # JSON types
    tags: list = ["python", "config"]
    metadata: dict = {"version": 1}

    # Optional types (need explicit annotation)
    api_key: Optional[str] = None

# Environment variables are converted automatically:
# TEXT="hello" NUMBER="99" ENABLED="true" CONFIG_DIR="/custom/path"
# TAGS='["web", "api"]' METADATA='{"env": "prod"}' API_KEY="secret"
```

## Static Snapshots

For performance-critical code, create static snapshots:

```python
from cheap_settings import CheapSettings

class DynamicSettings(CheapSettings):
    api_url: str = "https://api.example.com"
    timeout: int = 30
    retry_count: int = 3

# Create a static snapshot (frozen values)
StaticSettings = DynamicSettings.to_static()

# Static class has no dynamic behavior - just fast attribute access
print(f"API: {StaticSettings.api_url}")
print(f"Type: {type(StaticSettings)}")  # Regular Python class
```

## Pickle Support

Works with Ray and other frameworks requiring serialization:

```python
import pickle
from cheap_settings import CheapSettings

class Config(CheapSettings):
    host: str = "localhost"
    port: int = 8080

# Pickle and unpickle
pickled = pickle.dumps(Config)
unpickled_class = pickle.loads(pickled)

assert unpickled_class.host == Config.host
print("✓ Pickle support works!")
```

## More Examples

For complete runnable examples, see the [examples directory](https://github.com/evanjpw/cheap-settings/tree/main/examples) in the repository.
