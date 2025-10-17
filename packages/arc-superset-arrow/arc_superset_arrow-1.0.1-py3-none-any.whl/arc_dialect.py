"""
Custom SQLAlchemy dialect for Arc API integration with Superset using Apache Arrow
"""
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

import requests
import pyarrow as pa
from sqlalchemy import pool, text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.sql import sqltypes
from sqlalchemy.types import TypeEngine
from sqlalchemy.sql.compiler import SQLCompiler, DDLCompiler, GenericTypeCompiler

# SQLAlchemy 2.x compatibility
try:
    from sqlalchemy.engine.interfaces import Dialect, DBAPIConnection
except ImportError:
    # SQLAlchemy 2.x moved these
    from sqlalchemy.engine import Dialect
    from sqlalchemy.pool.base import _ConnectionRecord as DBAPIConnection

logger = logging.getLogger(__name__)


class ArcCompiler(SQLCompiler):
    """SQL statement compiler for Arc dialect"""
    pass


class ArcDDLCompiler(DDLCompiler):
    """DDL compiler for Arc dialect"""
    pass


class ArcTypeCompiler(GenericTypeCompiler):
    """Type compiler for Arc dialect"""
    pass


class ArcDBAPIConnection:
    """DBAPI-like connection for Arc API"""

    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })

    def cursor(self):
        return ArcCursor(self)

    def close(self):
        self.session.close()

    def commit(self):
        pass  # No transactions in Arc API

    def rollback(self):
        pass  # No transactions in Arc API


class ArcCursor:
    """DBAPI-like cursor for Arc API"""

    def __init__(self, connection: ArcDBAPIConnection):
        self.connection = connection
        self.description = None
        self.rowcount = 0
        self._rows = []

    def execute(self, sql: str, parameters=None):
        """Execute SQL query via Arc API using Apache Arrow IPC"""
        try:
            # Clean up the SQL query
            query = sql.strip()
            if query.endswith(';'):
                query = query[:-1]

            # Prepare request payload
            payload = {
                "sql": query,
                "limit": 10000,  # Default limit, can be overridden
            }

            # Extract LIMIT from SQL if present
            if 'LIMIT' in query.upper():
                # Simple regex to extract limit - could be more sophisticated
                import re
                limit_match = re.search(r'LIMIT\s+(\d+)', query.upper())
                if limit_match:
                    payload["limit"] = int(limit_match.group(1))

            logger.info(f"Executing query via Arc Arrow API: {query[:200]}...")

            # Make API request to Arrow endpoint
            response = self.connection.session.post(
                f"{self.connection.api_base_url}/query/arrow",
                json=payload,
                timeout=300  # 5 minute timeout
            )

            if response.status_code == 401:
                raise Exception("Authentication failed - check API key")
            elif response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")

            # Parse Arrow IPC response
            # The response is Arrow IPC format (stream)
            arrow_buffer = pa.BufferReader(response.content)
            arrow_reader = pa.ipc.open_stream(arrow_buffer)

            # Read all record batches into a single table
            arrow_table = arrow_reader.read_all()

            # Extract columns and convert to Python lists
            columns = arrow_table.schema.names

            # Convert Arrow table to list of rows (tuples)
            # Using to_pydict() and then converting to row format
            data_dict = arrow_table.to_pydict()
            num_rows = len(arrow_table)

            # Convert columnar format to row format
            data = []
            for i in range(num_rows):
                row = tuple(data_dict[col][i] for col in columns)
                data.append(row)

            # Set cursor description (column metadata)
            # Map Arrow types to SQLAlchemy types
            self.description = []
            for col_name, arrow_field in zip(columns, arrow_table.schema):
                sql_type = self._arrow_type_to_sqlalchemy(arrow_field.type)
                self.description.append((col_name, sql_type, None, None, None, None, True))

            self.rowcount = num_rows
            self._rows = data

            logger.info(f"Query executed successfully via Arrow: {self.rowcount} rows returned")

        except Exception as e:
            logger.error(f"Error executing query via Arrow: {e}")
            raise

    def _arrow_type_to_sqlalchemy(self, arrow_type):
        """Map Arrow types to SQLAlchemy types"""
        import pyarrow.types as pat

        if pat.is_integer(arrow_type):
            return sqltypes.Integer
        elif pat.is_floating(arrow_type):
            return sqltypes.Float
        elif pat.is_boolean(arrow_type):
            return sqltypes.Boolean
        elif pat.is_timestamp(arrow_type) or pat.is_date(arrow_type):
            return sqltypes.DateTime
        elif pat.is_string(arrow_type) or pat.is_large_string(arrow_type):
            return sqltypes.String
        else:
            # Default to String for unknown types
            return sqltypes.String

    def fetchall(self):
        """Fetch all remaining rows"""
        return self._rows

    def fetchone(self):
        """Fetch next row"""
        if self._rows:
            return self._rows.pop(0)
        return None

    def fetchmany(self, size=None):
        """Fetch multiple rows"""
        if size is None:
            size = len(self._rows)
        result = self._rows[:size]
        self._rows = self._rows[size:]
        return result

    def close(self):
        """Close cursor"""
        self._rows = []
        self.description = None


class ArcDialect(Dialect):
    """SQLAlchemy dialect for Arc API"""

    name = "arc"
    driver = "api"
    supports_alter = False
    supports_pk_autoincrement = False
    supports_default_values = False
    supports_empty_insert = False
    supports_unicode_statements = True
    supports_unicode_binds = True
    returns_unicode_strings = True
    description_encoding = None
    supports_native_boolean = True
    supports_simple_order_by_label = True
    paramstyle = 'named'  # Use named parameters

    # SQLAlchemy 2.x compatibility
    supports_statement_cache = True
    supports_server_side_cursors = False
    is_async = False
    positional = False  # Use named parameters instead of positional
    label_length = None  # No limit on label length
    max_identifier_length = None  # No limit on identifier length
    max_index_name_length = None  # No limit on index name length
    max_column_name_length = None  # No limit on column name length
    supports_sequences = False
    sequences_optional = False
    preexecute_autoincrement_sequences = False
    postfetch_lastrowid = False
    implicit_returning = False
    full_returning = False
    insert_executemany_returning = False
    update_executemany_returning = False
    delete_executemany_returning = False
    supports_multivalues_insert = False
    supports_comments = False
    inline_comments = False
    supports_constraint_comments = False
    supports_expression_defaults = False
    tuple_in_values = False
    supports_native_enum = False
    non_native_boolean_check_constraint = False
    cte_follows_with = False
    engine_config_types = {}
    default_schema_name = None
    server_version_info = None
    construct_arguments = []
    requires_name_normalize = False
    reflection_options = []
    dbapi_exception_translation_map = {}

    def __init__(self, **kwargs):
        """Initialize the dialect with any keyword arguments"""
        # Don't pass kwargs to parent, just initialize basic dialect
        super().__init__()

        # Initialize identifier preparer
        from sqlalchemy.sql.compiler import IdentifierPreparer
        self.identifier_preparer = IdentifierPreparer(self)

        # Initialize internal SQLAlchemy attributes
        self._type_memos = {}
        self._on_connect_url = None
        self._on_connect_url_token = None
        self._json_serializer = None
        self._json_deserializer = None

        # Store any additional parameters we might need
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def statement_compiler(self):
        """Return the statement compiler class"""
        return ArcCompiler

    @property
    def ddl_compiler(self):
        """Return the DDL compiler class"""
        return ArcDDLCompiler

    @property
    def type_compiler(self):
        """Return the type compiler class"""
        return ArcTypeCompiler

    @classmethod
    def dbapi(cls):
        """Return the DBAPI module (we implement our own)"""
        # Create a minimal DBAPI-like module
        class ArcDBAPI:
            Error = Exception
            Warning = UserWarning
            InterfaceError = Exception
            DatabaseError = Exception
            DataError = Exception
            OperationalError = Exception
            IntegrityError = Exception
            InternalError = Exception
            ProgrammingError = Exception
            NotSupportedError = Exception

        return ArcDBAPI()

    def get_dialect_pool_class(self, url):
        """Return the connection pool class to use"""
        from sqlalchemy.pool import StaticPool
        return StaticPool

    def create_connect_args(self, url):
        """Parse connection URL and return args for connect()"""
        # URL format: arc://api-key@host:port/database
        api_key = url.username
        host = url.host
        port = url.port or 8000

        if not api_key:
            raise ValueError("API key required in connection URL (arc://api-key@host:port/db)")

        api_base_url = f"http://{host}:{port}"

        return ([api_base_url, api_key], {})

    def connect(self, api_base_url: str, api_key: str):
        """Create a connection to Arc API"""
        return ArcDBAPIConnection(api_base_url, api_key)

    def do_ping(self, dbapi_conn):
        """Test the connection by executing a simple query"""
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            return True
        except Exception:
            return False

    def get_schema_names(self, connection, **kwargs):
        """Get available schemas (databases in Arc)

        Arc now supports multi-database architecture where each database
        is exposed as a schema in Superset.
        """
        try:
            # Get the raw DBAPI connection
            if hasattr(connection, 'connection'):
                dbapi_conn = connection.connection
            else:
                dbapi_conn = connection

            # Use SHOW DATABASES to get all databases
            cursor = dbapi_conn.cursor()
            cursor.execute("SHOW DATABASES")

            databases = []
            if cursor.description:
                for row in cursor.fetchall():
                    if len(row) >= 1 and row[0]:
                        databases.append(row[0])

            logger.info(f"Found {len(databases)} databases: {databases}")

            if databases:
                return databases
            else:
                # Fallback to default if SHOW DATABASES returns nothing
                return ["default"]
        except Exception as e:
            logger.warning(f"Could not get databases, using default: {e}")
            return ["default"]

    def has_table(self, connection, table_name, schema=None):
        """Check if table exists (we'll try to query it)"""
        try:
            # Get the raw DBAPI connection
            if hasattr(connection, 'connection'):
                dbapi_conn = connection.connection
            else:
                dbapi_conn = connection

            cursor = dbapi_conn.cursor()

            # Construct the proper table reference with schema
            if schema and schema != "default":
                table_ref = f"{schema}.{table_name}"
            else:
                table_ref = table_name

            cursor.execute(f"SELECT 1 FROM {table_ref} LIMIT 1")
            return True
        except Exception:
            return False

    def get_table_names(self, connection, schema=None, **kwargs):
        """Get available table names for a specific database (schema)

        Args:
            connection: Database connection
            schema: Database name (in Arc, databases are exposed as schemas)
            **kwargs: Additional SQLAlchemy kwargs

        Returns:
            List of table names in the specified database
        """
        # Accept and ignore additional kwargs like info_cache from SQLAlchemy
        try:
            logger.info(f"get_table_names called with schema='{schema}', connection type={type(connection)}")

            # Get the raw DBAPI connection
            if hasattr(connection, 'connection'):
                # SQLAlchemy Connection object
                dbapi_conn = connection.connection
                logger.info(f"Using connection.connection (DBAPI): {type(dbapi_conn)}")
            else:
                # Already a DBAPI connection
                dbapi_conn = connection
                logger.info(f"Using connection directly (DBAPI): {type(dbapi_conn)}")

            # Use SHOW TABLES to get actual table list
            cursor = dbapi_conn.cursor()

            # If schema is specified, query that specific database
            if schema:
                sql = f"SHOW TABLES FROM {schema}"
                logger.info(f"Executing: {sql}")
                cursor.execute(sql)
            else:
                sql = "SHOW TABLES"
                logger.info(f"Executing: {sql} (will return tables from ALL databases)")
                cursor.execute(sql)

            tables = set()
            if cursor.description:
                # SHOW TABLES returns: database, table_name, storage_path, file_count, total_size_mb
                # database column = database name (default, production, etc.)
                # table_name column = measurement name (cpu, mem, disk)
                rows = cursor.fetchall()
                logger.info(f"SHOW TABLES returned {len(rows)} rows, cursor.description={cursor.description}")
                for row in rows:
                    logger.info(f"Row data: {row}, row length: {len(row)}, row types: {[type(v).__name__ for v in row]}")
                    if len(row) >= 2:
                        db_name = row[0]  # database
                        table_name = row[1]  # measurement name
                        logger.info(f"  Parsed: db_name='{db_name}', table_name='{table_name}'")

                        # Filter by schema if specified
                        if schema is None or db_name == schema:
                            tables.add(table_name)
                            logger.info(f"  -> MATCHED: Added table '{table_name}' from database '{db_name}' (schema filter: '{schema}')")
                        else:
                            logger.info(f"  -> SKIPPED: db_name '{db_name}' != schema filter '{schema}'")
                    else:
                        logger.warning(f"  -> Row too short (expected >= 2 columns, got {len(row)}): {row}")

            logger.info(f"Final result: Found {len(tables)} tables in schema '{schema}': {sorted(tables)}")

            if tables:
                return sorted(tables)
            else:
                logger.warning(f"No tables found in schema '{schema}'")
                return []
        except Exception as e:
            logger.error(f"Could not get table names for schema '{schema}': {e}", exc_info=True)
            return []

    def get_columns(self, connection, table_name, schema=None, **kwargs):
        """Get column information for a table"""
        # Accept and ignore additional kwargs like info_cache from SQLAlchemy
        try:
            # Get the raw DBAPI connection
            if hasattr(connection, 'connection'):
                dbapi_conn = connection.connection
            else:
                dbapi_conn = connection

            cursor = dbapi_conn.cursor()

            # Construct the proper table reference with schema
            if schema and schema != "default":
                table_ref = f"{schema}.{table_name}"
            else:
                table_ref = table_name

            logger.info(f"Getting columns for table: {table_ref}")
            cursor.execute(f"SELECT * FROM {table_ref} LIMIT 1")

            if cursor.description:
                columns = []
                for col_desc in cursor.description:
                    col_name = col_desc[0]
                    col_type = sqltypes.String()  # Default to String

                    # Map common column names to appropriate types
                    if 'timestamp' in col_name.lower():
                        col_type = sqltypes.DateTime()
                    elif any(word in col_name.lower() for word in ['count', 'id', 'size']):
                        col_type = sqltypes.Integer()
                    elif any(word in col_name.lower() for word in ['percent', 'usage', 'rate', 'average']):
                        col_type = sqltypes.Float()

                    columns.append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': True,
                        'default': None
                    })

                logger.info(f"Found {len(columns)} columns for {table_ref}")
                return columns
        except Exception as e:
            logger.error(f"Could not get columns for {table_name} (schema: {schema}): {e}")

        return []

    def get_pk_constraint(self, connection, table_name, schema=None, **kwargs):
        """Get primary key constraint (none for Arc tables)"""
        return {'constrained_columns': [], 'name': None}

    def get_foreign_keys(self, connection, table_name, schema=None, **kwargs):
        """Get foreign key constraints (none for Arc tables)"""
        return []

    def get_indexes(self, connection, table_name, schema=None, **kwargs):
        """Get index information (none for Arc tables)"""
        return []

    def get_view_names(self, connection, schema=None, **kwargs):
        """Get view names (none for Arc - all are tables)"""
        return []

    def do_rollback(self, dbapi_connection):
        """Handle transaction rollback (no-op for Arc API)"""
        pass

    def do_commit(self, dbapi_connection):
        """Handle transaction commit (no-op for Arc API)"""
        pass

    def type_descriptor(self, type_):
        """Return a TypeEngine instance that represents the type"""
        # For our dialect, we mainly deal with basic types
        # Default to String for most cases, with some specific mappings
        from sqlalchemy.sql import sqltypes

        if isinstance(type_, sqltypes.String):
            return type_
        elif isinstance(type_, sqltypes.Integer):
            return type_
        elif isinstance(type_, sqltypes.Float):
            return type_
        elif isinstance(type_, sqltypes.DateTime):
            return type_
        elif isinstance(type_, sqltypes.Boolean):
            return type_
        else:
            # Default to String for unknown types
            return sqltypes.String()

    def do_close(self, dbapi_connection):
        """Handle connection close"""
        try:
            if hasattr(dbapi_connection, 'close'):
                dbapi_connection.close()
        except Exception:
            pass  # Ignore close errors


# Register the dialect
def register_arc_dialect():
    """Register the Arc dialect with SQLAlchemy"""
    from sqlalchemy.dialects import registry
    registry.register("arc", "arc_dialect", "ArcDialect")
    registry.register("arc.api", "arc_dialect", "ArcDialect")


# Auto-register when module is imported
register_arc_dialect()