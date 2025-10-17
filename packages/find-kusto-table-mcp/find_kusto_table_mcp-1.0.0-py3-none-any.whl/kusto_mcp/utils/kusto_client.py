"""
Kusto connection and query execution utilities.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

try:
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder, ClientRequestProperties
    from azure.kusto.data.exceptions import KustoServiceError
    from azure.identity import DefaultAzureCredential, AzureCliCredential, ManagedIdentityCredential
    KUSTO_AVAILABLE = True
except ImportError:
    KUSTO_AVAILABLE = False
    KustoClient = None
    KustoConnectionStringBuilder = None

from ..core.exceptions import ConnectionError, QueryError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..core.config import get_config
from ..core.resilience import (
    get_circuit_breaker, 
    get_bulkhead, 
    RetryStrategy,
    FallbackHandler
)

logger = get_logger("kusto")

# Initialize resilience patterns for Kusto operations
kusto_circuit_breaker = get_circuit_breaker("kusto_query", failure_threshold=5, timeout=60)
kusto_bulkhead = get_bulkhead("kusto_concurrent", max_concurrent=20)
kusto_retry = RetryStrategy(max_attempts=3, base_delay=1.0, max_delay=10.0)
kusto_fallback = FallbackHandler()


class RealKustoClient:
    """
    Real Azure Data Explorer (Kusto) client using azure-kusto-data SDK.
    Supports multiple authentication methods with automatic fallback.
    """
    
    def __init__(self, cluster: str, database: str = None, connection_string: str = None):
        if not KUSTO_AVAILABLE:
            raise ImportError(
                "Azure Kusto SDK not available. Install with: pip install azure-kusto-data azure-identity"
            )
        
        self.cluster = cluster
        self.database = database
        
        # Handle cluster URL formatting
        if cluster.startswith("https://") or cluster.startswith("http://"):
            self.cluster_url = cluster
        elif ".kusto.windows.net" in cluster or ".kusto." in cluster:
            # Already has the full domain
            self.cluster_url = f"https://{cluster}"
        else:
            # Short name, needs .kusto.windows.net suffix
            self.cluster_url = f"https://{cluster}.kusto.windows.net"
        
        # Build connection string with authentication
        if connection_string:
            # Use provided connection string
            self.kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                connection_string, **self._parse_connection_string(connection_string)
            )
        else:
            # Use Azure credential providers with automatic fallback
            # First try Azure CLI (most common for local development)
            try:
                credential = AzureCliCredential()
                credential.get_token("https://help.kusto.windows.net/.default")  # Test if CLI is logged in
                self.kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(self.cluster_url)
                logger.info(f"Using Azure CLI authentication for {cluster}")
            except Exception as cli_error:
                logger.debug(f"Azure CLI authentication not available: {cli_error}")
                try:
                    # Try managed identity (for Azure-hosted scenarios)
                    credential = ManagedIdentityCredential()
                    self.kcsb = KustoConnectionStringBuilder.with_aad_managed_service_identity_authentication(
                        self.cluster_url
                    )
                    logger.info(f"Using Managed Identity authentication for {cluster}")
                except Exception as msi_error:
                    logger.debug(f"Managed Identity authentication not available: {msi_error}")
                    # Fall back to device authentication
                    self.kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(self.cluster_url)
                    logger.info(f"Using device authentication for {cluster}")
        
        self.client = KustoClient(self.kcsb)
        logger.info(f"Initialized real Kusto client for {self.cluster_url}")
    
    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """Parse connection string into components"""
        parts = {}
        for pair in conn_str.split(';'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                parts[key.strip()] = value.strip()
        return parts
    
    async def list_databases(self) -> List[str]:
        """List all databases in the cluster"""
        query = ".show databases | project DatabaseName"
        
        try:
            # Execute as management command (doesn't require a database context)
            response = await asyncio.to_thread(self.client.execute_mgmt, None, query)
            
            databases = []
            if response and response.primary_results:
                for row in response.primary_results[0]:
                    databases.append(row["DatabaseName"])
            
            return databases
        except Exception as e:
            logger.error(f"Failed to list databases on {self.cluster}: {e}")
            return []
    
    async def list_tables(self, database: str = None) -> List[Dict[str, Any]]:
        """List all tables in a database"""
        db = database or self.database
        if not db:
            raise ValueError("Database must be specified")
        
        query = ".show tables | project TableName, DatabaseName, Folder, DocString"
        
        try:
            # Execute as management command (doesn't use asyncio.to_thread - already synchronous)
            response = self.client.execute_mgmt(db, query)
            
            tables = []
            if response and response.primary_results:
                for row in response.primary_results[0]:
                    # KustoResultRow doesn't have .get() - use try/except for optional fields
                    try:
                        tables.append({
                            "TableName": row["TableName"],
                            "DatabaseName": row["DatabaseName"] if "DatabaseName" in row else db,
                            "Folder": row["Folder"] if "Folder" in row else "",
                            "DocString": row["DocString"] if "DocString" in row else ""
                        })
                    except (KeyError, IndexError) as e:
                        logger.warning(f"Skipping row due to missing field: {e}")
                        continue
            
            return tables
        except Exception as e:
            logger.error(f"Failed to list tables in {self.cluster}.{db}: {e}")
            return []
    
    @kusto_circuit_breaker.protect
    @kusto_bulkhead.limit
    @kusto_retry.retry
    async def execute_query(
        self, 
        query: str, 
        timeout_seconds: int = 30,
        use_database: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Execute KQL query and return results with column metadata
        
        Protected by:
        - Circuit breaker (fails fast after 5 consecutive failures)
        - Bulkhead (limits to 20 concurrent queries)
        - Retry logic (3 attempts with exponential backoff)
        
        Returns:
            (results, columns)
        """
        with measure_operation("kusto_execute_query", {
            'cluster': self.cluster,
            'database': self.database,
            'query_length': len(query),
            'use_real_kusto': True
        }):
            try:
                # Set request properties for timeout and other options
                properties = ClientRequestProperties()
                properties.set_option(ClientRequestProperties.request_timeout_option_name, 
                                     timedelta(seconds=timeout_seconds))
                
                # Execute query
                db = self.database if use_database else None
                if not db and use_database:
                    raise ValueError("Database must be set to execute queries")
                
                response = await asyncio.to_thread(
                    self.client.execute_query, 
                    db, 
                    query, 
                    properties
                )
                
                # Parse results
                results = []
                columns = []
                
                # The Kusto response has different result tables in the response
                # We need to safely access the primary results
                try:
                    # Try to get primary_results - this is the standard method
                    if not hasattr(response, 'primary_results'):
                        logger.warning("Response has no primary_results attribute")
                        return results, columns
                    
                    primary_tables = response.primary_results
                    if not primary_tables or len(primary_tables) == 0:
                        logger.warning("No primary result tables in response")
                        return results, columns
                    
                    # Get the first (primary) result table
                    primary_result_table = primary_tables[0]
                    
                    # Extract column metadata from the table
                    if not hasattr(primary_result_table, 'columns'):
                        logger.warning("Primary result table has no columns attribute")
                        return results, columns
                    
                    table_columns = primary_result_table.columns
                    if not table_columns:
                        logger.warning("Primary result table has empty columns")
                        return results, columns
                    
                    for col in table_columns:
                        col_name = col.column_name if hasattr(col, 'column_name') else str(col)
                        col_type = str(col.column_type).lower() if hasattr(col, 'column_type') else 'unknown'
                        columns.append({
                            "name": col_name,
                            "type": col_type
                        })
                    logger.debug(f"Extracted {len(columns)} columns")
                    
                    # Extract data rows - iterate through the table
                    for row in primary_result_table:
                        row_dict = {}
                        for idx, col in enumerate(table_columns):
                            col_name = col.column_name if hasattr(col, 'column_name') else str(col)
                            # Try index-based access (most reliable for Kusto SDK)
                            try:
                                row_dict[col_name] = row[idx]
                            except (IndexError, TypeError, KeyError) as e:
                                # Fallback to name-based access
                                try:
                                    row_dict[col_name] = row[col_name]
                                except:
                                    row_dict[col_name] = None
                        results.append(row_dict)
                    
                except AttributeError as e:
                    logger.error(f"Error accessing response structure: {e}", exc_info=True)
                    raise QueryError(f"Failed to parse Kusto response: {str(e)}", query=query)
                except Exception as e:
                    logger.error(f"Error parsing results: {e}", exc_info=True)
                    # Don't fail completely - return what we have
                    pass
                
                logger.info(f"Query executed successfully on {self.cluster}.{db}: {len(results)} rows")
                return results, columns
                
            except KustoServiceError as e:
                logger.error(f"Kusto query failed: {e}")
                raise QueryError(f"Kusto query failed: {str(e)}", query=query)
            except Exception as e:
                logger.error(f"Query execution failed on {self.cluster}.{self.database}: {e}")
                raise QueryError(f"Query execution failed: {str(e)}", query=query)


class MockKustoClient:
    """
    Mock Kusto client for development and testing.
    In production, this would be replaced with actual Azure Data Explorer client.
    """
    
    def __init__(self, cluster: str, database: str = None):
        self.cluster = cluster
        self.database = database
        self.connection_string = f"https://{cluster}.kusto.windows.net"
    
    async def list_databases(self) -> List[str]:
        """List all databases in the cluster"""
        # Mock databases - in production would query .show databases
        return ["Database1", "Database2", "TestDB", "ProductionDB"]
    
    async def list_tables(self, database: str = None) -> List[Dict[str, Any]]:
        """List all tables in a database"""
        db = database or self.database
        if not db:
            raise ValueError("Database must be specified")
        
        # Mock tables - in production would query .show tables
        mock_tables = [
            {"TableName": "RequestLogs", "DatabaseName": db, "Folder": "", "DocString": "HTTP request logs"},
            {"TableName": "ErrorLogs", "DatabaseName": db, "Folder": "", "DocString": "Application error logs"},
            {"TableName": "MetricData", "DatabaseName": db, "Folder": "Monitoring", "DocString": "Performance metrics"},
            {"TableName": "AuditTrail", "DatabaseName": db, "Folder": "Security", "DocString": "Audit events"},
            {"TableName": "UserActivity", "DatabaseName": db, "Folder": "", "DocString": "User activity tracking"},
        ]
        return mock_tables
    
    async def execute_query(
        self, 
        query: str, 
        timeout_seconds: int = 30
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Execute KQL query and return results with column metadata
        
        Returns:
            (results, columns)
        """
        with measure_operation("kusto_execute_query", {
            'cluster': self.cluster,
            'database': self.database,
            'query_length': len(query)
        }):
            # Simulate query execution delay
            await asyncio.sleep(0.1)
            
            # Mock results based on query pattern
            if "getschema" in query.lower():
                return self._mock_schema_results()
            elif "count" in query.lower():
                return self._mock_count_results()
            elif "take" in query.lower() or "limit" in query.lower():
                return self._mock_sample_results()
            else:
                return self._mock_generic_results()
    
    def _mock_schema_results(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Mock schema query results"""
        results = [
            {"ColumnName": "Timestamp", "ColumnType": "datetime", "DataType": "System.DateTime"},
            {"ColumnName": "Level", "ColumnType": "string", "DataType": "System.String"},
            {"ColumnName": "Message", "ColumnType": "string", "DataType": "System.String"},
            {"ColumnName": "Properties", "ColumnType": "dynamic", "DataType": "System.Object"},
            {"ColumnName": "UserId", "ColumnType": "string", "DataType": "System.String"},
            {"ColumnName": "SessionId", "ColumnType": "string", "DataType": "System.String"},
            {"ColumnName": "RequestId", "ColumnType": "string", "DataType": "System.String"},
            {"ColumnName": "Duration", "ColumnType": "timespan", "DataType": "System.TimeSpan"},
            {"ColumnName": "ResponseCode", "ColumnType": "int", "DataType": "System.Int32"},
            {"ColumnName": "BytesTransferred", "ColumnType": "long", "DataType": "System.Int64"}
        ]
        
        columns = [
            {"name": "ColumnName", "type": "string"},
            {"name": "ColumnType", "type": "string"},
            {"name": "DataType", "type": "string"}
        ]
        
        return results, columns
    
    def _mock_count_results(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Mock count query results"""
        results = [{"Count": 150423}]
        columns = [{"name": "Count", "type": "long"}]
        return results, columns
    
    def _mock_sample_results(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Mock sample data results"""
        results = []
        for i in range(10):
            results.append({
                "Timestamp": f"2024-10-13T{10+i:02d}:30:00.000Z",
                "Level": ["Info", "Warning", "Error"][i % 3],
                "Message": f"Sample log message {i+1}",
                "Properties": f'{{"key": "value{i+1}"}}',
                "UserId": f"user_{1000+i}",
                "SessionId": f"session_{2000+i}",
                "RequestId": f"req_{3000+i}",
                "Duration": f"00:00:0{i}.{100+i*10:03d}",
                "ResponseCode": [200, 404, 500][i % 3],
                "BytesTransferred": 1024 * (i + 1)
            })
        
        columns = [
            {"name": "Timestamp", "type": "datetime"},
            {"name": "Level", "type": "string"},
            {"name": "Message", "type": "string"},
            {"name": "Properties", "type": "dynamic"},
            {"name": "UserId", "type": "string"},
            {"name": "SessionId", "type": "string"},
            {"name": "RequestId", "type": "string"},
            {"name": "Duration", "type": "timespan"},
            {"name": "ResponseCode", "type": "int"},
            {"name": "BytesTransferred", "type": "long"}
        ]
        
        return results, columns
    
    def _mock_generic_results(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Mock generic query results"""
        results = [
            {"Column1": "Value1", "Column2": 42, "Column3": "2024-10-13T10:30:00.000Z"},
            {"Column1": "Value2", "Column2": 84, "Column3": "2024-10-13T10:31:00.000Z"},
            {"Column1": "Value3", "Column2": 126, "Column3": "2024-10-13T10:32:00.000Z"}
        ]
        
        columns = [
            {"name": "Column1", "type": "string"},
            {"name": "Column2", "type": "int"},
            {"name": "Column3", "type": "datetime"}
        ]
        
        return results, columns


class KustoConnectionManager:
    """Manages connections to multiple Kusto clusters"""
    
    def __init__(self):
        if not KUSTO_AVAILABLE:
            raise ImportError(
                "Azure Kusto SDK is required. Install with: pip install azure-kusto-data azure-identity"
            )
        
        self.clients: Dict[str, Any] = {}
        self.cluster_clients: Dict[str, Any] = {}
        self.config = get_config()
        self.connection_strings = self._load_connection_strings()
        
        logger.info("Using Azure Data Explorer client")
    
    def _load_connection_strings(self) -> Dict[str, str]:
        """Load connection strings from config file"""
        try:
            conn_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'cache', 'connection_strings.json')
            if os.path.exists(conn_file):
                with open(conn_file, 'r') as f:
                    data = json.load(f)
                    # Extract cluster names from the new format
                    # Format: {"name": "azcore", "url": "https://azcore.centralus.kusto.windows.net", ...}
                    conn_strings = {}
                    for cluster_info in data.get('clusters', []):
                        # Get cluster name (short name like "azcore")
                        cluster_name = cluster_info.get('name', '')
                        # Get full URL
                        url = cluster_info.get('url', '')
                        
                        # Extract the full cluster domain from URL
                        # e.g., "https://azcore.centralus.kusto.windows.net" -> "azcore.centralus.kusto.windows.net"
                        if url and cluster_name:
                            full_cluster = url.replace('https://', '').replace('http://', '')
                            # Store both short name and full domain
                            conn_strings[cluster_name] = full_cluster
                            conn_strings[full_cluster] = full_cluster
                    
                    logger.info(f"Loaded {len(conn_strings)} cluster configurations")
                    return conn_strings
        except Exception as e:
            logger.warning(f"Failed to load connection strings: {e}")
        return {}
    
    def get_cluster_client(self, cluster: str) -> RealKustoClient:
        """Get or create a cluster-level client (no database specified)"""
        if cluster not in self.cluster_clients:
            # Resolve cluster name (could be short name or full domain)
            resolved_cluster = self.connection_strings.get(cluster, cluster)
            
            try:
                self.cluster_clients[cluster] = RealKustoClient(
                    resolved_cluster, 
                    database=None,
                    connection_string=None  # Use Azure CLI auth by default
                )
                logger.info(f"Created Kusto cluster client for {cluster} (resolved to {resolved_cluster})")
            except Exception as e:
                logger.error(f"Failed to create Kusto client for {cluster}: {e}")
                raise ConnectionError(
                    f"Failed to connect to Kusto cluster {cluster}: {e}",
                    cluster=cluster
                )
        
        return self.cluster_clients[cluster]
    
    def get_client(self, cluster: str, database: str) -> RealKustoClient:
        """Get or create a client for the specified cluster and database"""
        key = f"{cluster}.{database}"
        
        if key not in self.clients:
            # Resolve cluster name (could be short name or full domain)
            resolved_cluster = self.connection_strings.get(cluster, cluster)
            
            try:
                self.clients[key] = RealKustoClient(
                    resolved_cluster, 
                    database=database,
                    connection_string=None  # Use Azure CLI auth by default
                )
                logger.info(f"Created Kusto client for {key} (resolved to {resolved_cluster})")
            except Exception as e:
                logger.error(f"Failed to create Kusto client for {key}: {e}")
                raise ConnectionError(
                    f"Failed to connect to Kusto database {cluster}.{database}: {e}",
                    cluster=cluster
                )
        
        return self.clients[key]
    
    async def execute_query(
        self,
        cluster: str,
        database: str,
        query: str,
        timeout_seconds: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Execute a query on the specified cluster and database"""
        client = self.get_client(cluster, database)
        timeout = timeout_seconds or self.config.performance.query_timeout_seconds
        
        try:
            return await client.execute_query(query, timeout)
        except Exception as e:
            logger.error(f"Query execution failed on {cluster}.{database}: {e}")
            raise QueryError(f"Query execution failed: {str(e)}", query=query)
    
    async def test_connection(self, cluster: str, database: str) -> bool:
        """Test connection to a cluster/database"""
        try:
            client = self.get_client(cluster, database)
            # Use simple query that works with both mock and real clients
            await client.execute_query("print 'connection_test'")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {cluster}.{database}: {e}")
            return False
    
    async def get_table_schema(
        self,
        cluster: str,
        database: str,
        table: str
    ) -> Optional[Dict[str, Any]]:
        """Get schema information for a table"""
        query = f"{table} | getschema | project ColumnName, ColumnType, DataType"
        
        try:
            results, columns = await self.execute_query(cluster, database, query)
            
            if not results:
                return None
            
            schema_columns = []
            time_columns = []
            numeric_columns = []
            string_columns = []
            
            for row in results:
                col_name = row.get("ColumnName", "")
                col_type = row.get("ColumnType", "").lower()
                
                schema_columns.append({
                    "name": col_name,
                    "type": col_type
                })
                
                # Categorize columns
                if "datetime" in col_type or "timestamp" in col_type:
                    time_columns.append(col_name)
                elif any(t in col_type for t in ["int", "long", "real", "decimal", "double"]):
                    numeric_columns.append(col_name)
                elif "string" in col_type:
                    string_columns.append(col_name)
            
            return {
                "table_path": f"{cluster}.{database}.{table}",
                "cluster": cluster,
                "database": database,
                "table": table,
                "columns": schema_columns,
                "time_columns": time_columns,
                "numeric_columns": numeric_columns,
                "string_columns": string_columns,
                "primary_time_column": time_columns[0] if time_columns else None,
                "fetched_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get schema for {cluster}.{database}.{table}: {e}")
            return None
    
    async def sample_table(
        self,
        cluster: str,
        database: str,
        table: str,
        sample_size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Get sample data from a table"""
        query = f"{table} | take {sample_size}"
        
        try:
            results, columns = await self.execute_query(cluster, database, query)
            
            return {
                "table_path": f"{cluster}.{database}.{table}",
                "cluster": cluster,
                "database": database,
                "table": table,
                "sample_rows": results,
                "columns": columns,
                "sample_size": len(results),
                "sampled_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to sample table {cluster}.{database}.{table}: {e}")
            return None
    
    def close_all_connections(self):
        """Close all connections"""
        self.clients.clear()
        logger.info("All Kusto connections closed")


# Global connection manager instance
connection_manager = KustoConnectionManager()


def get_connection_manager() -> KustoConnectionManager:
    """Get the global connection manager"""
    return connection_manager