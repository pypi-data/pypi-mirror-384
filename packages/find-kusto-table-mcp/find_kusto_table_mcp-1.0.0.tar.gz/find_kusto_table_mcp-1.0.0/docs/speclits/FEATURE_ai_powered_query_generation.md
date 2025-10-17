# FEATURE: AI-Powered Query Generation

**Status**: ✅ Implemented  
**Date**: 2024-01-16  
**Pattern Origin**: enhanced-ado-mcp SamplingClient

## Overview

This feature adds AI-powered KQL query generation using VS Code's Language Model API. It follows the proven pattern from enhanced-ado-mcp, using system prompts and intelligent sampling to generate queries that work on the first try.

## Architecture

### Core Components

1. **SamplingClient** (`src/utils/sampling_client.py`)
   - Wrapper for VS Code LM API through fastmcp's `ctx.sample()`
   - Methods:
     - `create_message()` - Send prompts to language model
     - `generate_query_with_ai()` - Generate KQL from natural language
     - `analyze_table_sample()` - Provide intelligent table insights
     - `refine_query()` - Fix failed queries with error feedback

2. **System Prompts** (`prompts/system/`)
   - `kql_query_generator.md` - Query generation instructions and patterns
   - `intelligent_table_sampler.md` - Table analysis and recommendations
   - `kql_query_refiner.md` - Query debugging and error correction

3. **Query Builder Integration** (`src/tools/ai_query_builder.py`)
   - Updated `build_query_from_intent()` to accept `ctx` parameter
   - AI-first generation with rule-based fallback
   - Iterative refinement (3 attempts with error feedback)

4. **Natural Language Tool** (`src/mcp_tools/natural_language_query.py`)
   - Updated `_generate_kql_from_natural_language()` to use AI
   - Falls back to rule-based heuristics if AI unavailable

## Key Features

### 1. AI-First with Fallback
```python
# Try AI first
if ctx and hasattr(ctx, 'sample'):
    result = await sampling_client.generate_query_with_ai(...)
    return result['query']

# Fall back to rule-based
logger.info("Using rule-based generation (AI unavailable)")
# ... rule-based logic ...
```

### 2. Template Variable Substitution
System prompts use `{{VARIABLE}}` syntax for dynamic content:
```markdown
**CONTEXT:**
- Cluster: {{CLUSTER}}
- Database: {{DATABASE}}
- Table: {{TABLE}}
- Schema: {{SCHEMA}}
```

Loaded with:
```python
prompt = load_system_prompt("kql_query_generator", {
    "CLUSTER": cluster_name,
    "DATABASE": database_name,
    "TABLE": table_name,
    "SCHEMA": json.dumps(schema_dict)
})
```

### 3. Iterative Refinement
Implements the 3-attempt pattern:
1. Generate initial query
2. If fails, provide error feedback and retry
3. If fails again, provide more context and retry

```python
for attempt in range(1, max_attempts + 1):
    response = await create_message(system_prompt, user_content)
    result = parse_json_response(response)
    
    if attempt >= max_attempts:
        raise QueryGenerationError(f"Failed after {max_attempts} attempts")
```

### 4. Free Models Only
Enforces free model policy:
- GPT-4o (FREE)
- GPT-4.1 (FREE)
- Copilot SWE Preview (FREE)

Never uses paid models (Claude Sonnet, GPT-4.5, etc.)

## Usage Examples

### Generate Query from Intent
```python
from src.tools.ai_query_builder import create_ai_query_builder
from fastmcp import Context

builder = create_ai_query_builder()

result = await builder.build_query_from_intent(
    cluster="myCluster",
    database="myDB",
    table="EventsTable",
    user_intent="Show me recent high severity errors in the last hour",
    ctx=ctx  # FastMCP context with sample() capability
)

print(result['query'])
# EventsTable
# | where Timestamp > ago(1h)
# | where Severity == "High"
# | take 100
```

### Natural Language to KQL
```python
@mcp.tool()
async def query_natural_language(
    question: str,
    table: str,
    ctx: Context
) -> str:
    # AI generates query based on question
    query = await _generate_kql_from_natural_language(
        request=question,
        table_name=table,
        columns=columns,
        sample_data=sample,
        ctx=ctx
    )
    return query
```

## System Prompt Design

### KQL Query Generator
**Purpose**: Generate syntactically correct KQL queries from natural language

**Key Sections**:
- Critical rules (time filtering, result limits, field names)
- Common query patterns (10 templates)
- Error prevention (common mistakes to avoid)
- Performance tips (early filtering, column projection)

**Response Format**: JSON with query, explanation, confidence

### Intelligent Table Sampler
**Purpose**: Analyze table samples and recommend queries

**Key Sections**:
- Column analysis (cardinality, data types, use cases)
- Query recommendations (grouping, filtering, aggregations)
- Data insights (patterns, characteristics)
- Performance tips (optimization suggestions)

**Response Format**: JSON with column_insights, recommended_queries, data_characteristics

### KQL Query Refiner
**Purpose**: Debug and fix failed queries

**Key Sections**:
- Common error patterns (syntax, schema, logic, performance)
- Fix examples for each error type
- Refinement process (analyze → check → apply → validate)
- Confidence levels (high/medium/low)

**Response Format**: JSON with refined_query, changes_made, error_diagnosis, confidence

## Integration Points

### 1. Query Builder
- `build_query_from_intent()` accepts optional `ctx` parameter
- Passes `ctx` to `_generate_query()` and `_refine_query()`
- Maintains backward compatibility (works without ctx)

### 2. Natural Language Tool
- `query_natural_language()` tool passes `ctx` to generation function
- AI generates queries based on user questions
- Falls back to rule-based heuristics if AI unavailable

### 3. MCP Context
- FastMCP provides `ctx` with `sample()` method
- `ctx.sample()` calls VS Code LM API
- Handles message formatting, token limits, temperature

## Error Handling

### Query Generation Failures
```python
try:
    result = await sampling_client.generate_query_with_ai(...)
    return result['query']
except Exception as e:
    logger.warning(f"AI generation failed: {str(e)}")
    # Fall back to rule-based generation
```

### JSON Parsing Failures
```python
def _parse_json_response(response_text):
    # Remove markdown code blocks
    if response_text.startswith("```"):
        # Extract JSON from ```json blocks
        ...
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise QueryGenerationError(f"Failed to parse: {str(e)}")
```

## Performance Characteristics

- **AI Query Generation**: ~2-5 seconds (depends on model)
- **Rule-Based Generation**: <100ms
- **Iterative Refinement**: ~5-15 seconds (3 attempts max)
- **Token Usage**: ~1000-4000 tokens per query generation

## Testing

Validation tests:
```bash
# Syntax validation
python -m py_compile src/utils/sampling_client.py
python -m py_compile src/tools/ai_query_builder.py
python -m py_compile src/mcp_tools/natural_language_query.py

# Import validation
python -c "from src.utils.sampling_client import SamplingClient"
python -c "from src.utils.sampling_client import load_system_prompt"
```

Unit tests needed:
- `test_sampling_client.py` - SamplingClient methods
- `test_prompt_loader.py` - System prompt loading and variable substitution
- `test_ai_query_builder.py` - AI-powered query generation
- `test_natural_language_query.py` - Natural language to KQL

## Future Enhancements

### Potential Improvements
1. **Query Explanation**: Generate natural language explanations of queries
2. **Multi-Table Queries**: Support joins across multiple tables
3. **Advanced Analytics**: Suggest statistical analyses based on data
4. **Query Optimization**: Automatically optimize slow queries
5. **Context Learning**: Learn from user corrections to improve suggestions

### Model Support
Currently supports VS Code LM API free models. Could extend to:
- Local models (Ollama, LLaMA)
- Other cloud providers (with free tier restrictions)
- Fine-tuned KQL models

## References

- Pattern Origin: [enhanced-ado-mcp SamplingClient](https://github.com/AmeliaRose802/enhanced-ado-mcp/blob/master/mcp_server/src/services/sampling-service.ts)
- VS Code LM API: FastMCP `ctx.sample()` method
- System Prompts: `prompts/system/*.md`
- Free Models Policy: `docs/speclits/POLICY_free_models_only.md`
