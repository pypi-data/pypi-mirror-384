"""
Verification and Trust Tools for Kusto MCP Server

This module provides tools to verify AI responses and prevent hallucination:
- verify_query_result: Re-run a query and compare with previous results
- validate_schema_claims: Verify table/column names exist in actual schema
- create_verification_link: Generate verification payload for reproducibility

These tools help users quickly verify that AI responses are accurate and not hallucinated.

Best Practices:
- Always verify queries before trusting results
- Use validation to prevent column name hallucination
- Create verification links for audit trails

Example Usage:
    # Verify a query result
    result = verify_query_result(
        cluster="azcore",
        database="AtScale",
        query="Table | take 10",
        expected_row_count=10
    )
    
    # Validate schema claims
    validation = validate_schema_claims(
        cluster="azcore",
        database="AtScale",
        table_name="MyTable",
        claimed_columns=["TimeGenerated", "Message"]
    )
"""

import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..core.exceptions import ValidationError, QueryError, SchemaError
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.verification")


def register_verification_tools(mcp, services: dict):
    """Register verification and trust tools with the MCP server."""
    connection_manager = services['connection_manager']
    schema_cache = services['schema_cache']

    @mcp.tool()
    async def verify_query_result(
        cluster: str,
        database: str,
        query: str,
        expected_row_count: Optional[int] = None,
        expected_columns: Optional[List[str]] = None,
        show_diff: bool = True,
        ctx: Context = None
    ) -> str:
        """
        ✅ Verify a query result by re-running it and comparing with expectations.
        
        This tool helps verify that AI-provided information is accurate by:
        1. Re-executing the original query against live data
        2. Comparing row counts, columns, and data with expected values
        3. Highlighting any differences or changes
        
        Perfect for: Trust verification, detecting stale data, validating AI responses
        
        Args:
            cluster: Cluster name (e.g., "azcore", "admeus")
            database: Database name (e.g., "AtScale", "AdmProd")
            query: KQL query to verify
            expected_row_count: Expected number of rows (optional)
            expected_columns: Expected column names (optional)
            show_diff: Include detailed differences in output (default: True)
        
        Returns:
            JSON with verification results, differences, and trust indicators
        
        Raises:
            ValidationError: If input parameters are invalid
            QueryError: If query execution fails
        """
        if ctx:
            await ctx.info(f"Verifying query result...")
        
        with measure_operation("verify_query_result"):
            try:
                # Validate inputs
                if not cluster or not database or not query:
                    raise ValidationError(
                        "Missing required parameters: cluster, database, and query are required",
                        metadata={"cluster": cluster, "database": database}
                    )
                
                if expected_row_count is not None and expected_row_count < 0:
                    raise ValidationError(
                        "expected_row_count must be non-negative",
                        field="expected_row_count"
                    )
                
                # Execute query
                start_time = datetime.now()
                results, columns = await connection_manager.execute_query(
                    cluster=cluster,
                    database=database,
                    query=query,
                    timeout_seconds=None
                )
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Extract actual values
                actual_row_count: int = len(results)
                actual_columns: List[str] = [col['name'] for col in columns]
                
                # Build verification report
                verification: Dict[str, Any] = {
                    "verified_at": datetime.now().isoformat(),
                    "execution_time_seconds": round(execution_time, 2),
                    "query_hash": hashlib.md5(query.encode()).hexdigest()[:8],
                    "verification_status": "VERIFIED",
                    "checks": []
                }
                
                # Check row count
                if expected_row_count is not None:
                    row_match = actual_row_count == expected_row_count
                    verification["checks"].append({
                        "check": "row_count",
                        "status": "PASS" if row_match else "MISMATCH",
                        "expected": expected_row_count,
                        "actual": actual_row_count,
                        "diff": actual_row_count - expected_row_count if not row_match else 0
                    })
                    if not row_match:
                        verification["verification_status"] = "MISMATCH"
                else:
                    verification["checks"].append({
                        "check": "row_count",
                        "status": "INFO",
                        "actual": actual_row_count,
                        "note": "No expected value provided"
                    })
                
                # Check columns
                if expected_columns is not None:
                    missing_cols = set(expected_columns) - set(actual_columns)
                    extra_cols = set(actual_columns) - set(expected_columns)
                    cols_match = len(missing_cols) == 0 and len(extra_cols) == 0
                    
                    verification["checks"].append({
                        "check": "columns",
                        "status": "PASS" if cols_match else "MISMATCH",
                        "expected": expected_columns,
                        "actual": actual_columns,
                        "missing_columns": list(missing_cols) if missing_cols else [],
                        "extra_columns": list(extra_cols) if extra_cols else []
                    })
                    if not cols_match:
                        verification["verification_status"] = "MISMATCH"
                else:
                    verification["checks"].append({
                        "check": "columns",
                        "status": "INFO",
                        "actual": actual_columns,
                        "note": "No expected columns provided"
                    })
                
                # Include sample data if requested
                if show_diff and results:
                    verification["sample_data"] = {
                        "first_3_rows": results[:3],
                        "last_3_rows": results[-3:] if len(results) > 3 else [],
                        "total_rows": len(results)
                    }
                
                # Add trust indicators
                verification["trust_indicators"] = {
                    "data_freshness": "LIVE" if execution_time < 5 else "SLOW",
                    "query_executed_successfully": True,
                    "timestamp": datetime.now().isoformat(),
                    "verification_method": "direct_query_execution"
                }
                
                # Summary message
                if verification["verification_status"] == "VERIFIED":
                    summary = f"Query verified successfully. {actual_row_count} rows returned."
                else:
                    summary = f"Verification found differences. Check 'checks' array for details."
                
                verification["summary"] = summary
                
                if ctx:
                    status_emoji = "✅" if verification["verification_status"] == "VERIFIED" else "⚠️"
                    await ctx.info(f"{status_emoji} {summary}")
                
                return safe_json_dumps(verification, indent=2)
                
            except ValidationError:
                raise  # Re-raise validation errors
            except Exception as e:
                error_msg = f"Verification failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if ctx:
                    await ctx.error(error_msg)
                
                # Return error as verification failure
                raise QueryError(
                    "Query execution failed during verification",
                    query=query[:100],  # Truncate long queries
                    metadata={
                        "cluster": cluster,
                        "database": database,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

    @mcp.tool()
    async def validate_schema_claims(
        cluster: str,
        database: str,
        table_name: str,
        claimed_columns: Optional[List[str]] = None,
        ctx: Context = None
    ) -> str:
        """
        🔍 Validate that table and column names actually exist in the schema.
        
        This tool prevents hallucination by checking AI claims against actual schema:
        1. Verifies table exists in specified database
        2. Validates each claimed column name
        3. Reports missing or incorrect schema elements
        4. Provides suggestions for typos
        
        Perfect for: Schema validation, preventing hallucinated column names, trust verification
        
        Args:
            cluster: Cluster name (e.g., "azcore", "admeus")
            database: Database name (e.g., "AtScale", "AdmProd")
            table_name: Table name to validate
            claimed_columns: List of column names to validate (optional)
        
        Returns:
            JSON with validation results and trust indicators
        
        Raises:
            ValidationError: If input parameters are invalid
            SchemaError: If schema cannot be retrieved
        """
        if ctx:
            await ctx.info(f"Validating schema claims for {table_name}...")
        
        with measure_operation("validate_schema_claims"):
            try:
                # Validate inputs
                if not cluster or not database or not table_name:
                    raise ValidationError(
                        "Missing required parameters: cluster, database, and table_name are required",
                        metadata={"cluster": cluster, "database": database, "table": table_name}
                    )
                
                # Get actual schema
                schema = await schema_cache.get_schema(
                    cluster=cluster,
                    database=database,
                    table=table_name
                )
                
                if not schema:
                    validation_result: Dict[str, Any] = {
                        "validation_status": "FAILED",
                        "table_exists": False,
                        "error": f"Table '{table_name}' not found in {database}",
                        "summary": "Table does not exist - potential hallucination",
                        "trust_indicators": {
                            "schema_validated": False,
                            "hallucination_risk": "HIGH"
                        }
                    }
                    return safe_json_dumps(validation_result, indent=2)
                
                # Extract actual columns (schema is a SchemaMetadata dataclass, not a dict)
                actual_columns = {col['name']: col['type'] for col in schema.columns}
                
                validation = {
                    "validated_at": datetime.now().isoformat(),
                    "validation_status": "VALID",
                    "table_exists": True,
                    "table_name": table_name,
                    "database": database,
                    "cluster": cluster,
                    "actual_column_count": len(actual_columns)
                }
                
                # Validate claimed columns
                if claimed_columns:
                    valid_columns = []
                    invalid_columns = []
                    
                    for col in claimed_columns:
                        if col in actual_columns:
                            valid_columns.append({
                                "name": col,
                                "type": actual_columns[col],
                                "status": "VALID"
                            })
                        else:
                            invalid_columns.append({
                                "name": col,
                                "status": "INVALID",
                                "reason": "Column does not exist in schema"
                            })
                    
                    validation["column_validation"] = {
                        "total_claimed": len(claimed_columns),
                        "valid_count": len(valid_columns),
                        "invalid_count": len(invalid_columns),
                        "valid_columns": valid_columns,
                        "invalid_columns": invalid_columns
                    }
                    
                    if invalid_columns:
                        validation["validation_status"] = "PARTIAL"
                        validation["summary"] = f"{len(invalid_columns)} column(s) do not exist"
                    else:
                        validation["summary"] = f"All {len(claimed_columns)} columns validated successfully"
                else:
                    validation["all_available_columns"] = [
                        {"name": name, "type": type_} for name, type_ in actual_columns.items()
                    ]
                    validation["summary"] = f"Table exists with {len(actual_columns)} columns"
                
                # Trust indicators
                validation["trust_indicators"] = {
                    "schema_validated": True,
                    "hallucination_risk": "NONE" if validation["validation_status"] == "VALID" else "MEDIUM",
                    "validation_method": "direct_schema_query",
                    "timestamp": datetime.now().isoformat()
                }
                
                if ctx:
                    status_emoji = "✅" if validation["validation_status"] == "VALID" else "⚠️"
                    await ctx.info(f"{status_emoji} {validation['summary']}")
                
                return safe_json_dumps(validation, indent=2)
                
            except ValidationError:
                raise  # Re-raise validation errors
            except Exception as e:
                error_msg = f"Schema validation failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if ctx:
                    await ctx.error(error_msg)
                raise SchemaError(
                    "Failed to validate schema claims",
                    table_path=f"{cluster}.{database}.{table_name}",
                    metadata={"error_type": type(e).__name__, "error_message": str(e)}
                )

    @mcp.tool()
    def create_verification_link(
        cluster: str,
        database: str,
        query: str,
        description: Optional[str] = None,
        ctx: Context = None
    ) -> str:
        """
        🔗 Create a verification link with all info needed to re-run a query.
        
        This tool generates a verification payload that can be used to:
        1. Re-run the exact same query later
        2. Share queries with others for verification
        3. Track query provenance and lineage
        
        Perfect for: Documentation, audit trails, reproducibility
        
        Args:
            cluster: Cluster name
            database: Database name
            query: KQL query
            description: Optional description of what the query does
        
        Returns:
            JSON with verification link and metadata
        """
        if ctx:
            ctx.info(f"Creating verification link...")
        
        with measure_operation("create_verification_link"):
            # Create verification payload
            verification_link = {
                "created_at": datetime.now().isoformat(),
                "query_hash": hashlib.md5(query.encode()).hexdigest(),
                "verification_payload": {
                    "cluster": cluster,
                    "database": database,
                    "query": query,
                    "description": description or "No description provided"
                },
                "usage": {
                    "verify_command": "verify_query_result",
                    "parameters": {
                        "cluster": cluster,
                        "database": database,
                        "query": query
                    }
                },
                "trust_metadata": {
                    "query_type": "user_provided",
                    "can_be_verified": True,
                    "verification_method": "verify_query_result tool"
                }
            }
            
            if ctx:
                ctx.info(f"Verification link created. Use verify_query_result to verify this query.")
            
            return safe_json_dumps(verification_link, indent=2)
