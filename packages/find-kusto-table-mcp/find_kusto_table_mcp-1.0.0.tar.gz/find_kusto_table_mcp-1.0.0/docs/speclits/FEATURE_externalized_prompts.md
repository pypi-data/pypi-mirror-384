# FEATURE: Externalized Prompt Management

**Status**: ✅ Implemented  
**Date**: 2025-10-15  
**Category**: Architecture / Code Quality

## Overview

All MCP prompts have been moved from hardcoded Python strings to external markdown files in the `prompts/` directory. This improves maintainability, version control, and allows non-programmers to improve prompt content.

## Problem

Previously, all prompts were hardcoded directly in `kusto_server.py`:

```python
@mcp.prompt()
def prompt_find_and_query_table(query_description: str) -> str:
    """Generate a prompt for finding and querying tables"""
    return f"""I need to find and query Kusto tables. Here's what I'm looking for:

{query_description}

Please help me:
1. Search for relevant tables using search_kusto_tables
...
"""
```

**Issues:**
- Prompts mixed with code logic
- Hard to maintain and version control
- Changes require code deployment
- Non-programmers can't improve prompts
- Difficult to test independently

## Solution

### 1. Created `prompts/` Directory Structure

```
prompts/
├── README.md                          # Documentation
├── find_and_query_table.md            # Simple query guidance
├── create_workflows_from_docs.md      # Workflow extraction
└── discover_and_build_workflows.md    # Comprehensive discovery
```

### 2. Created Prompt Loader Utility

**File**: `src/utils/prompt_loader.py`

```python
def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from a markdown file."""
    # Loads from prompts/{prompt_name}.md
    # Caches for performance

def format_prompt(prompt_name: str, **kwargs) -> str:
    """Load and format a prompt with parameters."""
    template = load_prompt(prompt_name)
    return template.format(**kwargs)

def list_available_prompts() -> list[str]:
    """List all available prompt templates."""
```

### 3. Updated Server to Load Prompts

```python
from src.utils.prompt_loader import format_prompt, load_prompt

@mcp.prompt()
def prompt_find_and_query_table(query_description: str) -> str:
    """Generate a prompt for finding and querying tables"""
    return format_prompt("find_and_query_table", query_description=query_description)

@mcp.prompt()
def prompt_create_workflows_from_docs() -> str:
    """..."""
    return load_prompt("create_workflows_from_docs")
```

## Benefits

### ✅ Better Maintainability
- Prompts are separate from code logic
- Easy to find and edit
- Clear separation of concerns

### ✅ Version Control
- Track prompt changes independently
- Easy to review prompt improvements
- Revert problematic changes easily

### ✅ Collaboration
- Non-programmers can improve prompts
- Subject matter experts can contribute
- No Python knowledge required

### ✅ Testing
- Prompts can be tested independently
- Validate parameter substitution
- Check for missing placeholders

### ✅ Performance
- Prompts are cached after first load
- No repeated file I/O
- Fast access after initial load

## Prompt Format

Prompts use Python's `str.format()` syntax for parameters:

```markdown
I need to find and query Kusto tables. Here's what I'm looking for:

{query_description}

Please help me:
1. Search for relevant tables using search_kusto_tables
...
```

Parameters are replaced at runtime:

```python
result = format_prompt("find_and_query_table", query_description="Find errors")
# Result: "I need to find... Find errors ... Please help me..."
```

## Usage Examples

### Loading a Simple Prompt

```python
from src.utils.prompt_loader import load_prompt

# Load without formatting
prompt_text = load_prompt("analyze_query_results")
```

### Formatting with Parameters

```python
from src.utils.prompt_loader import format_prompt

# Load and format in one step
result = format_prompt(
    "find_and_query_table",
    query_description="Find error logs from last 24h"
)
```

### In MCP Server

```python
@mcp.prompt()
def prompt_my_feature(param: str) -> str:
    """Description"""
    return format_prompt("my_feature", param=param)
```

## Testing

Created comprehensive test suite in `tests/test_prompt_loader.py`:

```python
def test_format_prompt_with_params():
    """Test formatting prompt with parameters."""
    result = format_prompt(
        "find_and_query_table",
        query_description="Find error logs"
    )
    assert "Find error logs" in result
    assert "{query_description}" not in result  # Replaced
```

**All 8 tests pass** ✅

## Migration Checklist

- [x] Create `prompts/` directory
- [x] Move all 4 prompts to markdown files
- [x] Create `src/utils/prompt_loader.py`
- [x] Update `kusto_server.py` to load prompts
- [x] Add comprehensive tests
- [x] Update copilot instructions
- [x] Document in CHANGELOG
- [x] Create this speclit
- [x] Verify server starts correctly
- [x] All tests pass

## Best Practices (Added to Copilot Instructions)

1. **NEVER hardcode prompts** in Python code
2. **ALWAYS store prompts** in `prompts/` directory
3. **Use descriptive filenames**: `my_feature_name.md`
4. **Use `{parameter}` syntax** for placeholders
5. **Keep prompts readable** and well-formatted
6. **Test after changes** using test suite

## Files Changed

### Created
- `prompts/find_and_query_table.md`
- `prompts/create_workflows_from_docs.md`
- `prompts/discover_and_build_workflows.md`
- `prompts/README.md`
- `src/utils/prompt_loader.py`
- `tests/test_prompt_loader.py`
- `docs/speclits/FEATURE_externalized_prompts.md` (this file)

### Modified
- `kusto_server.py` - Updated to load prompts from files
- `.github/copilot-instructions.md` - Added prompt management section
- `docs/CHANGELOG.md` - Documented the change

## Future Improvements

1. **Prompt Validation**: Add linting for markdown prompts
2. **Parameter Schema**: Validate parameter names match usage
3. **Localization**: Support multiple languages
4. **Prompt Versioning**: Track prompt versions for A/B testing
5. **Hot Reload**: Reload prompts without server restart (for development)

## Related Documentation

- `prompts/README.md` - Prompt directory documentation
- `.github/copilot-instructions.md` - Developer guidelines
- `tests/test_prompt_loader.py` - Test suite

## Impact

- **Code Quality**: ⬆️ Improved separation of concerns
- **Maintainability**: ⬆️ Easier to update prompts
- **Collaboration**: ⬆️ Non-programmers can contribute
- **Testing**: ⬆️ Better test coverage
- **Performance**: ✔️ Cached loading, no impact
