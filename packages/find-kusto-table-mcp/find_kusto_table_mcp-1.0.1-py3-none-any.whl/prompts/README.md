# MCP Prompts Directory

This directory contains all prompt templates for the Kusto MCP server. Prompts are stored as markdown files and loaded dynamically by the server.

## Why Markdown Files?

- **Version Control**: Track changes to prompts over time
- **Maintainability**: Easy to edit without touching Python code
- **Separation of Concerns**: Keep prompt content separate from logic
- **Collaboration**: Non-programmers can improve prompts
- **Testing**: Can be tested independently of code

## Structure

Each prompt is a `.md` file with:
- Clear, descriptive filename (e.g., `find_and_query_table.md`)
- Parameter placeholders using `{parameter_name}` syntax
- Well-formatted, readable content

## Available Prompts

### � Workflow Discovery

- **`discover_and_build_workflows.md`** - Discover queries across multiple sources and build workflow templates
  - MCP Tool: `prompt_discover_and_build_workflows(sources, cluster="", database="")`
  - **Use When**: You want to find ALL queries across workspace/directories/repos
  - **Input**: Directories, multiple files, entire repositories
  - **Best For**: Large-scale workflow discovery and organization
  - Systematically extracts KQL queries, identifies parameters, and creates reusable templates

## Usage

### Loading a Prompt

```python
from src.utils.prompt_loader import load_prompt

# Load prompt without formatting
prompt_text = load_prompt("find_and_query_table")
```

### Formatting with Parameters

```python
from src.utils.prompt_loader import format_prompt

# Load and format in one step
result = format_prompt(
    "find_and_query_table",
    query_description="Find error logs"
)
```

### In MCP Server

```python
@mcp.prompt()
def prompt_my_feature(param: str) -> str:
    """Description of the prompt"""
    return format_prompt("my_feature", param=param)
```

## Best Practices

1. **Naming**: Use snake_case, descriptive names
2. **Parameters**: Use `{parameter_name}` for dynamic content
3. **Formatting**: Keep markdown clean and readable
4. **Documentation**: Add comments explaining complex prompts
5. **Testing**: Test prompts after changes

## CRITICAL RULE

**NEVER hardcode prompts in Python code!** All prompts must be stored as markdown files in this directory and loaded using `src/utils/prompt_loader.py`.
