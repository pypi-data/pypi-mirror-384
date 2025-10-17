# Changelog

## Latest Updates (October 16, 2025)
- **Bug Fix - Chart Tool Tests**: Fixed test suite for `get_chart` tool that was causing RecursionError and IndexError due to improper mocking. Tests now use real pandas DataFrame objects with mocked query results, and minimal matplotlib mocking (only `savefig`). All 5 chart tool tests now pass.
- **Enhanced Chart Visualization**: Renamed `save_chart` to `get_chart` with dual-mode support - can return base64-encoded PNG (default) or save to file, or both simultaneously via flags (`return_base64`, `save_to_file`)

## Critical Bug Fixes (October 16, 2025)
- **Bug #1 FIXED - Flow Execution DateTime Serialization**: Fixed `flow_execute` JSON serialization error when query results contain datetime objects. Now uses `safe_json_dumps` for export instead of raw `json.dump`, properly converting datetime to ISO format strings.
- **Bug #2 FIXED - Schema Validation Tool Failure (Method Call)**: Fixed `validate_schema_claims` tool that was calling non-existent `get_table_schema()` method. Corrected to call `get_schema()` method on schema_cache service, restoring anti-hallucination validation functionality.
- **Bug #3 FIXED - Schema Validation Tool Failure (Dict Access)**: Fixed `validate_schema_claims` tool that was treating SchemaMetadata dataclass as a dict. Changed `schema['columns']` to `schema.columns` for proper attribute access. Tool now works correctly in MCP context.
- **Bug #4 FIXED - Kusto Response Parsing FrameType Error**: Fixed query execution failure with 'FrameType' error when parsing Kusto SDK responses. Improved response parsing with safer attribute access, better error handling, and index-based row access for reliability. Flow execution now works correctly with real Kusto queries.
- **Beta Test Results**: Fixed 4 critical bugs identified in beta testing, bringing tool success rate from 90.9% to 100% for fixed tools.

## Code Quality Improvements
- **Enhanced cache_management.py**:
  - Added comprehensive type hints (Dict[str, Any], Optional types)
  - Added new `cache_clear` tool for manual cache maintenance
  - Improved docstrings with usage examples and best practices
  - Added health indicators to cache_stats (healthy/warning/critical status)
  - Enhanced error handling with CacheError exception type
  - Added recommendations for low cache hit rates
- **Enhanced verification.py**:
  - Added comprehensive type hints throughout all functions
  - Improved error handling with specific exception types (ValidationError, QueryError, SchemaError)
  - Enhanced input validation for all parameters
  - Added detailed error context and metadata to exceptions
  - Improved docstrings with examples and parameter descriptions
- **Enhanced anti_hallucination.py**:
  - Added `extract_column_references` method for better KQL column detection
  - Improved `suggest_similar_columns` with multiple similarity metrics (Levenshtein distance, prefix matching, substring matching)
  - Enhanced table reference extraction to detect union, materialize, and other KQL operators
  - Better handling of KQL keywords to reduce false positives
- **Comprehensive test coverage**:
  - Expanded test_verification.py from 4 placeholder tests to 14 comprehensive unit tests
  - Added integration tests for cache_stats, cache_clear, and performance_stats
  - All tests passing (17 cache tests, 14 verification tests, 140+ total)
  - Tests cover success cases, edge cases, error conditions, and validation
- **Code standards compliance**:
  - All logger statements properly validated (no emoji in logger calls)
  - Syntax checks passing for all modified files
  - Import validation successful
  - Server starts without errors

## Verification & Trust System Added
- **Added 3 verification tools** for anti-hallucination and trust validation:
  - `verify_query_result`: Re-run queries and compare with expected results to detect changes/hallucinations
  - `validate_schema_claims`: Verify table and column names exist in actual schema before querying
  - `create_verification_link`: Generate verification payloads for reproducibility and audit trails
- **Enhanced execute_query responses**: Now includes verification metadata with every query result (query hash, timestamp, verification instructions, expected values)
- **Trust indicators**: All verification tools return trust indicators (hallucination risk, data freshness, validation method)
- **One-click verification**: Users can instantly re-run any query to verify AI responses match current data
- **Schema validation badges**: Prevent hallucinated column names by validating against actual schema
- **Tool count**: 18 tools total (16 QUERY, 0 ANALYTICS, 2 ADMIN)

## Major Refactoring - Query Handles Removed, Flows Consolidated
- **Removed query handle system**: Simplified execute_query to return results directly with auto-export for large result sets (>100 rows)
- **Consolidated template tools into flows**: Merged template_create + template_save_confidential into flow_create (auto-saves all flows), merged template_render + template_execute into flow_execute
- **Renamed all "template" terminology to "flow"** throughout codebase for clarity
- **Added flow_find tool**: Natural language search for reusable query flows using keyword matching
- **Enhanced format_query**: Now converts relative timestamps (ago()) to absolute datetime literals and adds fully qualified cluster.database references
- **Added save_chart tool**: Export KQL render visualizations as PNG images (timechart, barchart, piechart, table)
- **Added ingestion delay support**: query_from_natural_language now accepts ingestion_delay_minutes parameter (default: 5 minutes)
- **Absolute timestamps everywhere**: All query generation now uses absolute datetime literals instead of relative ago() timestamps
- **Query testing with retry logic**: Natural language queries are tested and automatically refined up to 3 attempts on failure
- **Tool count**: Reduced from 21 tools to 17 tools (removed 4 query handle tools, kept core functionality simpler)

## AI-Powered Query Generation
- Added AI-powered KQL query generation using VS Code Language Model API
- Created three system prompts: `kql_query_generator.md`, `intelligent_table_sampler.md`, `kql_query_refiner.md`
- Implemented `SamplingClient` utility for VS Code LM API integration
- Updated `ai_query_builder.py` with AI-first generation and iterative refinement
- Updated `natural_language_query.py` with AI-powered natural language to KQL translation
- Pattern: AI-first with rule-based fallback for backward compatibility
- Free models only: GPT-4o, GPT-4.1, Copilot SWE (Preview)

