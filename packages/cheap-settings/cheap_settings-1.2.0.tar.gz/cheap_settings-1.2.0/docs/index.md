# Cheap Settings

_A lightweight, low footprint settings system_

[![PyPI version](https://img.shields.io/pypi/v/cheap-settings.svg)](https://pypi.org/project/cheap-settings/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/cheap-settings.svg)](https://pypi.org/project/cheap-settings/)
[![Downloads](https://pepy.tech/badge/cheap-settings)](https://pepy.tech/project/cheap-settings)

`cheap-settings` is a Python package for providing a very simple, very low impact, configuration. The Python configuration & settings landscape is virtually overflowing with clever, advanced, flexible solutions that cover many needs. However, what _I_ needed was a bit different from any config/settings package that I was aware of.

The main thing that distinguishes `cheap_settings` from any alternative solutions is simplicity: it is _extremely_ simple (& ergonomic) to use, & it intentionally limits its scope & feature set to be simple to understand.

Additionally, it supports circumstances where it is difficult to bring your config file with you. All of your config is defined in the code or in the environment.

## Quick Start

```python
from cheap_settings import CheapSettings

class MySettings(CheapSettings):
    host: str = "localhost"
    port: int = 8080
    debug: bool = False

# Access settings
print(f"Server: {MySettings.host}:{MySettings.port}")

# Override with environment variables
# HOST=production.com PORT=443 DEBUG=true python myapp.py
```

Environment variables automatically override defaults with proper type conversion.

## Installation

```shell
pip install cheap-settings
```

## Features

- **Simple**: Just inherit from `CheapSettings` and define typed attributes
- **Environment variables**: Automatic override with type conversion
- **Command line**: Optional CLI argument parsing
- **Type safe**: Full type hints and IDE support
- **Inheritance**: Settings classes can inherit from each other
- **Pickleable**: Works with Ray and other frameworks requiring serialization
- **Zero dependencies**: No external requirements
- **Performance**: Optional static snapshots for speed-critical code

## Why Cheap Settings?

You want to configure something. You don't want to spend time configuring the configuration system. You just want it to work with minimal ceremony.

That's exactly what `cheap-settings` provides.
