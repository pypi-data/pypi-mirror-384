# FEATURE: Kusto Cluster Connectivity and Schema Discovery

**Feature Owner**: Core Infrastructure  
**Status**: Production Ready  
**Version**: 2.0+

## Overview

Provides robust connectivity to Azure Data Explorer (Kusto) clusters with dynamic schema discovery, authentication management, and intelligent caching. This is the foundational feature enabling all Kusto operations in the MCP server.

## Purpose

Enable AI agents to:
- Connect to real Kusto clusters with proper authentication
- Discover tables dynamically without pre-loading metadata
- Fetch table schemas on-demand (lazy loading)
- Cache schema information for performance
- Handle various cluster name formats (short names, full domains)

## Architecture

### Components

1. **KustoConnectionManager** (`src/utils/kusto_client.py`)
   - Manages connections to multiple clusters
   - Handles authentication (Azure CLI, Managed Identity, Device Code)
   - Supports cluster name resolution (short → full domain)
   - Provides connection pooling and reuse

2. **SchemaCacheService** (`src/services/schema_cache_service.py`)
   - Lazy-loading schema cache with TTL
   - LRU eviction for memory management
   - Per-table caching with automatic expiration
   - Cache hit/miss tracking

3. **SmartTableDiscovery** (`src/tools/table_discovery.py`)
   - Dynamic table discovery from clusters
   - Searches across all configured clusters
   - Integrates with schema cache for enriched results
   - LRU caching for search results

### Authentication Chain

The server tries authentication methods in order:

1. **Azure CLI** (preferred for local development)
   - Uses `az login` credentials
   - Fast and reliable for human users
   
2. **Managed Identity** (for Azure-hosted deployments)
   - Automatic authentication in Azure environments
   - No credential management needed
   
3. **Device Code Flow** (fallback for interactive scenarios)
   - Provides URL and code for browser authentication
   - Last resort for user authentication

## Configuration

### Connection Strings

File: `cache/connection_strings.json`

```json
{
  "clusters": [
    {
      "name": "azcore",
      "url": "azcore.centralus.kusto.windows.net"
    },
    {
      "name": "gandalf",
      "url": "gandalfdeepad.westus2.kusto.windows.net"
    }
  ]
}
```

**Important**: This file is git-ignored. Each user/deployment needs their own copy.

### Schema Cache Settings

File: `src/core/config.json`

```json
{
  "cache": {
    "schema_cache_size": 500,
    "schema_cache_ttl_hours": 24,
    "enable_persistent_cache": true,
    "cache_directory": "cache"
  }
}
```

## Usage

### Connecting to a Cluster

```python
from src.utils.kusto_client import get_connection_manager

# Get connection manager (singleton)
conn_mgr = get_connection_manager()

# Get client for specific cluster/database
client = conn_mgr.get_client("azcore", "Fa")

# Execute query
results, columns = await client.execute_query(
    "WireserverHeartbeatEtwTable | take 10"
)
```

### Discovering Tables

```python
from src.tools.table_discovery import create_smart_table_discovery

# Create discovery service
discovery = create_smart_table_discovery()

# Search tables across all configured clusters
results = await discovery.search_tables(
    query="heartbeat",
    method="hybrid",
    limit=10,
    fetch_schema=True  # Include schema in results
)

# Results include:
# - cluster, database, table names
# - search relevance scores
# - schema information (columns, types, time columns, etc.)
```

### Fetching Schema

```python
from src.services.schema_cache_service import get_schema_cache_service

# Get schema cache (singleton)
schema_cache = get_schema_cache_service()

# Fetch schema (uses cache if available)
schema = await schema_cache.get_schema(
    cluster="azcore",
    database="Fa", 
    table="WireserverHeartbeatEtwTable",
    fetch_if_missing=True
)

# Schema includes:
# - columns: List[Dict] with name and type
# - time_columns: List[str] of datetime columns
# - primary_time_column: str (best column for time filtering)
# - numeric_columns: List[str]
# - string_columns: List[str]
```

## Key Features

### Cluster Name Resolution

Supports multiple input formats:
- Short name: `"azcore"` → `"azcore.centralus.kusto.windows.net"`
- Full domain: `"azcore.centralus.kusto.windows.net"` → used as-is
- URL with https: `"https://azcore.centralus.kusto.windows.net"` → extracted

### Error Handling

Provides actionable error messages:
```
Failed to fetch schema: Authentication failed

Troubleshooting:
1. Run 'az login' to authenticate with Azure CLI
2. Check your account has Data Reader permissions on the cluster
3. Verify network connectivity to the cluster
4. Check if the cluster URL is correct
```

### Performance Optimization

- **Schema caching**: 10ms cached lookups vs 1-2s fresh fetches
- **Connection pooling**: Reuses Kusto client instances
- **Lazy loading**: Only fetches schema when actually needed
- **Search result caching**: 30-minute TTL for repeated searches

## Changes

### Version 2.0.1 (2025-10-14) - Production Readiness

**Fixed critical connectivity issues**:
- Fixed connection string parsing to handle `name`/`url` format (was expecting `cluster_name`/`connection_string`)
- Added cluster name resolution for short names and full domains
- Fixed URL construction in `RealKustoClient.__init__()` to handle various input formats
- Updated table discovery to load configured clusters instead of defaulting to mock cluster
- Enhanced error messages with troubleshooting hints for common issues

**Result**: Server can now connect to real Kusto clusters and discover tables dynamically.

### Version 2.0.3 (2025-10-14) - Schema Enrichment

**Fixed schema integration in search**:
- Fixed `SchemaMetadata` attribute access in `search_tables()` method
- Changed from dictionary-style `.get()` to direct attribute access
- Added `string_columns` and `time_columns` to search results for completeness

**Result**: Table search now correctly enriches results with schema information.

## Related Features

- **Query Handle System** (`FEATURE_query_handle_system.md`) - Uses schema cache for validation
- **Anti-Hallucination** - Validates all table/column references against schema
- **Table Search** - Integrates schema fetching for enriched results

## Troubleshooting

### "Authentication failed"
**Solution**: Run `az login` and ensure you're authenticated to Azure

### "Cluster not found"
**Solution**: Check `cache/connection_strings.json` has correct cluster configuration

### "No tables loaded"
**Solution**: Verify cluster connectivity and database permissions

### "Schema cache miss rate high"
**Solution**: Increase `schema_cache_ttl_hours` in config if queries repeat frequently

## Performance Metrics

Typical performance (v2.0.3+):
- Connection establishment: 100-500ms (first time), <10ms (cached)
- Database list: 1-2s (51 databases)
- Table list per database: 50-200ms (varies by table count)
- Schema fetch: 1-2s (first time), <10ms (cached)
- Table search: 50-100ms (cached cluster metadata)

## Future Enhancements

- Connection health monitoring and automatic reconnection
- Parallel database/table discovery for faster startup
- Schema diff detection for cache invalidation
- Connection string validation on startup
- Support for Azure AD service principal authentication
