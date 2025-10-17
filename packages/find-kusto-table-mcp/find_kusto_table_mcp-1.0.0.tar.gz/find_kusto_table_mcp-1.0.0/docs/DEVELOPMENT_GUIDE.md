# Development Guide

## Setup Instructions

### Prerequisites
- Python 3.8+
- Access to Kusto clusters (for production use)
- Git

### Quick Setup
```bash
# Clone repository
git clone https://github.com/AmeliaRose802/find-kusto-table-mcp.git
cd find-kusto-table-mcp

# Install dependencies
pip install -r requirements.txt

# Configure clusters
mkdir -p cache
cp connection_strings.json.example cache/connection_strings.json
# Edit cache/connection_strings.json with your cluster details

# Build search index
python scripts/build_metadata.py

# Start enhanced server
python src/enhanced_mcp_server.py
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ --cov=src --cov-report=html

# Code quality checks
python -m flake8 src/
python -m mypy src/

# Performance benchmarks
python -m pytest benchmarks/ -v
```

## Project Structure

```
src/
├── core/                           # Core infrastructure
│   ├── config.py                  # Configuration management
│   ├── exceptions.py              # Custom exception hierarchy  
│   ├── logging_config.py          # Structured logging setup
│   └── performance.py             # Performance monitoring
├── services/                       # Business logic services
│   ├── query_handle_service.py    # Query result caching with handles
│   ├── schema_cache_service.py    # Smart schema caching with TTL
│   ├── query_template_service.py  # Reusable parameterized queries
│   └── kql_query_builder_service.py # Validated query building
├── tools/                          # High-level tools
│   ├── table_discovery.py         # Enhanced table search with caching
│   └── query_sampler.py           # Query validation and sampling
├── utils/                          # Shared utilities
│   ├── anti_hallucination.py      # Hallucination prevention
│   ├── kusto_client.py            # Mock Kusto client (replace in prod)
│   └── helpers.py                 # Common utility functions
└── enhanced_mcp_server.py         # Main MCP server implementation
```

## Development Workflow

### Adding New Features
1. **Design Phase**
   - Review existing patterns in codebase
   - Ensure anti-hallucination safeguards are considered
   - Plan performance monitoring integration

2. **Implementation Phase**
   - Add type hints for all new functions
   - Include error handling with specific exceptions
   - Add performance monitoring decorators
   - Follow existing naming conventions

3. **Testing Phase**
   - Write unit tests with >90% coverage
   - Add integration tests for MCP endpoints
   - Include performance benchmarks
   - Test error scenarios thoroughly

4. **Documentation Phase**
   - Update API documentation
   - Add usage examples
   - Update AGENT_INSTRUCTIONS.md if needed

### Code Quality Standards

#### Type Hints
```python
# Good
async def search_tables(
    query: str,
    method: str = "hybrid",
    limit: int = 10
) -> Dict[str, Any]:
    pass

# Bad  
async def search_tables(query, method="hybrid", limit=10):
    pass
```

#### Error Handling
```python
# Good
from src.core.exceptions import ValidationError, SchemaError

def validate_table(cluster: str, database: str, table: str) -> bool:
    try:
        # validation logic
        return True
    except KeyError as e:
        raise ValidationError(f"Invalid table reference: {e}")
    except Exception as e:
        raise SchemaError(f"Schema validation failed: {e}")

# Bad
def validate_table(cluster, database, table):
    try:
        # validation logic
        return True
    except:
        return False
```

#### Performance Monitoring
```python
# Good
from src.core.performance import measure_operation

async def expensive_operation(data: List[str]) -> Dict[str, Any]:
    with measure_operation("expensive_operation", {"data_size": len(data)}):
        # operation logic
        return result

# Bad
async def expensive_operation(data):
    # operation logic with no monitoring
    return result
```

#### Logging
```python
# Good
from src.core.logging_config import get_logger

logger = get_logger("component_name")

def process_data(data: Dict[str, Any]) -> None:
    logger.info(f"Processing {len(data)} items")
    try:
        # processing logic
        logger.debug("Processing completed successfully")
    except Exception as e:
        logger.error(f"Processing failed: {e}")

# Bad
import logging

def process_data(data):
    print(f"Processing {len(data)} items")  # Don't use print
    # processing logic
```

## Testing Guidelines

### Unit Tests
```python
import pytest
from src.services.schema_cache_service import SchemaCacheService

class TestSchemaCacheService:
    
    @pytest.fixture
    def cache_service(self):
        return SchemaCacheService(max_cache_size=10)
    
    async def test_cache_hit(self, cache_service):
        # Test cache hit scenario
        pass
    
    async def test_cache_miss(self, cache_service):
        # Test cache miss scenario
        pass
    
    async def test_cache_expiration(self, cache_service):
        # Test TTL expiration
        pass
```

### Integration Tests
```python
import pytest
from src.enhanced_mcp_server import EnhancedKustoMCPServer

class TestMCPServerIntegration:
    
    @pytest.fixture
    async def server(self):
        server = EnhancedKustoMCPServer()
        yield server
        # cleanup
    
    async def test_search_tables_tool(self, server):
        # Test complete MCP tool workflow
        pass
```

### Performance Tests
```python
import pytest
import time

@pytest.mark.performance
async def test_search_performance():
    start = time.perf_counter()
    # operation
    duration = time.perf_counter() - start
    assert duration < 0.1  # Must complete in <100ms
```

## Debugging

### Common Issues

#### Import Errors
- Ensure `src/` is in Python path
- Check for circular imports
- Verify all `__init__.py` files exist

#### Schema Validation Failures
- Check if table exists in search index
- Verify connection string configuration
- Test with mock data first

#### Performance Issues
- Check performance monitoring logs
- Profile with built-in performance tools
- Verify cache hit rates

### Debugging Tools

#### Performance Profiling
```python
from src.core.performance import get_performance_summary, get_operation_stats

# Get overall performance summary
summary = get_performance_summary()
print(f"Cache hit rate: {summary['cache_stats']['hit_rate_percent']}%")

# Get specific operation stats
stats = get_operation_stats("search_tables")
print(f"Average duration: {stats['avg_duration_ms']}ms")
```

#### Logging Configuration
```python
from src.core.logging_config import setup_logging

# Enable debug logging
setup_logging(level="DEBUG", enable_performance_logs=True)
```

## Deployment

### Production Considerations
- Replace mock Kusto client with real Azure Data Explorer client
- Configure proper authentication and authorization
- Set up monitoring and alerting
- Configure log aggregation
- Implement proper secret management

### Configuration Management
- Use environment variables for sensitive configuration
- Validate configuration on startup
- Provide clear error messages for misconfigurations

### Health Checks
- Implement health check endpoints
- Monitor cache hit rates and performance
- Alert on error rate thresholds
- Track resource usage patterns