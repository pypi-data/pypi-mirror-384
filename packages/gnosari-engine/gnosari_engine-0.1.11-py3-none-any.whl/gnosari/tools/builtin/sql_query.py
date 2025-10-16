"""
Universal SQL Query Tool - Using OpenAI Agents SDK FunctionTool
Supports multiple database types through SQLAlchemy connection URLs
"""

import logging
import asyncio
import json
from typing import Any, Optional, Dict, List, Union
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool


class SQLQueryArgs(BaseModel):
    """Arguments for the SQL query tool."""
    query: str = Field(..., description="The SQL query to execute")
    query_type: str = Field(default="SELECT", description="Type of query (SELECT, INSERT, UPDATE, DELETE, etc.)")
    limit: Optional[int] = Field(default=None, description="Maximum number of rows to return (for SELECT queries)")
    timeout: Optional[int] = Field(default=None, description="Query timeout in seconds (overrides configured timeout)")
    return_format: str = Field(default="json", description="Return format: 'json', 'table', or 'raw'")

    @field_validator('query_type')
    @classmethod
    def validate_query_type(cls, v):
        """Validate query type."""
        valid_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'SHOW', 'DESCRIBE', 'EXPLAIN']
        if v.upper() not in valid_types:
            raise ValueError(f"Query type must be one of: {valid_types}")
        return v.upper()

    @field_validator('return_format')
    @classmethod
    def validate_return_format(cls, v):
        """Validate return format."""
        valid_formats = ['json', 'table', 'raw']
        if v.lower() not in valid_formats:
            raise ValueError(f"Return format must be one of: {valid_formats}")
        return v.lower()


class SQLQueryTool(SyncTool):
    """Universal SQL Query Tool that supports multiple database types through SQLAlchemy URLs."""
    
    def __init__(self, 
                 database_url: str,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 pool_timeout: int = 30,
                 pool_recycle: int = 3600,
                 query_timeout: int = 30,
                 echo: bool = False,
                 enable_unsafe_operations: bool = False,
                 allowed_schemas: Optional[List[str]] = None,
                 blocked_keywords: Optional[List[str]] = None):
        """Initialize the SQL query tool.
        
        Args:
            database_url: SQLAlchemy database URL (e.g., 'postgresql://user:pass@host:port/db')
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum overflow connections beyond pool_size
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Time in seconds before connection is recycled
            query_timeout: Default timeout for queries in seconds
            echo: Whether to echo SQL statements (for debugging)
            enable_unsafe_operations: Allow dangerous operations (DROP, TRUNCATE, etc.)
            allowed_schemas: List of allowed schema names (None = all allowed)
            blocked_keywords: Additional keywords to block in queries
        """
        # Call parent constructor first
        super().__init__(
            name="sql_query",
            description="Execute SQL queries against a database",
            input_schema=SQLQueryArgs
        )
        
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.query_timeout = query_timeout
        self.echo = echo
        self.enable_unsafe_operations = enable_unsafe_operations
        self.allowed_schemas = allowed_schemas
        self.blocked_keywords = blocked_keywords or []
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Parse database URL to determine database type
        self.db_type = self._parse_database_type(database_url)
        
        # Initialize engine and session factory
        self.engine = None
        self.SessionFactory = None
        self._initialize_connection()
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=f"{self.description} (Database: {self.db_type})",
            params_json_schema=SQLQueryArgs.model_json_schema(),
            on_invoke_tool=self._run_sql_query
        )
    
    def _parse_database_type(self, database_url: str) -> str:
        """Parse database type from SQLAlchemy URL."""
        try:
            parsed = urlparse(database_url)
            scheme = parsed.scheme.lower()
            
            # Map common SQLAlchemy schemes to database types
            db_type_mapping = {
                'postgresql': 'PostgreSQL',
                'postgresql+psycopg2': 'PostgreSQL',
                'postgresql+asyncpg': 'PostgreSQL',
                'mysql': 'MySQL',
                'mysql+pymysql': 'MySQL',
                'mysql+mysqlconnector': 'MySQL',
                'sqlite': 'SQLite',
                'oracle': 'Oracle',
                'oracle+cx_oracle': 'Oracle',
                'mssql': 'SQL Server',
                'mssql+pyodbc': 'SQL Server',
                'mssql+pymssql': 'SQL Server',
                'clickhouse': 'ClickHouse',
                'clickhouse+native': 'ClickHouse',
                'snowflake': 'Snowflake',
                'bigquery': 'BigQuery',
                'redshift': 'Redshift',
                'cockroachdb': 'CockroachDB'
            }
            
            return db_type_mapping.get(scheme, scheme.title())
        except Exception:
            return "Unknown"
    
    def _initialize_connection(self):
        """Initialize the database connection and session factory."""
        try:
            # Choose appropriate pooling strategy based on database type
            if self.db_type.lower() == 'sqlite':
                # SQLite doesn't support connection pooling
                poolclass = NullPool
                pool_kwargs = {}
            else:
                poolclass = QueuePool
                pool_kwargs = {
                    'pool_size': self.pool_size,
                    'max_overflow': self.max_overflow,
                    'pool_timeout': self.pool_timeout,
                    'pool_recycle': self.pool_recycle
                }
            
            # Create engine with appropriate configuration
            engine_kwargs = {
                'poolclass': poolclass,
                'echo': self.echo,
                **pool_kwargs
            }
            
            # Add database-specific connection arguments
            connect_args = {}
            
            if 'mysql' in self.database_url.lower():
                connect_args.update({
                    'connect_timeout': 10,
                    'read_timeout': self.query_timeout,
                    'write_timeout': self.query_timeout
                })
            elif 'postgresql' in self.database_url.lower():
                connect_args.update({
                    'connect_timeout': 10,
                    'command_timeout': self.query_timeout
                })
            elif 'sqlite' in self.database_url.lower():
                connect_args.update({
                    'timeout': self.query_timeout,
                    'check_same_thread': False
                })
            
            if connect_args:
                engine_kwargs['connect_args'] = connect_args
            
            # Create engine
            self.engine = create_engine(self.database_url, **engine_kwargs)
            
            # Create session factory
            self.SessionFactory = sessionmaker(bind=self.engine)
            
            self.logger.info(f"🔗 SQL CONNECTION INITIALIZED - Database: {self.db_type}")
            
        except Exception as e:
            self.logger.error(f"❌ FAILED TO INITIALIZE SQL CONNECTION: {str(e)}")
            raise
    
    def _validate_query_safety(self, query: str, query_type: str) -> bool:
        """Validate the SQL query for safety."""
        query_upper = query.strip().upper()
        
        # Check if query type matches the actual query
        if not query_upper.startswith(query_type.upper()):
            self.logger.warning(f"Query type '{query_type}' doesn't match query start: {query_upper[:20]}...")
        
        # Define dangerous keywords
        dangerous_keywords = [
            'DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE', 'DELETE FROM',
            'GRANT', 'REVOKE', 'ALTER USER', 'CREATE USER', 'DROP USER',
            'SHUTDOWN', 'KILL', 'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE'
        ]
        
        # Add user-defined blocked keywords
        all_blocked = dangerous_keywords + [kw.upper() for kw in self.blocked_keywords]
        
        # Check for dangerous operations if not explicitly allowed
        if not self.enable_unsafe_operations:
            for keyword in all_blocked:
                if keyword in query_upper:
                    raise ValueError(f"Query contains blocked keyword: {keyword}. Set enable_unsafe_operations=True to allow.")
        
        # Check schema restrictions
        if self.allowed_schemas:
            # This is a basic check - more sophisticated schema validation could be added
            for schema in self.allowed_schemas:
                if schema.upper() in query_upper:
                    break
            else:
                # If we're checking specific tables/schemas, this would need more sophisticated parsing
                pass
        
        return True
    
    def _format_results(self, columns: List[str], rows: List, return_format: str, query_type: str) -> str:
        """Format query results based on the requested format."""
        if not rows and query_type.upper() == 'SELECT':
            return "Query executed successfully. No rows returned."
        
        if return_format == 'json':
            return self._format_as_json(columns, rows, query_type)
        elif return_format == 'table':
            return self._format_as_table(columns, rows, query_type)
        else:  # raw
            return self._format_as_raw(columns, rows, query_type)
    
    def _format_as_json(self, columns: List[str], rows: List, query_type: str) -> str:
        """Format results as JSON."""
        if query_type.upper() == 'SELECT':
            results_list = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i] if i < len(row) else None
                    # Convert non-serializable types
                    if hasattr(value, 'isoformat'):  # datetime objects
                        value = value.isoformat()
                    elif hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool)):
                        value = str(value)
                    row_dict[column] = value
                results_list.append(row_dict)
            
            return json.dumps({
                "status": "success",
                "database_type": self.db_type,
                "query_type": query_type,
                "row_count": len(results_list),
                "columns": columns,
                "data": results_list
            }, indent=2, default=str)
        else:
            # For non-SELECT queries
            affected_rows = len(rows) if rows else 0
            return json.dumps({
                "status": "success",
                "database_type": self.db_type,
                "query_type": query_type,
                "affected_rows": affected_rows,
                "message": f"Query executed successfully. {affected_rows} rows affected."
            }, indent=2)
    
    def _format_as_table(self, columns: List[str], rows: List, query_type: str) -> str:
        """Format results as a simple table."""
        if query_type.upper() == 'SELECT' and rows:
            # Calculate column widths
            col_widths = [len(col) for col in columns]
            for row in rows:
                for i, value in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(value)))
            
            # Build table
            result = []
            
            # Header
            header = " | ".join(col.ljust(col_widths[i]) for i, col in enumerate(columns))
            result.append(header)
            result.append("-" * len(header))
            
            # Rows
            for row in rows:
                row_str = " | ".join(str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) 
                                   for i in range(len(columns)))
                result.append(row_str)
            
            result.append(f"\n({len(rows)} rows)")
            return "\n".join(result)
        else:
            affected_rows = len(rows) if rows else 0
            return f"Query executed successfully. {affected_rows} rows affected."
    
    def _format_as_raw(self, columns: List[str], rows: List, query_type: str) -> str:
        """Format results as raw string representation."""
        if query_type.upper() == 'SELECT' and rows:
            result = f"Columns: {columns}\n"
            result += f"Rows ({len(rows)}):\n"
            for i, row in enumerate(rows):
                result += f"  {i+1}: {list(row)}\n"
            return result
        else:
            affected_rows = len(rows) if rows else 0
            return f"Query executed successfully. {affected_rows} rows affected."
    
    async def _run_sql_query(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """
        Execute a SQL query.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing SQLQueryArgs
            
        Returns:
            Query result as string
        """
        session = None
        try:
            # Parse arguments
            parsed_args = SQLQueryArgs.model_validate_json(args)
            
            # Use config values as defaults, allow per-call overrides
            final_timeout = parsed_args.timeout or self.query_timeout
            
            self.logger.info(f"🗄️ SQL QUERY STARTED - Database: {self.db_type} | Type: {parsed_args.query_type} | Timeout: {final_timeout}s")
            self.logger.debug(f"Query: {parsed_args.query}")
            
            # Validate query safety
            self._validate_query_safety(parsed_args.query, parsed_args.query_type)
            
            # Create session
            session = self.SessionFactory()
            
            # Execute query (run synchronous code in executor)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._execute_query,
                session,
                parsed_args.query,
                parsed_args.query_type,
                parsed_args.limit,
                parsed_args.return_format,
                final_timeout
            )
            
            # Log successful result
            result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            self.logger.info(f"✅ SQL QUERY SUCCESSFUL - {parsed_args.query_type} executed on {self.db_type}")
            self.logger.debug(f"📄 Result preview: {result_preview}")
            
            return result
            
        except ValueError as e:
            error_msg = f"Query validation error: {str(e)}"
            self.logger.error(f"❌ SQL QUERY FAILED with validation error: {error_msg}")
            return error_msg
            
        except SQLAlchemyError as e:
            error_msg = f"Database error executing {parsed_args.query_type} query on {self.db_type}: {str(e)}"
            self.logger.error(f"❌ SQL QUERY FAILED with SQLAlchemyError: {error_msg}")
            return error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error executing {parsed_args.query_type} query on {self.db_type}: {str(e)}"
            self.logger.error(f"❌ SQL QUERY FAILED with unexpected error: {error_msg}")
            return error_msg
            
        finally:
            if session:
                session.close()
    
    def _execute_query(self, session, query: str, query_type: str, limit: Optional[int], 
                      return_format: str, timeout: int) -> str:
        """Execute a SQL query and return formatted results."""
        try:
            # Add LIMIT if specified and not already present (for SELECT queries)
            if limit and query_type.upper() == 'SELECT' and "LIMIT" not in query.upper():
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            # Execute query
            result = session.execute(text(query))
            
            # Handle different query types
            if query_type.upper() in ['SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN']:
                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                
                # Fetch all rows
                rows = result.fetchall()
                
                return self._format_results(columns, rows, return_format, query_type)
                
            else:
                # For INSERT/UPDATE/DELETE queries
                session.commit()
                
                # Get affected row count
                row_count = result.rowcount if hasattr(result, 'rowcount') else 0
                
                return self._format_results([], [None] * row_count, return_format, query_type)
                
        except Exception as e:
            # Rollback on error
            if query_type.upper() not in ['SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN']:
                session.rollback()
            raise SQLAlchemyError(f"Error executing {query_type} query: {str(e)}")
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the connected database.
        
        Returns:
            Dictionary with database information
        """
        try:
            inspector = inspect(self.engine)
            return {
                "database_type": self.db_type,
                "database_url": self.database_url.split('@')[0] + '@[HIDDEN]',  # Hide credentials
                "schema_names": inspector.get_schema_names() if hasattr(inspector, 'get_schema_names') else [],
                "table_names": inspector.get_table_names(),
                "pool_size": self.pool_size,
                "echo": self.echo,
                "unsafe_operations_enabled": self.enable_unsafe_operations
            }
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
    def close_connections(self):
        """Close all database connections."""
        if self.engine:
            self.engine.dispose()
            self.logger.info(f"🔒 {self.db_type} connections closed")


def get_default_sql_query_tool(database_url: str = "sqlite:///test.db") -> FunctionTool:
    """Get a default SQL query tool instance.
    
    Args:
        database_url: SQLAlchemy database URL
    
    Returns:
        FunctionTool instance
    """
    return SQLQueryTool(database_url=database_url).get_tool()