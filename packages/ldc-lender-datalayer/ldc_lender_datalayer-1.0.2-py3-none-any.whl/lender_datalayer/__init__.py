"""
Lender Data Layer - A comprehensive data access layer for Django applications.

This package provides database operations, Redis caching, and various data mappers
for Django applications.
"""

from .base_datalayer import BaseDataLayer, DataLayerUtils
from .redis_datalayer import RedisDataLayer
from .custom_exception_handlers import (
    DataLayerError,
    ConnectionError,
    QueryError,
    ValidationError,
    TransactionError
)

__version__ = "1.0.2"
__author__ = "Sandesh Kanagal"
__email__ = "sandesh.kanagal@lendenclub.com"

__all__ = [
    "BaseDataLayer",
    "DataLayerUtils", 
    "RedisDataLayer",
    "DataLayerError",
    "ConnectionError",
    "QueryError",
    "ValidationError",
    "TransactionError"
]
