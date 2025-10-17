import time

from django.db.utils import DatabaseError, IntegrityError, OperationalError


class DataLayerError(Exception):
    """Base exception class for all data layer errors."""

    def __init__(self, message, error_code=None, db_alias=None):
        super().__init__(message)
        self.error_code = error_code
        self.db_alias = db_alias
        self.timestamp = time.time()


class ConnectionError(DataLayerError):
    """Raised when database connection fails."""

    def __init__(self, message, db_alias=None):
        super().__init__(message, error_code="DB_CONNECTION_ERROR", db_alias=db_alias)


class QueryError(DataLayerError):
    """Raised when query execution fails."""

    def __init__(self, message, sql=None, db_alias=None):
        super().__init__(message, error_code="DB_QUERY_ERROR", db_alias=db_alias)
        self.sql = sql


class ValidationError(DataLayerError):
    """Raised when data validation fails."""

    def __init__(self, message, field_name=None, invalid_value=None):
        super().__init__(message, error_code="DB_VALIDATION_ERROR")
        self.field_name = field_name
        self.invalid_value = invalid_value


class TransactionError(DataLayerError):
    """Raised when transaction operations fail."""

    def __init__(self, message, db_alias=None, operation_count=None):
        super().__init__(message, error_code="DB_TRANSACTION_ERROR", db_alias=db_alias)
        self.operation_count = operation_count
