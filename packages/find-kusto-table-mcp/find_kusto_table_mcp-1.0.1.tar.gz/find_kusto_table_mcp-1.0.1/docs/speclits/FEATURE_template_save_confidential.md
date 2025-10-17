# FEATURE: template_save_confidential Tool

**Date**: October 15, 2025  
**Issue**: AI agents confused about how to create confidential templates with proper metadata  
**Status**: ✅ Implemented

## Problem Description

Users (AI agents) were trying to use `template_create` with complex JSON structures containing full metadata, leading to validation errors:

```
Input validation error: 'cluster' is a required property
```

### Root Causes

1. **Two workflows, unclear distinction**: 
   - Simple templates → `template_create` (memory only)
   - Complex/confidential templates → Save JSON to `cache/templates/` (persisted to disk)

2. **No tool for confidential templates**: Users had to manually create JSON files, which AI agents struggled with

3. **Documentation showed JSON examples** but didn't explain how to save them programmatically

4. **User confusion**: Agent provided complete JSON structure but tried to call `template_create` instead of saving to file

### User's Attempted JSON

The user (AI agent) created a perfect template structure:
```json
{
  "name": "wireserver_troubleshooting_first_steps",
  "description": "Comprehensive WireServer troubleshooting...",
  "query": "// Multi-step KQL workflow...",
  "parameters": [...],
  "tags": ["wireserver", "troubleshooting", ...]
}
```

But tried to pass it to `template_create`, which expects individual parameters, not a JSON blob.

## Solution: New `template_save_confidential` Tool

Created a new MCP tool that accepts complete template JSON and saves it to `cache/templates/`:

### Tool Signature

```python
@mcp.tool()
def template_save_confidential(
    template_json: Dict[str, Any],
    filename: str = None,
    ctx: Context = None
) -> str:
    """
    🔒 Save a confidential workflow template to cache/templates/ directory.
    
    Use this when creating complex multi-step troubleshooting workflows from documentation
    that contain confidential query patterns. Templates saved here are automatically loaded
    on server startup and available through workflow_list and template_execute.
    """
```

### What It Does

1. **Validates required fields**: name, description, query, parameters, metadata
2. **Validates metadata**: Ensures cluster and database are present
3. **Marks as confidential**: Automatically adds `metadata.confidential = true`
4. **Saves to disk**: Writes JSON to `cache/templates/{name}.json`
5. **Loads immediately**: Creates template in memory so it's available right away
6. **Returns confirmation**: Shows success, filepath, and cluster/database info

### Key Features

#### Validation
```python
# Check required fields
required_fields = ["name", "description", "query", "parameters", "metadata"]
missing = [f for f in required_fields if f not in template_json]
if missing:
    raise ToolError(f"Missing required fields: {missing}")

# Validate metadata has cluster and database
metadata = template_json.get("metadata", {})
if "cluster" not in metadata or "database" not in metadata:
    raise ToolError(
        "Template metadata must include 'cluster' and 'database' fields. "
        f"Current metadata: {metadata}"
    )
```

#### Automatic Confidential Marking
```python
# Mark as confidential if not already set
if "confidential" not in metadata:
    metadata["confidential"] = True
    template_json["metadata"] = metadata
```

#### Immediate Loading
```python
# Load into memory immediately (don't wait for restart)
params = [QueryParameter(...) for p in template_json["parameters"]]

success, error = templates.create_template(
    name=template_name,
    description=template_json["description"],
    query=template_json["query"],
    parameters=params,
    tags=template_json.get("tags", []),
    metadata=template_json["metadata"]
)
```

#### Helpful Response
```python
return {
    "success": True,
    "template_name": template_name,
    "filepath": str(filepath),
    "cluster": metadata.get("cluster"),
    "database": metadata.get("database"),
    "note": "Template saved to disk and loaded into memory. Available via workflow_list and template_execute."
}
```

## Usage Comparison

### Before: Manual File Creation (Confusing)

```python
# AI agent had to do this manually - NOT PROVIDED AS A TOOL!
import json
with open("cache/templates/wireserver_workflow.json", "w") as f:
    json.dump(template_data, f)

# Then tell user to restart server to load it
# Very confusing workflow!
```

### After: Use `template_save_confidential` Tool

```python
# AI agent calls tool with complete JSON
template_save_confidential(
    template_json={
        "name": "wireserver_troubleshooting_first_steps",
        "description": "Comprehensive WireServer troubleshooting...",
        "query": "// Multi-step workflow...",
        "parameters": [
            {
                "name": "node_id",
                "type": "string",
                "description": "Node ID to analyze",
                "required": true
            }
        ],
        "metadata": {
            "cluster": "azcore",
            "database": "Fa"
        },
        "tags": ["wireserver", "troubleshooting"]
    }
)

# ✅ Saved to disk
# ✅ Loaded into memory immediately
# ✅ Available via workflow_list and template_execute
```

## Clear Workflow Distinction

Updated documentation to make the distinction crystal clear:

### Simple Templates (Non-Confidential)
**Use `template_create`**:
- Individual parameters (not JSON blob)
- Stored in memory only
- Good for: Simple queries, non-confidential data
- Example:
  ```python
  template_create(
      name="error_count",
      description="Count errors in timespan",
      query="Errors | where Timestamp > ago({window}) | count",
      parameters=[{"name": "window", "type": "timespan", "description": "Time window"}],
      cluster="azcore",
      database="AtScale",
      tags=["monitoring"]
  )
  ```

### Complex Workflows (Confidential)
**Use `template_save_confidential`**:
- Complete JSON structure
- Saved to disk + loaded into memory
- Auto-loads on server restart
- Good for: Multi-step troubleshooting, confidential patterns
- Example: (See above)

## Updated Prompt Documentation

Updated `prompt_create_workflows_from_docs` to explain the two workflows:

```
🔧 **Tool Call Sequence:**

1. `read_file("path/to/docs.md")` - Load documentation
2. *[Analyze and extract workflows]*
3. **FOR SIMPLE/NON-CONFIDENTIAL QUERIES:**
   - Use `template_create(name, description, query, parameters, cluster, database, tags)`
   - Templates stored in memory only
4. **FOR COMPLEX/CONFIDENTIAL WORKFLOWS:**
   - Build complete JSON structure with metadata
   - Use `template_save_confidential(template_json)` to save to cache/templates/
   - Templates persisted to disk and auto-loaded on server restart
   - **CRITICAL**: template_json MUST include metadata.cluster and metadata.database!
5. `workflow_list()` - Verify all templates created/loaded
```

## Testing

Created comprehensive test suite in `scripts/tmp_test/test_confidential_template_save.py`:

### Test 1: Save Confidential Template
```
✅ Template saved to disk
✅ Template loaded into memory
✅ Metadata present: cluster=azcore, database=Fa, confidential=True
✅ Template found in list with complete metadata
```

### Test 2: Metadata Validation
```
✅ Correctly detected missing cluster
✅ Correctly detected missing database
```

**All tests passed**: 2/2 ✅

## Impact

### Before Fix
```python
# AI agent creates perfect JSON structure
template_json = { "name": "...", "query": "...", ... }

# But tries to call wrong tool
template_create(...)  # ❌ Validation error - wrong parameters

# OR manually saves file (no tool available)
# ❌ Confusing, error-prone, requires restart
```

### After Fix
```python
# AI agent creates JSON structure
template_json = { 
    "name": "wireserver_workflow",
    "metadata": {"cluster": "azcore", "database": "Fa"},
    ... 
}

# Calls correct tool
template_save_confidential(template_json)
# ✅ Saved to disk
# ✅ Loaded immediately
# ✅ Ready to execute

# Execute right away (no restart needed)
template_execute(
    name="wireserver_workflow",
    parameters={...}
)
# ✅ Works perfectly
```

## User Experience Improvements

1. **Clear Tool Choice**: Two distinct tools for two use cases
2. **No Manual File Creation**: Tool handles all file I/O
3. **Immediate Availability**: No restart required
4. **Better Error Messages**: Validation explains exactly what's missing
5. **Complete Documentation**: Prompts explain when to use each tool
6. **Automatic Confidential Marking**: Sets confidential flag automatically

## Related Files

- `kusto_server.py` - New `template_save_confidential` tool
- `scripts/tmp_test/test_confidential_template_save.py` - Validation tests
- `docs/speclits/FEATURE_template_save_confidential.md` - This document

## Migration Guide for AI Agents

### Old Approach (Confusing)
```
1. Extract workflow from documentation
2. Create JSON structure manually
3. ??? How to save it ???
4. Try template_create - validation error!
5. Confusion and frustration
```

### New Approach (Clear)
```
1. Extract workflow from documentation
2. Determine: Simple or Complex?
3. IF SIMPLE:
   - Call template_create(name, description, query, parameters, cluster, database, tags)
4. IF COMPLEX/CONFIDENTIAL:
   - Build JSON with all fields
   - Call template_save_confidential(template_json)
5. Verify with workflow_list()
6. Execute with template_execute()
```

## Conclusion

This feature completes the template creation workflow by providing a proper tool for saving confidential templates. AI agents now have clear guidance on when to use each tool, and complex workflows can be saved programmatically without manual file creation.

**Status**: ✅ Implemented, tested, and documented
