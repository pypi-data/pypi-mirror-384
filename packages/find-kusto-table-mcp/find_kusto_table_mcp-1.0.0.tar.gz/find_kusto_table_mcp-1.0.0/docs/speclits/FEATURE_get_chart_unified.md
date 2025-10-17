# Feature: Unified Chart Visualization Tool

## Overview
The `get_chart` tool provides a unified interface for creating chart visualizations from Kusto query results, with flexible output options including base64-encoded images and file saving.

## Tool Name
`get_chart`

## What It Does
- Executes a KQL query and generates a chart visualization
- Supports multiple chart types (timechart, barchart, piechart, table)
- Can return chart as base64-encoded PNG image (default)
- Can save chart to file (optional)
- Can do both simultaneously

## Parameters

### Required
- `cluster`: Kusto cluster name
- `database`: Database name
- `query`: KQL query (may include `| render` operator)

### Optional
- `chart_type`: Chart type - "auto" (default), "timechart", "barchart", "columnchart", "piechart", "table"
- `return_base64`: Return base64-encoded PNG (default: `True`)
- `save_to_file`: Save to file (default: `False`)
- `filename`: Custom filename when saving (auto-generated if not provided)
- `export_dir`: Directory for saved files (uses command-line default if not specified)
- `width`: Chart width in pixels (default: 1200)
- `height`: Chart height in pixels (default: 800)

## Usage Examples

### Example 1: Return Base64 Only (Default)
```python
get_chart(
    cluster="myCluster",
    database="myDatabase",
    query="MyTable | summarize count() by Category"
)
# Returns JSON with image_base64 field containing PNG data
```

### Example 2: Save to File Only
```python
get_chart(
    cluster="myCluster",
    database="myDatabase",
    query="MyTable | summarize count() by Category",
    return_base64=False,
    save_to_file=True,
    filename="my_chart.png"
)
# Saves to file, returns JSON with filepath
```

### Example 3: Both Base64 and File
```python
get_chart(
    cluster="myCluster",
    database="myDatabase",
    query="MyTable | summarize count() by Category | render timechart",
    return_base64=True,
    save_to_file=True
)
# Returns base64 image AND saves to file
```

### Example 4: Custom Dimensions
```python
get_chart(
    cluster="myCluster",
    database="myDatabase",
    query="MyTable | summarize avg(Value) by bin(Timestamp, 1h)",
    chart_type="timechart",
    width=1920,
    height=1080
)
```

## Return Value

JSON object containing:
- `success`: Boolean indicating success
- `chart_type`: Type of chart created
- `data_points`: Number of data points visualized
- `dimensions`: Chart dimensions (width, height)
- `image_base64`: Base64-encoded PNG (if `return_base64=True`)
- `image_size_bytes`: Size of base64 image (if returned)
- `filename`: Saved filename (if `save_to_file=True`)
- `filepath`: Full path to saved file (if `save_to_file=True`)
- `file_size_bytes`: File size in bytes (if saved)
- `file_size_kb`: File size in KB (if saved)
- `summary`: Human-readable summary

## Chart Type Auto-Detection

When `chart_type="auto"`, the tool automatically detects the appropriate chart type:

1. **From Query**: Checks for `| render <type>` in query
2. **From Data**: If no render operator found:
   - Uses `timechart` if datetime column detected
   - Uses `barchart` otherwise

## Supported Chart Types

### timechart
Time series line chart with datetime on x-axis. Automatically detects datetime column and plots all numeric columns as lines.

### barchart / columnchart
Vertical bar chart. Uses first column as x-axis labels, subsequent numeric columns as bars.

### piechart
Pie chart showing proportions. Uses first column as labels, second column as values.

### table
Renders query results as a formatted table image.

## Dependencies

Requires:
- `matplotlib>=3.7.0`
- `pandas>=2.0.0`

Install with:
```bash
pip install matplotlib pandas
```

## Use Cases

### 1. **Inline Display in Chat/UI**
Return base64-encoded image for immediate display in chat interfaces or web UIs without saving files.

### 2. **Report Generation**
Save charts to files for inclusion in reports, dashboards, or documentation.

### 3. **Dual Output**
Generate both inline preview (base64) and permanent file for archival/sharing.

### 4. **Automated Monitoring**
Generate and save charts on schedule for monitoring dashboards.

## Design Rationale

### Why Unified Tool?
Previously had separate `save_chart` tool. Unified approach provides:
- **Flexibility**: One tool, multiple output modes
- **Simplicity**: Single interface to learn
- **Efficiency**: Can get both outputs in one call
- **Discoverability**: Users find one tool instead of searching for alternatives

### Why Base64 Default?
Most AI chat interfaces benefit from inline image display. Base64 encoding allows immediate visualization without file system access.

### Why Optional File Saving?
File saving adds overhead (disk I/O, file management). Making it optional keeps the default case fast while supporting persistence when needed.

## Implementation Notes

- Uses matplotlib's non-interactive backend (`Agg`) for server-side rendering
- Converts query results to pandas DataFrame for easy plotting
- Generates chart in memory, then either:
  - Encodes to base64 via BytesIO buffer
  - Saves to file via `plt.savefig()`
  - Or both
- Properly closes matplotlib figures to prevent memory leaks
- Auto-generates timestamps for filenames to prevent collisions

## Migration from `save_chart`

Old code:
```python
save_chart(cluster, database, query, filename="chart.png")
```

New equivalent:
```python
get_chart(cluster, database, query, 
          return_base64=False, 
          save_to_file=True, 
          filename="chart.png")
```

Or use new default (base64):
```python
get_chart(cluster, database, query)  # Returns base64 image
```

## Error Handling

Tool raises `ToolError` for:
- Missing matplotlib/pandas dependencies
- Query returns no results
- Unsupported chart type
- Chart-specific errors (e.g., no datetime column for timechart)
- File I/O errors when saving

## Performance Considerations

- Base64 encoding adds ~33% size overhead vs raw PNG
- Large charts (many data points) will have large base64 strings
- File saving is slower but produces smaller on-disk files
- Consider using `save_to_file=True` with `return_base64=False` for very large visualizations

## Future Enhancements

Potential additions:
- Additional chart types (scatter, heatmap, area)
- Style customization (colors, themes, fonts)
- Multiple format support (SVG, PDF, JPEG)
- Chart template library
- Interactive charts with Plotly
