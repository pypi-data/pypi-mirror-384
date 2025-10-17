"""
Base Data Layer for handling all database operations with connection management.
This class provides a centralized way to handle database operations with proper error handling
and connection management.
"""

import ast
import logging
from abc import ABC, abstractmethod

from django.db import connections

from .custom_exception_handlers import ConnectionError, QueryError

logger = logging.getLogger('normal')


class BaseDataLayer(ABC):

    def __init__(self, db_alias="default"):
        self.db_alias = db_alias
        if db_alias not in connections.databases:
            raise ConnectionError(
                f"Database alias '{db_alias}' not found in settings", db_alias=db_alias
            )

    def execute_sql(self, sql, params, return_rows_count=False):
        """
        Execute SQL query with optional row count return.

        Args:
            sql: SQL query string
            params: Query parameters
            return_rows_count: Whether to return affected row count

        Returns:
            Row count if return_rows_count is True, otherwise None
        """
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.rowcount if return_rows_count else None
        except Exception as e:
            logger.error(
                f"Failed to execute SQL on database alias '{self.db_alias}': {str(e)}"
            )
            raise QueryError(
                f"Failed to execute SQL: {str(e)}", sql=sql, db_alias=self.db_alias
            ) from e

    def sql_execute_fetch_one(self, sql, params, index_result=False, to_dict=False):
        """
        Execute query and fetch one result.
        Consolidated function that merges sql_execute_fetch_one and sql_execute_fetch_one_v2.

        Args:
            sql: SQL query string
            params: Query parameters
            index_result: Whether to return first column only
            to_dict: Whether to return as dictionary

        Returns:
            Single row result or dictionary
        """
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()

                if result and index_result:
                    return result[0]
                elif result and to_dict:
                    return self._row_to_dict(cursor, result)
                return result
        except Exception as e:
            logger.error(
                f"Failed to execute fetch one query on database alias '{self.db_alias}': {str(e)}"
            )
            raise QueryError(
                f"Failed to execute fetch one query: {str(e)}",
                sql=sql,
                db_alias=self.db_alias,
            ) from e

    def sql_execute_fetch_all(
        self, sql, params, to_dict=False, fetch_single_column=False
    ):
        """
        Execute query and fetch all results.

        Args:
            sql: SQL query string
            params: Query parameters
            to_dict: Whether to return as list of dictionaries
            fetch_single_column: Whether to fetch only the first column of each row

        Returns:
            List of rows or list of single column values
        """
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.execute(sql, params)

                if fetch_single_column:
                    return [row[0] for row in cursor.fetchall()]
                elif to_dict:
                    return self._rows_to_dict(cursor)
                return cursor.fetchall()
        except Exception as e:
            logger.error(
                f"Failed to execute fetch all query on database alias '{self.db_alias}': {str(e)}"
            )
            raise QueryError(
                f"Failed to execute fetch all query: {str(e)}",
                sql=sql,
                db_alias=self.db_alias,
            ) from e

    def sql_execute_bulk_update(self, sql, values):
        """
        Execute bulk update operation.

        Args:
            sql: SQL query string
            values: List of parameter sets for bulk operation

        Returns:
            Number of affected rows
        """
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.executemany(sql, values)
                return cursor.rowcount
        except Exception as e:
            logger.error(
                f"Failed to execute bulk update on database alias '{self.db_alias}': {str(e)}"
            )
            raise QueryError(
                f"Failed to execute bulk update: {str(e)}",
                sql=sql,
                db_alias=self.db_alias,
            ) from e

    @staticmethod
    def _row_to_dict(cursor, row):
        """
        Convert a database row to dictionary.

        Args:
            cursor: Database cursor
            row: Database row tuple

        Returns:
            Dictionary representation of the row
        """
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    @staticmethod
    def _rows_to_dict(cursor):
        """
        Convert database rows to list of dictionaries.

        Args:
            cursor: Database cursor

        Returns:
            List of dictionary representations of rows
        """
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @abstractmethod
    def get_entity_name(self):
        """
        Get the name of the entity this data layer handles.
        Must be implemented by subclasses.

        Returns:
            Entity name
        """
        pass


class DataLayerUtils:
    @staticmethod
    def format_in_clause_params(value):
        """
        Format a value for use in an IN clause, converting it to a list.

        Args:
            value: The value to format. Can be:
                - String representation of a tuple/list
                - Actual tuple/list
                - Single value

        Returns:
            List of values suitable for IN clause
        """
        if isinstance(value, str):
            # Check if it's a string representation of a tuple/list
            if (value.startswith("(") and value.endswith(")")) or (
                value.startswith("[") and value.endswith("]")
            ):
                try:
                    # Try to safely evaluate the string as a literal
                    parsed = ast.literal_eval(value)
                    return (
                        list(parsed) if isinstance(parsed, (list, tuple)) else [parsed]
                    )
                except (ValueError, SyntaxError):
                    # If it fails, split by comma and clean up
                    items = value.strip("()[]").split(",")
                    return [item.strip().strip("\"'") for item in items if item.strip()]
            return [value]
        elif isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    @staticmethod
    def to_pg_array(values):
        """
        Convert list of values to PostgreSQL array string.

        Args:
            values: List of values to convert

        Returns:
            PostgreSQL array literal string
        """
        # Properly quote and escape values
        quoted_values = []
        for v in values:
            # Replace double quotes with escaped double quotes
            escaped_value = str(v).replace('"', '""')
            quoted_values.append(f'"{escaped_value}"')
        return "{" + ",".join(quoted_values) + "}"

    def prepare_sql_params(self, params):
        """
        Prepare SQL parameters for PostgreSQL array handling.

        Args:
            params: Dictionary of parameters

        Returns:
            Dict with properly formatted parameters
        """
        prepared_params = {}

        for key, value in params.items():
            if isinstance(value, (list, tuple)) or (
                isinstance(value, str)
                and (value.startswith("(") or value.startswith("["))
            ):
                # Convert to list and clean values
                values = self.format_in_clause_params(value)
                # Filter out empty strings and None values
                values = [v for v in values if v is not None and str(v).strip()]
                prepared_params[key] = self.to_pg_array(values) if values else "{}"
            else:
                prepared_params[key] = value

        return prepared_params
