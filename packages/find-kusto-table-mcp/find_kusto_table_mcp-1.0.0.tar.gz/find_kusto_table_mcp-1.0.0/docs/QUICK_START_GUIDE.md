# Quick Start Guide - Production Features

This guide helps you quickly leverage the production-ready enhancements added to the Kusto MCP server.

## 🚀 5-Minute Setup

### 1. Enable Real Kusto Connectivity

**Edit `connection_strings.json`:**
```json
{
    "clusters": {
        "mycluster": {
            "cluster_url": "https://mycluster.westus.kusto.windows.net",
            "use_real_client": true,
            "default_database": "MyDatabase"
        }
    },
    "default_cluster": "mycluster"
}
```

**Authentication (automatic fallback):**
- ✅ **Managed Identity**: Works automatically in Azure (VMs, Functions, AKS)
- ✅ **Azure CLI**: Run `az login` for local development
- ✅ **Device Auth**: Interactive fallback if above methods fail

### 2. Run the Server

```bash
python kusto_server.py
```

Server starts with:
- Circuit breakers enabled (protects against cascading failures)
- Retry logic active (3 attempts with exponential backoff)
- Bulkhead isolation (20 concurrent query limit)
- Persistent caching (survives restarts)
- 10 production query templates loaded

## 📊 Common Use Cases

### Use Case 1: Error Analysis with Anomaly Detection

```python
# Step 1: Execute query with handle
handle = execute_query_with_handle(
    cluster="mycluster",
    database="MyDatabase",
    table="ErrorLogs",
    query="""
    ErrorLogs
    | where EventTime > ago(7d)
    | summarize ErrorCount=count() by bin(EventTime, 1h), Severity
    """
)

# Step 2: Detect anomalies (no context pollution)
anomalies = query_handle_outlier_detection(
    handle=handle,
    column="ErrorCount",
    method="modified_zscore",  # Robust to extreme outliers
    threshold=3.5
)

# Step 3: Analyze statistics
stats = query_handle_statistical_analysis(
    handle=handle,
    columns=["ErrorCount"]
)

print(f"Anomalies detected: {len(anomalies['outliers'])}")
print(f"P95 error count: {stats['ErrorCount']['p95']}")
```

### Use Case 2: Performance Monitoring with Templates

```python
# Use production template for P95 latency analysis
query = template_render(
    name="performance_percentiles",
    parameters={
        "table": "RequestMetrics",
        "time_column": "RequestTime",
        "value_column": "Latency",
        "timespan": "1h",
        "bin_size": "5m"
    }
)

# Execute with handle
handle = execute_query_with_handle(
    cluster="mycluster",
    database="MyDatabase",
    query=query
)

# Analyze trends
trends = query_handle_time_series_analysis(
    handle=handle,
    time_column="bin_time",
    value_column="p95",
    window_size=12  # 1 hour moving average (12 * 5min)
)

if trends["trend"] == "increasing":
    print(f"⚠️ P95 latency increasing at {trends['rate_of_change']:.2f}ms/hour")
```

### Use Case 3: Query Optimization

```python
# Analyze problematic query
query = """
MyTable
| where Status == 'Failed'
| order by EventTime desc
| take 1000
"""

analysis = query_analyze_optimization(query=query)

print(f"Complexity: {analysis['complexity_score']} - {analysis['complexity_category']}")
print(f"Anti-patterns found: {len(analysis['anti_patterns'])}")
print(f"Estimated cost: {analysis['estimated_cost']}")

# Get optimized version
optimized = analysis["optimized_query"]
print(f"\nOptimized query:\n{optimized}")

# Get index recommendations
indexes = query_suggest_indexes(
    query=query,
    table_name="MyTable"
)

for idx in indexes["recommended_indexes"]:
    print(f"  - {idx['type']} index on {idx['columns']}: {idx['justification']}")
```

### Use Case 4: Security Threat Detection

```python
# Use security template
query = template_render(
    name="security_suspicious_activity",
    parameters={
        "table": "SecurityEvents",
        "lookback": "24h",
        "user_column": "UserPrincipalName",
        "ip_column": "SourceIP",
        "action_column": "Action"
    }
)

handle = execute_query_with_handle(
    cluster="mycluster",
    database="SecurityDB",
    query=query
)

# Detect anomalies in authentication attempts
anomalies = query_handle_outlier_detection(
    handle=handle,
    column="AttemptCount",
    method="iqr",
    threshold=1.5
)

if anomalies["outliers"]:
    print(f"🚨 {len(anomalies['outliers'])} users with suspicious activity detected!")
```

### Use Case 5: Cost Analysis and Optimization

```python
# Cost analysis template
query = template_render(
    name="cost_analysis_by_resource",
    parameters={
        "table": "BillingData",
        "timespan": "30d",
        "cost_column": "Cost",
        "resource_column": "ResourceId"
    }
)

handle = execute_query_with_handle(
    cluster="mycluster",
    database="FinOps",
    query=query
)

# Statistical analysis
stats = query_handle_statistical_analysis(
    handle=handle,
    columns=["DailyCost"]
)

print(f"Average daily cost: ${stats['DailyCost']['mean']:.2f}")
print(f"P95 daily cost: ${stats['DailyCost']['p95']:.2f}")
print(f"Total resources analyzed: {stats['DailyCost']['count']}")

# Correlation between resources
correlations = query_handle_correlation_analysis(
    handle=handle,
    numeric_columns=["DailyCost", "Usage"]
)

if correlations["DailyCost"]["Usage"] > 0.8:
    print("✅ Strong correlation between usage and cost (expected)")
```

## 🎯 Production Query Templates

### Available Templates

| Template Name | Use Case | Key Parameters |
|--------------|----------|----------------|
| `error_analysis_timerange` | Error monitoring and troubleshooting | `table`, `start_time`, `end_time`, `min_severity` |
| `performance_percentiles` | SLA monitoring (P50/P90/P95/P99) | `table`, `time_column`, `value_column`, `timespan` |
| `top_users_by_activity` | User analytics and insights | `table`, `user_column`, `timespan`, `top_n` |
| `anomaly_detection_timeseries` | Statistical anomaly detection | `table`, `time_column`, `value_column`, `lookback` |
| `data_quality_check` | ETL validation and data quality | `table`, `timespan`, `key_columns` |
| `hourly_trend_analysis` | Hour-over-hour comparison | `table`, `time_column`, `metric_column`, `days` |
| `failure_rate_by_component` | Service reliability tracking | `table`, `component_column`, `status_column`, `timespan` |
| `resource_utilization_peaks` | Capacity planning | `table`, `resource_column`, `metric_column`, `timespan` |
| `security_suspicious_activity` | Threat detection | `table`, `user_column`, `ip_column`, `action_column`, `lookback` |
| `cost_analysis_by_resource` | FinOps and cost optimization | `table`, `cost_column`, `resource_column`, `timespan` |

### Template Usage Pattern

```python
# 1. List available templates
templates = template_list(tags=["monitoring"])

# 2. Get template details
template = template_get(name="error_analysis_timerange")
print(f"Parameters: {[p['name'] for p in template['parameters']]}")

# 3. Render with parameters
query = template_render(
    name="error_analysis_timerange",
    parameters={
        "table": "MyTable",
        "start_time": "ago(6h)",
        "end_time": "now()",
        "min_severity": 3
    }
)

# 4. Execute
handle = execute_query_with_handle(query=query)
```

## 🛡️ Resilience Features

### Circuit Breaker

Automatically protects against cascading failures:

```python
# Circuit breaker states:
# - CLOSED: Normal operation, all queries execute
# - OPEN: Too many failures (5+), blocks all queries for 60s
# - HALF_OPEN: Testing recovery, allows 1 query through

# If Kusto cluster fails repeatedly:
# 1. After 5 failures → circuit opens (blocks queries)
# 2. After 60s → half-open (allows test query)
# 3. If test succeeds → closed (normal operation)
# 4. If test fails → open again (wait another 60s)
```

**No configuration needed - works automatically!**

### Exponential Backoff Retry

Automatically retries transient failures:

```python
# Retry behavior:
# - Attempt 1: Execute immediately
# - Attempt 2: Wait 1s + random jitter (0-200ms)
# - Attempt 3: Wait 2s + random jitter (0-400ms)
# - After 3 attempts: Raise exception

# Retried automatically for:
# - Network timeouts
# - Throttling errors
# - Transient Kusto failures

# NOT retried for:
# - Syntax errors (permanent)
# - Authentication failures (permanent)
# - Invalid table names (permanent)
```

**No configuration needed - works automatically!**

### Bulkhead Isolation

Limits concurrent queries to protect resources:

```python
# Maximum 20 concurrent Kusto queries
# If 20 queries are running:
# - Query 21 waits for a slot
# - Query 22+ wait in queue
# - Prevents resource exhaustion

# Metrics tracked:
# - concurrent_operations: Current active queries
# - total_operations: Total queries processed
# - rejected_operations: Queries rejected (if queue full)
```

**No configuration needed - works automatically!**

## 💿 Persistent Caching

### How It Works

```python
# Query results automatically persisted to disk:
# - Location: cache/query_handles/
# - Format: Pickle serialization
# - LRU eviction: Keeps 1000 newest in memory
# - Lazy loading: Loads from disk only when accessed

# Example workflow:
handle = execute_query_with_handle(query="MyTable | take 100000")
# → Results saved to disk immediately
# → Handle kept in memory (if space available)

# Server restarts...

# Later, access same handle:
data = query_handle_analyze(handle=handle, operation="count_by", column="Status")
# → Loads from disk if not in memory
# → No context pollution (doesn't return all rows)
```

### Cache Statistics

```python
stats = cache_stats()

print(f"Memory handles: {stats['memory_handles']}")
print(f"Disk handles: {stats['disk_handles']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Disk reads: {stats['disk_reads']}")
print(f"Disk writes: {stats['disk_writes']}")
```

## 📈 Advanced Analytics

### Statistical Analysis

```python
stats = query_handle_statistical_analysis(
    handle=handle,
    columns=["ResponseTime", "ErrorCount"]
)

# Returns for each column:
# - count, mean, median
# - stddev, variance
# - min, max
# - p25, p50 (median), p75, p90, p95, p99
# - skewness, kurtosis (distribution shape)
```

### Correlation Analysis

```python
correlations = query_handle_correlation_analysis(
    handle=handle,
    numeric_columns=["CPU", "Memory", "Latency", "ErrorRate"]
)

# Returns Pearson correlation matrix:
# correlations["CPU"]["Memory"] = 0.85  (strong positive correlation)
# correlations["Latency"]["ErrorRate"] = 0.92  (high correlation)

# Interpretation:
# - 1.0: Perfect positive correlation
# - 0.0: No correlation
# - -1.0: Perfect negative correlation
```

### Anomaly Detection Methods

```python
# Method 1: IQR (Interquartile Range) - Good for skewed data
anomalies = query_handle_outlier_detection(
    handle=handle,
    column="ResponseTime",
    method="iqr",
    threshold=1.5  # Standard threshold (1.5 * IQR)
)

# Method 2: Z-Score - Good for normal distributions
anomalies = query_handle_outlier_detection(
    handle=handle,
    column="ResponseTime",
    method="zscore",
    threshold=3.0  # 3 standard deviations
)

# Method 3: Modified Z-Score (MAD) - Robust to extreme outliers
anomalies = query_handle_outlier_detection(
    handle=handle,
    column="ResponseTime",
    method="modified_zscore",
    threshold=3.5  # Recommended for MAD
)

# Returns:
# - outliers: List of anomalous values
# - indices: Row indices of outliers
# - statistics: Method-specific stats (IQR, Z-scores, MAD)
```

### Time Series Trend Detection

```python
trends = query_handle_time_series_analysis(
    handle=handle,
    time_column="Timestamp",
    value_column="ErrorRate",
    window_size=10  # Moving average window
)

# Returns:
# - trend: "increasing", "decreasing", or "stable"
# - rate_of_change: Change per time unit
# - moving_averages: Smoothed values
# - timestamps: Time points

if trends["trend"] == "increasing":
    print(f"⚠️ Error rate increasing at {trends['rate_of_change']:.2f} errors/hour")
```

## 🎓 Best Practices

### 1. Always Use Handles for Large Results

```python
# ❌ BAD: Pollutes context with 100,000 rows
results = execute_query(query="MyTable | take 100000")

# ✅ GOOD: Server-side caching, no context pollution
handle = execute_query_with_handle(query="MyTable | take 100000")
stats = query_handle_statistical_analysis(handle=handle)
```

### 2. Leverage Production Templates

```python
# ❌ BAD: Reinvent the wheel
query = "MyTable | where Time > ago(1h) | summarize..."

# ✅ GOOD: Use tested templates
query = template_render(name="performance_percentiles", parameters={...})
```

### 3. Always Validate Queries Before Execution

```python
# ✅ GOOD: Catch issues early
analysis = query_analyze_optimization(query=my_query)

if analysis["complexity_score"] > 80:
    print(f"⚠️ High complexity query! Consider optimization.")
    print(f"Optimized version:\n{analysis['optimized_query']}")
```

### 4. Monitor Cache Statistics

```python
# Periodically check cache health
stats = cache_stats()

if stats["cache_hit_rate"] < 0.5:
    print("⚠️ Low cache hit rate - consider increasing TTL")

if stats["disk_handles"] > 5000:
    print("⚠️ Many disk handles - consider cleanup")
```

### 5. Use Anti-Hallucination Workflow

```python
# ✅ ALWAYS follow this workflow:
# 1. Search for tables
results = search_kusto_tables(query="error logs")

# 2. Sample table to get REAL schema
schema = sample_table_for_query_building(
    cluster=results[0]["cluster"],
    database=results[0]["database"],
    table=results[0]["table"]
)

# 3. Build query using EXACT column names from schema
time_col = schema["schema"]["primary_time_column"]
query = f"{table} | where {time_col} > ago(1h)"

# 4. Validate and optimize
analysis = query_analyze_optimization(query=query)

# 5. Execute with handle
handle = execute_query_with_handle(query=query)
```

## 🐛 Troubleshooting

### Circuit Breaker Opened

**Symptom**: Queries failing with "Circuit breaker is OPEN"

**Solution**:
```python
# Wait 60 seconds for automatic recovery
# Or manually reset if issue resolved:
# (requires access to resilience module)

# Check Kusto cluster health first:
# - Network connectivity
# - Authentication
# - Cluster availability
```

### Low Cache Hit Rate

**Symptom**: High disk I/O, slow query handle access

**Solution**:
```python
# Increase memory limit in query_handle_service.py:
# max_memory_handles = 2000  # Default: 1000

# Or clean up old handles:
cache_clear()
```

### High Query Complexity

**Symptom**: Slow query execution, high costs

**Solution**:
```python
analysis = query_analyze_optimization(query=your_query)

# Apply recommendations:
# - Add time filters
# - Add LIMIT clause
# - Select specific columns instead of *
# - Use suggested indexes

# Use optimized version:
optimized = analysis["optimized_query"]
```

## 📚 Additional Resources

- **Comprehensive Feature Documentation**: [OVERNIGHT_ENHANCEMENTS_V3.md](OVERNIGHT_ENHANCEMENTS_V3.md)
- **Development Guide**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- **Agent Instructions**: [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Questions or Issues?** Check the troubleshooting section in [OVERNIGHT_ENHANCEMENTS_V3.md](OVERNIGHT_ENHANCEMENTS_V3.md) or review the comprehensive test suite in `tests/`.
