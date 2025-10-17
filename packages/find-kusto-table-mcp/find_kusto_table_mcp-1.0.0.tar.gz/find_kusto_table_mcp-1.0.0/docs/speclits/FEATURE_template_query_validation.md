# Feature: Template Query Validation

## Overview

Templates now validate KQL query syntax before saving by executing queries with sample parameter values. This prevents invalid queries from being saved as templates and catches syntax errors early in the workflow creation process.

## Problem Statement

Previously, templates could be created with syntactically invalid KQL queries. These errors would only be discovered when users tried to execute the template, leading to:
- Wasted time debugging during execution
- Poor user experience with failed templates
- Accumulation of broken templates in the system

## Solution

Added query syntax validation to both `template_create` and `template_save_confidential` tools that:
1. Generates sample parameter values based on parameter types
2. Renders the query with these sample values
3. Wraps the query in `| take 0` to check syntax without returning data
4. Executes the validation query against the target cluster/database
5. Rejects template creation if syntax errors are detected

## Implementation Details

### New Method: `validate_query_syntax`

Added to `QueryTemplateService` class in `src/services/query_template_service.py`:

```python
def validate_query_syntax(
    self,
    query: str,
    parameters: List[QueryParameter],
    cluster: str,
    database: str,
    connection_manager: Any
) -> tuple[bool, str]:
    """
    Validate query syntax by executing it with sample parameter values.
    Uses 'take 0' to check syntax without returning data.
    
    Returns:
        (is_valid, error_message)
    """
```

**Key Features:**
- **Smart parameter value generation**: Provides sensible defaults for each parameter type
  - STRING: "test_value"
  - NUMBER: 0
  - DATETIME: "datetime(2024-01-01)"
  - TIMESPAN: "1h"
  - BOOLEAN: True
  - LIST: ["test"]
- **Minimal execution**: Uses `| take 0` to validate syntax without processing data
- **Error extraction**: Parses Kusto error messages to extract meaningful syntax/semantic errors
- **Graceful degradation**: If validation fails due to connection issues, allows template creation with a warning
- **Async support**: Handles both running and non-running event loops

### Tool Updates

Both `template_create` and `template_save_confidential` tools now:
1. Call `validate_query_syntax()` before saving
2. Provide user feedback via `ctx.info()` during validation
3. Return detailed error messages if validation fails
4. Prevent template creation/saving if query is invalid

## Usage Examples

### Valid Query - Success
```python
template_create(
    name="error_count_analysis",
    description="Count errors by node",
    query="ErrorTable | where Timestamp > ago({timespan}) | summarize count() by NodeId",
    parameters=[{
        "name": "timespan",
        "type": "timespan",
        "description": "Time range",
        "default_value": "1h"
    }],
    cluster="azcore",
    database="AtScale"
)
```
**Result:** ✅ Query validated, template created

### Invalid Query - Rejection
```python
template_create(
    name="broken_query",
    description="Query with syntax error",
    query="NonExistentTable | where BadOperator >> ago({timespan})",
    parameters=[{
        "name": "timespan",
        "type": "timespan",
        "description": "Time range",
        "default_value": "1h"
    }],
    cluster="azcore",
    database="AtScale"
)
```
**Result:** ❌ Validation failed with error message, template not created

## Benefits

1. **Early Error Detection**: Catch syntax errors during template creation, not execution
2. **Better User Experience**: Clear error messages help users fix queries before saving
3. **Template Quality**: Ensures only valid queries are saved as templates
4. **Time Savings**: Reduces debugging time during template execution
5. **System Integrity**: Prevents accumulation of broken templates

## Error Handling

### Connection Failures
If validation fails due to connection issues (cluster unavailable, auth problems), the system:
- Logs a warning
- Allows template creation to proceed
- Returns a warning message to the user

This prevents connectivity issues from blocking legitimate template creation.

### Syntax/Semantic Errors
If validation fails due to query syntax or semantic errors:
- Extraction of meaningful error from Kusto response
- Clear error message returned to user
- Template creation is blocked
- User can fix query and retry

## Testing

Added comprehensive test suite in `tests/test_template_query_validation.py`:
- Valid query validation
- Invalid query rejection
- Multiple parameter handling
- Connection failure scenarios
- Query rendering failures

## Performance Impact

- **Validation Time**: Adds 1-2 seconds per template creation (one-time cost)
- **Network Cost**: One lightweight query per template (`take 0` returns no data)
- **Trade-off**: Small upfront cost prevents larger costs during execution failures

## Future Enhancements

Potential improvements:
1. Cache validation results for identical queries
2. Add option to skip validation for trusted sources
3. Provide query suggestions when validation fails
4. Validate against table schema (column existence checks)

## Related Documentation

- `docs/TEMPLATE_EXECUTE_GUIDE.md` - Template execution workflow
- `src/services/query_template_service.py` - Core template service
- `src/mcp_tools/templates.py` - Template management tools
