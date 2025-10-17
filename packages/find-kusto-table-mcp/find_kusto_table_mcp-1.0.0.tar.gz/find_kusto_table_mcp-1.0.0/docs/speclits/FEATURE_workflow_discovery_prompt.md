# FEATURE: Workflow Discovery and Builder Prompt

**Date**: October 15, 2025  
**Feature**: New MCP prompt for discovering Kusto queries and building workflow templates  
**Status**: ✅ Implemented

## Overview

Added a comprehensive MCP prompt (`prompt_discover_and_build_workflows`) that guides AI agents through the complete workflow of:
1. Discovering Kusto queries in documentation or repositories
2. Analyzing query patterns and dependencies
3. Grouping related queries into logical workflows
4. Extracting parameters and metadata intelligently
5. Creating reusable workflow templates

## Problem Statement

Previously, users had to:
- Manually search for Kusto queries across multiple files
- Figure out which queries belonged together
- Extract parameters by hand
- Decide between `template_create` and `template_save_confidential`
- Create templates one at a time

This was time-consuming and error-prone, especially when onboarding new troubleshooting documentation or converting ad-hoc queries into standardized workflows.

## Solution

Created a systematic, phase-based prompt that walks AI agents through the complete workflow discovery process.

### Prompt Name
`prompt_discover_and_build_workflows`

### Key Features

#### 1. **Multiple Input Sources**
Supports various input types:
- Single documentation file (markdown, text)
- Multiple files (list of paths)
- Entire directory (recursive search)
- GitHub repository
- Open files in editor

#### 2. **Six-Phase Systematic Approach**

**Phase 1: Discovery**
- Scan files for KQL query patterns
- Look for code blocks (```kql, ```kusto)
- Detect cluster/database references
- Create inventory of all queries

**Phase 2: Analysis**
- Extract query purpose from context
- Identify hardcoded values for parameterization:
  - Time ranges (ago(), between())
  - IDs (SubscriptionId, NodeId, ContainerId)
  - Filters (status codes, error codes)
  - Thresholds (numeric limits)
  - Resources (cluster, database names)
- Detect query structure (simple vs complex)
- Extract tags from surrounding text

**Phase 3: Grouping**
- Group related queries into workflows
- Define workflow boundaries:
  - Independent queries → Separate templates
  - Dependent queries → Multi-step template
  - Alternative approaches → Related templates
- Generate workflow names and descriptions

**Phase 4: Parameterization**
- Convert hardcoded values to {parameter} placeholders
- Define parameter schemas with:
  - name, type, description
  - default_value, required flag
- Validate consistency across workflow

**Phase 5: Template Creation**
- Generate complete template structure
- Choose appropriate tool:
  - Simple/non-confidential → `template_create`
  - Complex/confidential → `template_save_confidential`
- Create all templates

**Phase 6: Verification**
- Run `workflow_list()` to verify
- Confirm all metadata is correct
- Provide summary report

#### 3. **Intelligent Pattern Detection**

The prompt teaches AI agents to recognize common patterns:

**Time-Based Patterns:**
```kql
| where Timestamp > ago(24h)          → {time_window}: "24h"
| where Timestamp between (start..end) → {start_time}, {end_time}
```

**ID Patterns:**
```kql
| where SubscriptionId == "abc-123"    → {subscription_id}
| where NodeId == "node-xyz"           → {node_id}
```

**Filter Patterns:**
```kql
| where ErrorCode == "500"             → {error_code}
| where Status == "Failed"             → {status}
```

**Threshold Patterns:**
```kql
| where Duration > 4000                → {duration_threshold_ms}
| where ErrorCount > 100               → {error_threshold}
```

#### 4. **Clear Tool Usage Guidance**

Provides concrete examples for:
- Searching for files (`file_search`, `grep_search`, `semantic_search`)
- Reading content (`read_file`)
- Creating simple templates (`template_create`)
- Creating complex templates (`template_save_confidential`)
- Verifying results (`workflow_list`)

#### 5. **Naming Conventions**

Standardized naming for consistency:

**Template Names** (snake_case):
- Format: `{component}_{action}_{context}`
- Examples: `wireserver_error_analysis`, `imds_request_monitoring`

**Parameter Names** (snake_case):
- Format: `{context}_{type}`
- Examples: `start_time`, `node_id`, `error_threshold`

**Tags** (lowercase, hyphenated):
- Component: wireserver, imds, metadata
- Action: monitoring, troubleshooting, analysis
- Category: errors, performance, requests

#### 6. **Summary Report Format**

The prompt guides the AI to provide a structured summary:
```
🎯 WORKFLOW DISCOVERY COMPLETE

📂 Sources Analyzed: [list of files]
🔍 Discovery Results: [query counts]
📦 Templates Created: [template list with types]
🏷️ Categories: [category breakdown]
📊 Total: [summary stats]
```

## Usage Examples

### Example 1: Analyze Single File
```
User: Use prompt_discover_and_build_workflows
AI: Ready! What would you like me to analyze?
User: docs/troubleshooting/wireserver-guide.md
AI: [Follows 6-phase process to discover and create templates]
```

### Example 2: Scan Entire Directory
```
User: Use prompt_discover_and_build_workflows
AI: Ready! What would you like me to analyze?
User: Analyze docs/troubleshooting/ directory
AI: [Searches all files recursively, creates workflow templates]
```

### Example 3: Search Workspace
```
User: Use prompt_discover_and_build_workflows
AI: Ready! What would you like me to analyze?
User: Search the entire workspace for Kusto queries and build templates
AI: [Uses semantic_search and grep_search to find queries everywhere]
```

## Benefits

### For Users
1. **Automated Discovery**: No manual search through files
2. **Intelligent Grouping**: AI understands workflow relationships
3. **Smart Parameterization**: Automatic detection of reusable values
4. **Consistent Naming**: Follows standardized conventions
5. **Complete Workflow**: End-to-end from discovery to verification

### For AI Agents
1. **Clear Step-by-Step Process**: Systematic 6-phase approach
2. **Pattern Recognition**: Examples of common query patterns
3. **Tool Selection Guidance**: When to use each tool
4. **Validation Steps**: Built-in verification
5. **Error Prevention**: Checks for required metadata

### For Organizations
1. **Standardization**: All workflows follow same structure
2. **Reusability**: Queries become templates
3. **Documentation**: Auto-generated from existing content
4. **Onboarding**: Fast integration of new troubleshooting guides
5. **Maintenance**: Easy to update and version

## Comparison with Existing Prompt

### Old: `prompt_create_workflows_from_docs`
- Single file at a time
- User must provide file path
- Less structured approach
- Minimal guidance on grouping
- Basic pattern examples

### New: `prompt_discover_and_build_workflows`
- Multiple input sources (files, directories, repos)
- Can search entire workspace
- Systematic 6-phase methodology
- Comprehensive grouping logic
- Extensive pattern detection examples
- Tool usage guidance
- Summary reporting

## Technical Implementation

### Prompt Definition
```python
@mcp.prompt()
def prompt_discover_and_build_workflows() -> str:
    """
    🔍 Discover Kusto queries in documentation or repositories and build logical workflow templates.
    
    This prompt is a comprehensive workflow discovery assistant that:
    - Searches through documentation files, markdown, or entire repositories
    - Identifies all Kusto/KQL queries automatically
    - Analyzes query patterns and dependencies
    - Groups related queries into logical workflows
    - Extracts parameters and metadata intelligently
    - Creates reusable workflow templates with proper structure
    
    Perfect for:
    - Onboarding new troubleshooting guides
    - Converting ad-hoc queries into workflows
    - Building template libraries from existing documentation
    - Standardizing query patterns across teams
    """
```

### Integration with Existing Tools

The prompt leverages all existing MCP tools:
- **Discovery**: `file_search`, `grep_search`, `semantic_search`, `read_file`
- **Creation**: `template_create`, `template_save_confidential`
- **Verification**: `workflow_list`, `template_list`

No new tools needed - just intelligent orchestration of existing capabilities.

## Use Cases

### 1. Onboarding Troubleshooting Documentation
**Scenario**: New troubleshooting guide with 10+ queries  
**Before**: Hours of manual extraction and template creation  
**After**: 5 minutes with automated discovery and grouping

### 2. Standardizing Ad-Hoc Queries
**Scenario**: Team has queries scattered across wikis and markdown files  
**Before**: Inconsistent naming, missing parameters, no reusability  
**After**: Standardized templates with proper structure

### 3. Building Template Libraries
**Scenario**: Organization wants centralized workflow library  
**Before**: Manual curation, inconsistent quality  
**After**: Automated extraction with consistent quality

### 4. Converting Wiki Pages
**Scenario**: Azure DevOps wiki with troubleshooting procedures  
**Before**: Copy-paste queries, manual parameter adjustment  
**After**: Automated conversion to reusable workflows

## Future Enhancements

Potential improvements for future versions:
1. **GitHub Integration**: Direct repository cloning and analysis
2. **Azure DevOps Wiki**: Native wiki page analysis
3. **Query Validation**: Syntax checking before template creation
4. **Dependency Detection**: Identify query dependencies automatically
5. **Performance Analysis**: Estimate query performance from patterns
6. **Version Control**: Track template changes over time

## Related Files

- `kusto_server.py` - Prompt implementation
- `docs/speclits/FEATURE_workflow_discovery_prompt.md` - This document
- `docs/speclits/FEATURE_template_save_confidential.md` - Related feature

## Conclusion

The `prompt_discover_and_build_workflows` prompt provides a comprehensive, systematic approach to discovering Kusto queries and building workflow templates. It reduces manual work, ensures consistency, and makes it easy for AI agents to convert existing documentation into reusable, standardized workflows.

**Status**: ✅ Implemented and ready to use
