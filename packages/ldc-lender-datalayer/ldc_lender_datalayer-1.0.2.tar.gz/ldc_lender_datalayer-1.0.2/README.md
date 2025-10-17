# Lender Data Layer

A comprehensive data access layer for Django applications providing database operations, Redis caching, and various data mappers.

## Features

- **Data Mappers**: IMS and iOS specific data mappers with internal functions
- **Redis Integration**: Caching layer with Redis support
- **Exception Handling**: Custom exception classes for error handling
- **Utilities**: Common utilities for data processing

## Installation

```bash
pip install lender-datalayer
```

## Quick Start

### Using Data Mappers (Recommended)

```python
# Import specific mappers
from lender_datalayer.ims_mappers import account_mapper, investor_mapper
from lender_datalayer.ios_mappers import user_mapper, bank_mapper

# Use mapper functions directly
user_data = user_mapper.get_user_by_id(user_id=123)
account_info = account_mapper.get_account_details(account_id=456)
```

### Using Redis Operations

```python
from lender_datalayer import RedisDataLayer

# Initialize Redis layer
redis = RedisDataLayer()

# Store data in cache
redis.store_data_in_redis_cache("user:123", {"name": "John", "email": "john@example.com"})

# Retrieve data from cache
user_data = redis.get_data_from_redis_cache("user:123")

# Delete data from cache
redis.delete_data_from_redis_cache("user:123")
```

## Requirements

- Python 3.8+
- Django 5.2+
- Redis 5.0+
- PostgreSQL (with psycopg)

## Usage Guidelines

### ✅ What End Users Should Use

#### **1. Mapper Functions (Primary Usage)**
```python
# IMS Mappers
from lender_datalayer.ims_mappers import account_mapper, investor_mapper, cp_mapper

# Use internal functions of mappers
user_data = investor_mapper.get_investor_details(investor_id=123)
account_list = account_mapper.get_user_accounts(user_id=456)
cp_data = cp_mapper.get_cp_dashboard_data(cp_id=789)
```

#### **2. iOS Mappers**
```python
from lender_datalayer.ios_mappers import user_mapper, bank_mapper, document_mapper

# Use internal functions of mappers
user_profile = user_mapper.get_user_profile(user_id=123)
bank_accounts = bank_mapper.get_user_bank_accounts(user_id=456)
documents = document_mapper.get_user_documents(user_id=789)
```

#### **3. Redis Operations**
```python
from lender_datalayer import RedisDataLayer

redis = RedisDataLayer()

# Cache operations
redis.store_data_in_redis_cache("key", data, ttl=3600)
cached_data = redis.get_data_from_redis_cache("key")
redis.delete_data_from_redis_cache("key")
```

### ❌ What End Users Should NOT Use

#### **Base Classes (Internal Use Only)**
```python
# DON'T use these directly - they are for internal mapper implementation
from lender_datalayer import BaseDataLayer  # ❌ Not for end users
from lender_datalayer import DataLayerUtils  # ❌ Not for end users
```

#### **Custom Exception Classes (Internal Use Only)**
```python
# DON'T import these directly - they are used internally by mappers
from lender_datalayer import ConnectionError  # ❌ Not for end users
from lender_datalayer import QueryError  # ❌ Not for end users
```

## Available Mappers

### IMS Mappers
- `account_mapper` - Account management functions
- `investor_mapper` - Investor data functions
- `cp_mapper` - Credit Partner functions
- `bank_mapper` - Banking functions
- `document_mapper` - Document handling functions
- `partner_mapper` - Partner management functions
- `thirdparty_mapper` - Third-party integration functions

### iOS Mappers
- `user_mapper` - User management functions
- `bank_mapper` - Banking functions
- `document_mapper` - Document handling functions
- `dashboard_mapper` - Dashboard data functions
- `bureau_mapper` - Credit bureau functions
- `kmi_mapper` - KYC functions
- `thirdparty_mapper` - Third-party integration functions

## Development

```bash
# Install in development mode
pip install -e .[dev]

# Format code
black lender_datalayer/

# Type checking
mypy lender_datalayer/
```

## License

This package is for personal use only.
