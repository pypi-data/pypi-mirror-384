"""
Data export tools for Kusto MCP server.

This module provides tools for exporting query results to various formats:
- get_chart: Create chart visualization from query (save to file or return as base64)
"""

import os
import base64
import io
from typing import Optional
from datetime import datetime
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.data_export")


def register_data_export_tools(mcp, services: dict, default_export_dir: str):
    """Register data export tools with the MCP server."""

    # Note: export_results tool removed - execute_query now auto-exports large result sets
    # Charts are created using get_chart tool below

    @mcp.tool()
    async def get_chart(
        cluster: str,
        database: str,
        query: str,
        chart_type: str = "auto",
        return_base64: bool = True,
        save_to_file: bool = False,
        filename: Optional[str] = None,
        export_dir: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        ctx: Context = None
    ) -> str:
        """
        📊 Create a chart visualization from a KQL query result.
        
        Execute a query with visualization (render operator) and either return as base64-encoded
        PNG image or save to file (or both).
        
        Uses matplotlib for rendering various chart types based on KQL render operators.
        
        Supported chart types (from KQL render operator):
        - timechart: Time series line chart
        - barchart: Vertical bar chart
        - columnchart: Vertical bar chart (alias for barchart)
        - piechart: Pie chart
        - table: Data table (rendered as image)
        - auto: Automatically detect from query or use default
        
        Args:
            cluster: Cluster name
            database: Database name
            query: KQL query (may include | render operator)
            chart_type: Chart type to render (auto-detected from query if present)
            return_base64: Return chart as base64-encoded PNG (default: True)
            save_to_file: Save chart to file (default: False)
            filename: Optional filename when saving (auto-generated if not provided)
            export_dir: Directory to save charts (default: uses --export-dir from command line)
            width: Chart width in pixels (default: 1200)
            height: Chart height in pixels (default: 800)
        
        Returns:
            JSON with chart data (base64 and/or file info depending on flags)
        """
        if ctx:
            await ctx.info(f"Creating {chart_type} chart visualization")
        
        with measure_operation("get_chart"):
            try:
                # Import visualization libraries
                try:
                    import matplotlib
                    matplotlib.use('Agg')  # Use non-interactive backend
                    import matplotlib.pyplot as plt
                    import pandas as pd
                except ImportError:
                    raise ToolError("Chart generation requires 'matplotlib' and 'pandas' packages. Install with: pip install matplotlib pandas")
                
                # Execute the query to get data
                connection_manager = services['connection_manager']
                results, columns = await connection_manager.execute_query(
                    cluster=cluster,
                    database=database,
                    query=query,
                    timeout_seconds=None
                )
                
                if not results:
                    raise ToolError("Query returned no results to visualize")
                
                # Convert results to pandas DataFrame for easy plotting
                df = pd.DataFrame(results)
                
                # Auto-detect chart type from query if set to auto
                if chart_type == "auto":
                    query_lower = query.lower()
                    if "| render timechart" in query_lower:
                        chart_type = "timechart"
                    elif "| render barchart" in query_lower or "| render columnchart" in query_lower:
                        chart_type = "barchart"
                    elif "| render piechart" in query_lower:
                        chart_type = "piechart"
                    elif "| render table" in query_lower:
                        chart_type = "table"
                    else:
                        # Default to timechart if we have a datetime column, else barchart
                        datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
                        chart_type = "timechart" if datetime_cols else "barchart"
                
                # Create figure
                fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
                
                # Generate appropriate chart type
                if chart_type == "timechart":
                    # Find datetime column (usually first column)
                    datetime_col = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col]) or 'time' in col.lower():
                            datetime_col = col
                            break
                    
                    if datetime_col:
                        df[datetime_col] = pd.to_datetime(df[datetime_col])
                        df = df.sort_values(datetime_col)
                        
                        # Plot all numeric columns
                        for col in df.columns:
                            if col != datetime_col and pd.api.types.is_numeric_dtype(df[col]):
                                ax.plot(df[datetime_col], df[col], marker='o', label=col)
                        
                        ax.set_xlabel(datetime_col)
                        ax.legend()
                        plt.xticks(rotation=45, ha='right')
                    else:
                        raise ToolError("No datetime column found for timechart")
                
                elif chart_type == "barchart":
                    # Use first column as x-axis, rest as bars
                    if len(df.columns) < 2:
                        raise ToolError("Bar chart requires at least 2 columns")
                    
                    x_col = df.columns[0]
                    y_cols = [col for col in df.columns[1:] if pd.api.types.is_numeric_dtype(df[col])]
                    
                    if not y_cols:
                        raise ToolError("No numeric columns found for bar chart")
                    
                    df.plot(x=x_col, y=y_cols, kind='bar', ax=ax)
                    plt.xticks(rotation=45, ha='right')
                
                elif chart_type == "piechart":
                    # Use first column as labels, second as values
                    if len(df.columns) < 2:
                        raise ToolError("Pie chart requires at least 2 columns")
                    
                    labels_col = df.columns[0]
                    values_col = df.columns[1]
                    
                    ax.pie(df[values_col], labels=df[labels_col], autopct='%1.1f%%')
                
                elif chart_type == "table":
                    # Render as table image
                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='left')
                    table.auto_set_font_size(False)
                    table.set_fontsize(9)
                    table.scale(1, 2)
                
                else:
                    raise ToolError(f"Unsupported chart type: {chart_type}")
                
                # Add title
                ax.set_title(f"KQL Query Visualization - {chart_type}", fontsize=14, fontweight='bold')
                plt.tight_layout()
                
                # Prepare result dictionary
                result = {
                    "success": True,
                    "chart_type": chart_type,
                    "data_points": len(results),
                    "dimensions": {
                        "width": width,
                        "height": height
                    }
                }
                
                # Handle base64 encoding if requested
                if return_base64:
                    # Save to BytesIO buffer
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                    buffer.seek(0)
                    
                    # Encode as base64
                    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    result["image_base64"] = image_base64
                    result["image_size_bytes"] = len(image_base64)
                    
                    if ctx:
                        await ctx.info(f"Chart encoded as base64 ({len(image_base64)} bytes)")
                
                # Handle file saving if requested
                if save_to_file:
                    # Generate filename if not provided
                    if not filename:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"chart_{chart_type}_{timestamp}.png"
                    elif not filename.endswith('.png'):
                        filename = f"{filename}.png"
                    
                    # Use default export directory if not specified
                    if export_dir is None:
                        export_dir = default_export_dir
                    
                    # Create export directory if needed
                    os.makedirs(export_dir, exist_ok=True)
                    filepath = os.path.join(export_dir, filename)
                    
                    # Save chart to file
                    plt.savefig(filepath, bbox_inches='tight', dpi=100)
                    
                    # Get file size
                    file_size = os.path.getsize(filepath)
                    file_size_kb = file_size / 1024
                    
                    result["filename"] = filename
                    result["filepath"] = filepath
                    result["file_size_bytes"] = file_size
                    result["file_size_kb"] = round(file_size_kb, 2)
                    
                    if ctx:
                        await ctx.info(f"Chart saved to {filename} ({file_size_kb:.1f} KB)")
                
                # Close the figure
                plt.close(fig)
                
                # Add summary message
                if return_base64 and save_to_file:
                    result["summary"] = f"Successfully created {chart_type} chart with {len(results)} data points (base64 + file)"
                elif return_base64:
                    result["summary"] = f"Successfully created {chart_type} chart with {len(results)} data points (base64)"
                elif save_to_file:
                    result["summary"] = f"Successfully saved {chart_type} chart with {len(results)} data points (file)"
                else:
                    result["summary"] = f"Chart created but no output requested (set return_base64=True or save_to_file=True)"
                
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                error_msg = f"Chart generation failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if ctx:
                    await ctx.error(error_msg)
                raise ToolError(error_msg)
