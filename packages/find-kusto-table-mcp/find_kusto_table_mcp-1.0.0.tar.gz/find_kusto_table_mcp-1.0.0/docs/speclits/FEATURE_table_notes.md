# Feature: Table Notes System

## Overview

The Table Notes System enables agents to add persistent contextual notes to Kusto tables. These notes are stored separately from the schema cache and are included in all table searches and details, allowing agents to learn and share workflow-specific context over time.

## Use Cases

### 1. Workflow Documentation
Agents can document specific patterns and best practices:
```
"Always filter by TimeGenerated > ago(7d) for performance"
"Use Region='WestUS' first to reduce query time"
```

### 2. Data Quality Awareness
Record known data issues:
```
"Location column is often null for records before 2023-01-01"
"Status field changed format on 2024-06-15"
```

### 3. Business Context
Share domain knowledge:
```
"This table tracks production deployments for Azure VMs"
"Used by monitoring team for incident response"
```

### 4. Performance Tips
Save optimization insights:
```
"Query runs faster when filtering by ContainerId before TimeGenerated"
"Aggregations work best with 5-minute bins on this table"
```

## Architecture

### Storage
- **Notes File**: `cache/table_notes.json` - Persistent storage separate from schema cache
- **In-Memory**: Notes loaded at startup and kept in `SchemaCacheService.table_notes` dictionary
- **Persistence**: Automatically saved when notes are added

### Data Structure

**SchemaMetadata** (enhanced):
```python
@dataclass
class SchemaMetadata:
    # ... existing fields ...
    notes: List[Dict[str, Any]] = None  # User-added context notes
```

**Note Entry**:
```json
{
  "note": "Always filter by Region first for performance",
  "category": "performance",
  "added_at": "2025-10-15T13:00:00.000000",
  "table_path": "cluster.database.table"
}
```

### Categories
- `workflow`: Workflow-specific patterns and usage
- `usage`: General usage guidelines and tips
- `schema`: Schema-related notes and gotchas
- `performance`: Performance optimization tips
- `general`: Uncategorized notes

## API

### Add Note
```python
@mcp.tool()
async def add_table_note(
    cluster: str,
    database: str,
    table: str,
    note: str,
    category: str = "general",
    ctx: Context = None
) -> str
```

**Example**:
```python
add_table_note(
    cluster="azcore",
    database="kusto",
    table="ActivityLog",
    note="Always filter by SubscriptionId for better performance",
    category="performance"
)
```

### Get Notes
```python
@mcp.tool()
async def get_table_notes(
    cluster: str,
    database: str,
    table: str,
    ctx: Context = None
) -> str
```

**Example**:
```python
get_table_notes(
    cluster="azcore",
    database="kusto",
    table="ActivityLog"
)
```

## Integration Points

### 1. Table Search
Notes are included in search results when `fetch_schema=True`:
```json
{
  "table": "ActivityLog",
  "cluster": "azcore",
  "database": "kusto",
  "notes": [
    {
      "note": "Always filter by SubscriptionId",
      "category": "performance",
      "added_at": "2025-10-15T13:00:00"
    }
  ]
}
```

### 2. Table Details
Notes are included in `get_table_details()` results:
```json
{
  "table_path": "azcore.kusto.ActivityLog",
  "schema": { ... },
  "notes": [ ... ],
  "metadata": { ... }
}
```

### 3. Schema Cache
Notes are automatically attached when schemas are fetched:
- Loaded from persistent storage on startup
- Merged with cached schema metadata
- Included in all schema lookups

## Implementation Details

### SchemaCacheService Methods

**add_note()**:
1. Creates note entry with timestamp and metadata
2. Adds to in-memory `table_notes` dictionary
3. Updates cached schema if present
4. Saves to persistent storage

**get_notes()**:
1. Returns all notes for a table from in-memory storage
2. Returns empty list if no notes exist

**_load_notes()**:
1. Called during service initialization
2. Loads notes from `cache/table_notes.json`
3. Populates `table_notes` dictionary

**_save_notes()**:
1. Saves all notes to `cache/table_notes.json`
2. Includes version and timestamp metadata

### Schema Integration
When fetching schema:
```python
schema_metadata = SchemaMetadata(
    # ... other fields ...
    notes=self.table_notes.get(cache_key, [])
)
```

## Benefits

### For Agents
- **Learn over time**: Each interaction can add context
- **Avoid mistakes**: Learn from previous issues documented in notes
- **Better queries**: Use documented patterns and optimizations
- **Faster onboarding**: New agents inherit knowledge from previous sessions

### For Users
- **Knowledge sharing**: Team insights captured automatically
- **Persistent memory**: Context doesn't reset between sessions
- **Better results**: Agents make more informed decisions
- **Documentation**: Automatic documentation of tribal knowledge

## Future Enhancements

### Possible Improvements
1. **Note editing/deletion**: Ability to update or remove notes
2. **Note search**: Search across all notes for specific keywords
3. **Note prioritization**: Flag important notes for prominence
4. **Note validation**: Automatic detection of outdated notes
5. **Note suggestions**: AI-generated note recommendations based on query patterns
6. **Note sharing**: Export/import notes between environments
7. **Note analytics**: Track which notes are most helpful

### Versioning
Consider adding note versioning:
```json
{
  "note": "New best practice",
  "version": 2,
  "supersedes": "old-note-id",
  "added_at": "2025-10-15T13:00:00"
}
```

## Testing

### Unit Tests
- Test note addition and retrieval
- Test persistence (save/load)
- Test integration with schema cache
- Test search result enrichment

### Integration Tests
- Test full workflow: add note → search table → verify note in results
- Test server restart: notes persist across restarts
- Test concurrent note additions

## Example Workflow

```python
# Agent discovers a performance pattern
add_table_note(
    cluster="azcore",
    database="kusto",
    table="ActivityLog",
    note="Filtering by SubscriptionId before TimeGenerated reduces query time by 80%",
    category="performance"
)

# Later, another agent searches for the table
results = search_kusto_tables(query="activity log", fetch_schema=True)

# Results include the note:
# {
#   "table": "ActivityLog",
#   "notes": [
#     {
#       "note": "Filtering by SubscriptionId before...",
#       "category": "performance"
#     }
#   ]
# }

# Agent applies the learned pattern
query = """
ActivityLog
| where SubscriptionId == @subscriptionId
| where TimeGenerated > ago(1h)
| summarize count() by Status
"""
```

## Configuration

Notes are automatically enabled when schema cache is initialized. No additional configuration required.

**Files**:
- `cache/table_notes.json` - Notes storage (git-ignored)
- `src/services/schema_cache_service.py` - Implementation
- `src/tools/table_discovery.py` - Integration with search
- `kusto_server.py` - MCP tool definitions

## Migration

No migration needed. Notes feature is additive:
- Existing functionality unchanged
- Notes are optional (empty list by default)
- Backward compatible with existing caches
