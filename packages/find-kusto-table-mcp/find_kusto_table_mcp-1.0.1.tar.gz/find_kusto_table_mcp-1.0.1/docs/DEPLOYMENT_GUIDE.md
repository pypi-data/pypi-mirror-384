# 🎯 Deployment & Testing Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Connections
```bash
# Copy example and edit with your Kusto clusters
cp connection_strings.json.example connection_strings.json
# Edit connection_strings.json with your cluster details
```

### 3. Run the Server
```bash
# STDIO (default for Claude Desktop)
python kusto_server.py

# HTTP server (for web access)
fastmcp run kusto_server.py --transport http --port 8000

# SSE (for streaming)
fastmcp run kusto_server.py --transport sse
```

### 4. Configure Claude Desktop

Edit your Claude config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add:
```json
{
  "mcpServers": {
    "kusto-table-search": {
      "command": "python",
      "args": ["C:\\path\\to\\cache-kusto-info\\kusto_server.py"]
    }
  }
}
```

Restart Claude Desktop.

---

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Run Specific Test Classes
```bash
# Integration tests
pytest tests/test_fastmcp_server.py -v

# Unit tests
pytest tests/test_schema_cache_service.py -v
pytest tests/test_query_handle_service.py -v
pytest tests/test_table_search.py -v
```

### Run CI Locally
```bash
# Linting
black src/ tests/ --check
isort src/ tests/ --check
flake8 src/ tests/
mypy src/

# Security
bandit -r src/
safety check
```

---

## Using the Server

### Example Queries via FastMCP Client

```python
from fastmcp.client import Client
import kusto_server

async with Client(kusto_server.mcp) as client:
    # Search for tables
    result = await client.call_tool(
        "search_kusto_tables",
        arguments={"query": "wireserver requests", "limit": 5}
    )
    
    # Sample table for query building
    schema = await client.call_tool(
        "sample_table_for_query_building",
        arguments={
            "cluster": "admeus",
            "database": "AdmeusDB",
            "table": "RequestLogs"
        }
    )
    
    # Get cache stats
    stats = await client.call_tool("cache_stats", arguments={})
    print(stats)
```

### Example Usage in Claude

```
User: Find tables related to node health monitoring

[Server searches and returns relevant tables with schemas]

User: Sample the NodeHealthEvents table to see what columns it has

[Server returns actual schema with real column names]

User: Write a query to count errors by node in the last hour

[Server uses ACTUAL column names from schema, no hallucination]
```

---

## Monitoring

### Performance Stats
```python
# Via tool
result = await client.call_tool("performance_stats", arguments={})

# Or check logs
tail -f logs/kusto_mcp.log
```

### Cache Statistics
```python
stats = await client.call_tool("cache_stats", arguments={})
print(stats)
# Shows: schema cache hits, query handles, search cache, performance metrics
```

### Prometheus Metrics (if using Docker Compose)
Visit http://localhost:9090 and query:
- `kusto_search_duration_seconds`
- `kusto_cache_hits_total`
- `kusto_cache_misses_total`

---

## Troubleshooting

### Server Won't Start
```bash
# Check Python version (3.9+ required)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for import errors
python -c "import kusto_server; print('OK')"
```

### Connection Issues
```bash
# Verify cache/connection_strings.json exists and is valid JSON
python -c "import json; json.load(open('cache/connection_strings.json'))"

# Test Kusto connectivity (if credentials configured)
python -c "from src.utils.kusto_client import get_connection_manager; print('OK')"
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -vv

# Run with debug logging
pytest tests/ -vv --log-cli-level=DEBUG

# Run specific failing test
pytest tests/test_fastmcp_server.py::TestClassName::test_name -vv
```

---

## Performance Tuning

### Cache Configuration
Edit `src/core/config.py`:
```python
DEFAULT_CONFIG = {
    "cache_ttl_hours": 24,  # Schema cache TTL
    "max_cache_size": 1000,  # Max schemas in cache
    "search_cache_ttl_minutes": 5,  # Search result cache
    "query_handle_ttl_hours": 1,  # Query handle expiration
}
```

### Concurrency
FastMCP handles concurrency automatically for local development.

---

## Development

### Project Structure
```
kusto_server.py          # Main FastMCP server
src/
  core/                  # Infrastructure
  services/              # Business logic
  tools/                 # High-level tools
  utils/                 # Utilities
tests/                   # Test suite
docs/                    # Documentation
.github/workflows/       # CI/CD
```

### Adding New Tools
```python
@mcp.tool()
async def my_new_tool(
    param: str,
    optional_param: int = 10,
    ctx: Context = None
) -> str:
    """Tool description here"""
    if ctx:
        await ctx.info(f"Processing: {param}")
    
    # Implementation
    result = do_something(param, optional_param)
    
    return safe_json_dumps(result)
```

### Running Locally During Development
```bash
# Watch mode (auto-reload on changes)
fastmcp dev kusto_server.py

# With specific transport
fastmcp dev kusto_server.py --transport http --port 8000
```

---

## Migration from Old Server

### Legacy Files
- `enhanced_mcp_server.py` - Old MCP SDK server (keep for reference)
- `mcp_table_search_server.py` - Original server (keep for reference)

### New Files
- `kusto_server.py` - **Use this for all new development**

### Key Differences
| Feature | Old (MCP SDK) | New (FastMCP) |
|---------|---------------|---------------|
| Definition | Class-based | Decorator-based |
| Schema | Manual | Automatic from types |
| Testing | Subprocess | In-memory client |
| Deployment | Manual | `fastmcp deploy` |
| Documentation | Manual | Auto-generated |

---

## Support

### Getting Help
1. Check `OVERNIGHT_ENHANCEMENTS.md` for feature overview
2. Read `README_NEW.md` for usage guide
3. Review `docs/DEVELOPMENT_GUIDE.md` for architecture
4. Check test files for usage examples

### Reporting Issues
Include:
- Python version
- FastMCP version
- Error message & stack trace
- Minimal reproduction steps

### Contributing
1. Fork repository
2. Create feature branch
3. Add tests for new features
4. Ensure CI passes
5. Submit PR with description

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Configure connections: Edit `cache/connection_strings.json`
3. ✅ Run tests: `pytest tests/ -v`
4. ✅ Start server: `python kusto_server.py`
5. ✅ Configure Claude Desktop
6. 🚀 Start querying Kusto tables safely!

---

*For questions or issues, refer to OVERNIGHT_ENHANCEMENTS.md or open an issue.*
