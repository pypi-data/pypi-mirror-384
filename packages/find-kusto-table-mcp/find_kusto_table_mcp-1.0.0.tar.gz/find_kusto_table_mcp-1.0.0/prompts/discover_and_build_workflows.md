---
name: discover_and_build_workflows
description: >-
  Discover Kusto queries across multiple sources (files, directories, repos) and build workflow templates.
  Systematically extracts KQL queries, identifies parameters, groups related queries, and creates reusable templates.
version: 1
arguments: {}
---

# 🔍 Workflow Discovery and Template Builder

## Input Sources

Tell me what to analyze:

1. **Single File**: `docs/troubleshooting/guide.md`
2. **Multiple Files**: `["docs/imds.md", "docs/metadata.md"]`
3. **Directory**: `docs/troubleshooting/`
4. **Open Files**: "analyze open files"

## Systematic Approach

### Phase 1: Discovery
- Scan files for KQL query patterns (```kql, ```kusto, ```)
- Detect cluster() and database() references  
- Identify table names and query structures
- Create inventory of all found queries

### Phase 2: Analysis
- Extract query purpose from headers/context
- Identify parameterizable values:
  - Time ranges: `ago(24h)`, `between(start..end)`
  - IDs: SubscriptionId, NodeId, ContainerId
  - Filters: Status codes, error codes, strings
  - Thresholds: Numeric limits, percentiles
- Detect cluster/database from query text
- Analyze structure (single vs multi-step)

### Phase 3: Grouping
- Group related queries together
- Define workflow boundaries
- Generate workflow names/descriptions

### Phase 4: Parameterization
- Convert hardcoded values to `{parameter}` placeholders
- Define parameter schema (name, type, description, default, required)
- Validate parameter consistency

### Phase 5: Template Creation
- Build template structure with metadata
- **Simple/Non-Confidential**: Use `template_create()`
- **Complex/Confidential**: Use `template_save_confidential()`

### Phase 6: Verification
- Run `template_list()` to confirm
- Provide summary report

## Tool Usage

**Search for files:**
```
file_search(query="**/*.md")
grep_search(query="cluster\\(", isRegexp=true)
```

**Create template:**
```json
template_create(
  name="component_action_context",
  description="What this query does",
  query="TableName | where Timestamp > ago({time_window})",
  parameters=[{
    "name": "time_window",
    "type": "timespan",
    "description": "Time range",
    "default_value": "24h"
  }],
  cluster="azcore",
  database="Fa",
  tags=["monitoring"]
)
```

## Pattern Detection

**Time patterns:**
- `ago(24h)` → `{time_window}: "24h"`
- `between(start..end)` → `{start_time}`, `{end_time}`

**ID patterns:**
- `SubscriptionId == "abc"` → `{subscription_id}`
- `NodeId == "xyz"` → `{node_id}`

**Filter patterns:**
- `ErrorCode == "500"` → `{error_code}`
- `Status == "Failed"` → `{status}`

## Naming Conventions

**Templates**: `{component}_{action}_{context}`
- wireserver_error_analysis
- imds_request_monitoring

**Parameters**: `{context}_{type}`
- start_time, time_window
- node_id, subscription_id

**Tags**: wireserver, imds, troubleshooting, monitoring

## Output Format

```
🎯 WORKFLOW DISCOVERY COMPLETE

📂 Sources: 3 files analyzed
🔍 Discovery: 15 queries found  
📦 Created: 7 templates
🏷️ Categories: troubleshooting (4), monitoring (3)

✅ All templates available via template_list()
```

1. **Single Documentation File**
   - Path to markdown/text file in workspace
   - Example: "docs/troubleshooting/wireserver-guide.md"

2. **Multiple Files**
   - List of file paths
   - Example: ["docs/imds.md", "docs/metadata.md", "docs/attestation.md"]

3. **Entire Directory**
   - Directory path to search recursively
   - Example: "docs/troubleshooting/"

4. **GitHub Repository**
   - Repository URL or workspace folder
   - Example: "github.com/myorg/troubleshooting-docs"

5. **Open Files**
   - Use files already open in editor
   - Tell me: "analyze open files"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **MY SYSTEMATIC APPROACH:**

**PHASE 1: DISCOVERY** (Find all Kusto queries)
├─ 🔍 Scan files for KQL query patterns
├─ 📝 Look for code blocks: ```kql, ```kusto, ```
├─ 🔗 Detect inline cluster() and database() references
├─ 📊 Identify table names and query structures
└─ 📋 Create inventory of all found queries

**PHASE 2: ANALYSIS** (Understand each query)
├─ 🏷️ Extract query purpose from surrounding text/headers
├─ 🔢 Identify hardcoded values that should be parameters:
│   ├─ Time ranges: ago(24h), between(start..end)
│   ├─ IDs: SubscriptionId, NodeId, ContainerId, RequestId
│   ├─ Filters: Status codes, error codes, strings
│   ├─ Thresholds: Numeric limits, percentiles
│   └─ Resources: Cluster names, database names
├─ 🗃️ Detect cluster/database from query text
├─ 🏗️ Analyze query structure:
│   ├─ Single-step query? → Simple template
│   ├─ Multi-step workflow? → Complex template
│   ├─ Numbered sections? → Sequential workflow
│   └─ Conditional logic? → Decision tree workflow
└─ 🏷️ Extract tags from context (component, action, category)

**PHASE 3: GROUPING** (Organize into workflows)
├─ 📦 Group related queries together:
│   ├─ Same troubleshooting scenario
│   ├─ Sequential investigation steps
│   ├─ Related metrics/analysis
│   └─ Common component/feature
├─ 🎯 Define workflow boundaries:
│   ├─ Independent queries → Separate templates
│   ├─ Dependent queries → Single multi-step template
│   └─ Alternative approaches → Related templates with tags
└─ 📝 Generate workflow names and descriptions

**PHASE 4: PARAMETERIZATION** (Make queries reusable)
├─ 🔄 Convert hardcoded values to {parameter_name} placeholders
├─ 📋 Define parameter schema for each:
│   ├─ name: Descriptive identifier
│   ├─ type: string | number | datetime | timespan | boolean
│   ├─ description: Clear explanation of purpose
│   ├─ default_value: Sensible default (if applicable)
│   └─ required: true/false
├─ ✅ Validate parameter consistency across workflow
└─ 📝 Document parameter examples and constraints

**PHASE 5: TEMPLATE CREATION** (Save workflows)
├─ 🎨 Generate template structure:
│   ├─ name: {component}_{action}_{context}
│   ├─ description: Clear purpose and use case
│   ├─ query: Parameterized KQL with placeholders
│   ├─ parameters: Full parameter definitions
│   ├─ metadata: {cluster, database, confidential, ...}
│   └─ tags: [component, category, action, ...]
├─ 🔀 Choose appropriate tool:
│   ├─ SIMPLE/NON-CONFIDENTIAL:
│   │   → Use template_create(name, description, query, parameters, cluster, database, tags)
│   │   → Stored in memory only
│   └─ COMPLEX/CONFIDENTIAL:
│       → Use template_save_confidential(template_json)
│       → Saved to cache/templates/ and loaded into memory
└─ 💾 Create all templates

**PHASE 6: VERIFICATION** (Confirm success)
├─ 📋 Run workflow_list() to see all created templates
├─ ✅ Verify each template has:
│   ├─ Correct name and description
│   ├─ All required parameters defined
│   ├─ Valid cluster/database metadata
│   └─ Appropriate tags for discovery
└─ 📊 Provide summary report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 **TOOL USAGE PATTERNS:**

**Searching for Files:**
```
file_search(query="**/*.md")  # Find all markdown files
grep_search(query="cluster\\(", isRegexp=true)  # Find files with Kusto queries
semantic_search(query="troubleshooting kusto queries wireserver")
```

**Reading Content:**
```
read_file(filePath="docs/troubleshooting/guide.md")
```

**Creating Simple Templates:**
```python
template_create(
    name="component_action_context",
    description="Clear description of what this query does",
    query="TableName | where Timestamp > ago({time_window}) | where Status == '{status}'",
    parameters=[
        {
            "name": "time_window",
            "type": "timespan",
            "description": "Time range to analyze",
            "default_value": "24h",
            "required": true
        },
        {
            "name": "status",
            "type": "string",
            "description": "Status to filter by",
            "default_value": "Error",
            "required": false
        }
    ],
    cluster="azcore",
    database="Fa",
    tags=["monitoring", "errors", "component-name"]
)
```

**Creating Complex/Confidential Templates:**
```python
template_save_confidential(
    template_json={
        "name": "component_troubleshooting_workflow",
        "description": "Multi-step troubleshooting workflow for component",
        "query": "// Step 1: Check status\\nprint 'Step 1';\\nTable1 | ...\\n\\n// Step 2: Analyze errors\\nprint 'Step 2';\\nTable2 | ...",
        "parameters": [
            {
                "name": "node_id",
                "type": "string",
                "description": "Node to investigate",
                "required": true
            },
            {
                "name": "start_time",
                "type": "datetime",
                "description": "Investigation start time",
                "required": true
            }
        ],
        "metadata": {
            "cluster": "azcore",
            "database": "Fa",
            "confidential": true
        },
        "tags": ["troubleshooting", "multi-step", "component-name"]
    }
)
```

**Verifying Results:**
```python
workflow_list()  # See all created workflows
workflow_list(category="troubleshooting")  # Filter by category
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **INTELLIGENT QUERY PATTERNS TO DETECT:**

**Time-Based Patterns:**
```kql
| where Timestamp > ago(24h)          → {time_window}: "24h"
| where Timestamp between (start..end) → {start_time}, {end_time}
```

**ID Patterns:**
```kql
| where SubscriptionId == "abc-123"    → {subscription_id}
| where NodeId == "node-xyz"           → {node_id}
| where ContainerId == "container-1"   → {container_id}
```

**Filter Patterns:**
```kql
| where ErrorCode == "500"             → {error_code}
| where Status == "Failed"             → {status}
| where RequestUrl contains "/metadata" → {url_pattern}
```

**Threshold Patterns:**
```kql
| where Duration > 4000                → {duration_threshold_ms}
| where ErrorCount > 100               → {error_threshold}
```

**Cluster/Database References:**
```kql
cluster('azcore.centralus').database('Fa')
cluster("admeus.westus2").database("AdmProd")
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 **NAMING CONVENTIONS:**

**Template Names** (snake_case):
- Format: `{component}_{action}_{context}`
- Examples:
  - wireserver_error_analysis
  - imds_request_monitoring
  - metadata_endpoint_troubleshooting
  - node_health_check
  - subscription_error_summary

**Parameter Names** (snake_case):
- Format: `{context}_{type}`
- Examples:
  - start_time, end_time
  - time_window
  - node_id, subscription_id
  - error_code, status_code
  - error_threshold
  - url_pattern

**Tags** (lowercase, hyphenated):
- Component: wireserver, imds, metadata, attestation
- Action: monitoring, troubleshooting, analysis, debugging
- Category: errors, performance, requests, health
- Type: multi-step, diagnostic, investigation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **EXPECTED OUTPUT FORMAT:**

After discovery and creation, provide a summary:

```
🎯 WORKFLOW DISCOVERY COMPLETE

📂 Sources Analyzed:
- docs/troubleshooting/wireserver-guide.md
- docs/troubleshooting/imds-debugging.md
- docs/monitoring/health-checks.md

🔍 Discovery Results:
- Total queries found: 15
- Simple queries: 8
- Complex workflows: 7

📦 Templates Created:
✅ wireserver_heartbeat_check (simple, non-confidential)
✅ wireserver_error_analysis (simple, non-confidential)
✅ wireserver_troubleshooting_first_steps (complex, confidential)
✅ imds_request_monitoring (simple, non-confidential)
✅ imds_endpoint_health (simple, non-confidential)
✅ metadata_endpoint_analysis (complex, confidential)
✅ node_health_comprehensive (complex, confidential)

🏷️ Categories:
- troubleshooting: 4 workflows
- monitoring: 3 workflows
- diagnostics: 2 workflows

📊 Total: 7 workflow templates created and ready to use

✅ All templates available via workflow_list() and executable via template_execute()
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 **READY TO START!**

Please provide:
1. What to analyze (file path, directory, repo, or "open files")
2. Any specific focus areas (optional: components, tags, query types)
3. Cluster/database to use if not specified in queries

Example:
- "Analyze docs/troubleshooting/ and create workflows"
- "Search workspace for all Kusto queries and build templates"
- "Convert the open markdown file into workflow templates"

Let's discover and organize your Kusto workflows! 🎯
