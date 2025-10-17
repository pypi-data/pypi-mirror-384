"""
AI-Powered KQL Query Builder with Iterative Validation

Inspired by enhanced-ado-mcp's successful sampling-based query generation approach.
This tool uses AI to generate queries, validates them by execution, and refines
them iteratively to prevent hallucination issues.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..core.exceptions import ValidationError, QueryError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.kusto_client import get_connection_manager
from ..utils.anti_hallucination import create_anti_hallucination_guard
from ..services.schema_cache_service import get_schema_cache_service
from ..services.query_handle_service import get_query_handle_service
from ..tools.query_sampler_simple import create_query_sampler

logger = get_logger("ai_query_builder")


class AIQueryBuilder:
    """
    AI-powered query builder with iterative validation
    
    Key Features:
    - Generates KQL queries based on natural language intent
    - Validates queries by actual execution with limits
    - Refines queries on errors iteratively
    - Returns query handles by default to prevent context pollution
    - Prevents hallucination through validation loops
    """
    
    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.schema_cache = get_schema_cache_service()
        self.query_handle_service = get_query_handle_service()
        self.query_sampler = create_query_sampler()
        self.hallucination_guard = create_anti_hallucination_guard(self.schema_cache)
        
        # Configuration
        self.max_iterations = 3  # Maximum refinement attempts
        self.validation_row_limit = 10  # Rows to fetch for validation
    
    async def build_query_from_intent(
        self,
        cluster: str,
        database: str,
        table: str,
        user_intent: str,
        return_handle: bool = True,
        max_iterations: Optional[int] = None,
        ctx = None
    ) -> Dict[str, Any]:
        """
        Build and validate a KQL query from natural language intent
        
        Args:
            cluster: Target cluster
            database: Target database
            table: Target table
            user_intent: Natural language description of query intent
            return_handle: If True, return query handle instead of raw data
            max_iterations: Override default max iterations
            ctx: FastMCP context for AI-powered generation (optional)
            
        Returns:
            Dictionary with query, validation info, and optionally handle/results
        """
        with measure_operation("build_query_from_intent", {
            "table": f"{cluster}.{database}.{table}",
            "intent_length": len(user_intent)
        }):
            iterations = max_iterations or self.max_iterations
            
            # Step 1: Sample table to understand structure
            logger.info(f"Sampling table {cluster}.{database}.{table} for query building")
            sample_info = await self.query_sampler.sample_table_for_query_building(
                cluster, database, table, sample_size=20, include_schema=True
            )
            
            # Step 2: Generate initial query
            logger.info(f"Generating initial query for intent: {user_intent[:100]}")
            current_query = await self._generate_query(
                cluster, database, table, user_intent, sample_info, iteration=0, ctx=ctx
            )
            
            validation_history = []
            last_error = None
            
            # Step 3: Iterative validation and refinement
            for iteration in range(iterations):
                logger.info(f"Validation iteration {iteration + 1}/{iterations}")
                
                # Validate query by execution
                valid, execution_result, error = await self._validate_query_by_execution(
                    cluster, database, table, current_query
                )
                
                validation_history.append({
                    'iteration': iteration + 1,
                    'query': current_query,
                    'valid': valid,
                    'error': error
                })
                
                if valid:
                    logger.info(f"Query validated successfully on iteration {iteration + 1}")
                    break
                
                last_error = error
                logger.warning(f"Query validation failed on iteration {iteration + 1}: {error}")
                
                # Refine query if not last iteration
                if iteration < iterations - 1:
                    logger.info(f"Refining query based on error: {error}")
                    current_query = await self._refine_query(
                        cluster, database, table, current_query, error, 
                        sample_info, user_intent, iteration + 1, ctx=ctx
                    )
            
            # Step 4: Build result
            result = {
                'success': valid,
                'query': current_query,
                'table_path': f"{cluster}.{database}.{table}",
                'user_intent': user_intent,
                'iterations': len(validation_history),
                'validation_history': validation_history
            }
            
            if not valid:
                result['error'] = last_error
                result['message'] = f"Failed to generate valid query after {iterations} iterations"
                return result
            
            # Step 5: Execute query and return handle or results
            if return_handle:
                # Execute with limit and store in handle
                limited_query = self._add_limit_if_missing(current_query, 1000)
                
                results, columns = await self.connection_manager.execute_query(
                    cluster, database, limited_query
                )
                
                # Store in handle
                handle = self.query_handle_service.store_query_results(
                    query=current_query,
                    table_path=f"{cluster}.{database}.{table}",
                    cluster=cluster,
                    database=database,
                    table=table,
                    results=results,
                    columns=columns,
                    execution_time_ms=0.0  # Not tracking here
                )
                
                result['handle'] = handle
                result['row_count'] = len(results)
                result['message'] = f"Query executed successfully, {len(results)} rows cached in handle {handle}"
            else:
                result['message'] = "Query validated successfully"
            
            return result
    
    async def _generate_query(
        self,
        cluster: str,
        database: str,
        table: str,
        user_intent: str,
        sample_info: Dict[str, Any],
        iteration: int,
        ctx = None
    ) -> str:
        """Generate KQL query using AI or fallback to rules."""
        # Try AI-powered generation first if ctx available
        if ctx and hasattr(ctx, 'sample'):
            try:
                from ..utils.sampling_client import SamplingClient
                
                sampling_client = SamplingClient(ctx)
                
                # Extract schema information
                schema_dict = sample_info.get('schema', {})
                all_columns = schema_dict.get('all_columns', [])
                time_columns = schema_dict.get('time_columns', [])
                primary_time_column = time_columns[0] if time_columns else None
                
                # Generate query using AI
                logger.info("Attempting AI-powered query generation")
                result = await sampling_client.generate_query_with_ai(
                    user_request=user_intent,
                    cluster=cluster,
                    database=database,
                    table=table,
                    schema=schema_dict,
                    columns=all_columns,
                    time_columns=time_columns,
                    primary_time_column=primary_time_column
                )
                
                logger.info(f"AI generated query with confidence: {result.get('confidence', 'unknown')}")
                return result['query']
                
            except Exception as e:
                logger.warning(f"AI query generation failed, falling back to rule-based: {str(e)}")
                # Fall through to rule-based generation
        
        # FALLBACK: Rule-based query generation
        logger.info("Using rule-based query generation (AI unavailable)")
        # Extract useful information from sample
        schema = sample_info.get('schema', {})
        analysis = sample_info.get('analysis', {})
        sample_rows = sample_info.get('sample_rows', [])
        
        # Simple rule-based query generation based on intent keywords
        query_parts = [table]
        
        intent_lower = user_intent.lower()
        
        # Time filtering
        if 'recent' in intent_lower or 'last' in intent_lower or 'ago' in intent_lower:
            time_cols = schema.get('time_columns', [])
            if time_cols:
                time_col = time_cols[0]
                if 'hour' in intent_lower:
                    query_parts.append(f"| where {time_col} > ago(1h)")
                elif 'day' in intent_lower:
                    query_parts.append(f"| where {time_col} > ago(1d)")
                else:
                    query_parts.append(f"| where {time_col} > ago(24h)")
        
        # Aggregation
        if 'count' in intent_lower or 'total' in intent_lower or 'sum' in intent_lower:
            if 'by' in intent_lower or 'per' in intent_lower or 'group' in intent_lower:
                # Try to find good grouping column
                recommendations = analysis.get('recommendations', [])
                grouping_cols = []
                
                for rec in recommendations:
                    if 'Good grouping columns:' in rec:
                        cols_str = rec.split(':')[1].strip()
                        grouping_cols = [c.strip() for c in cols_str.split(',')]
                        break
                
                if grouping_cols:
                    query_parts.append(f"| summarize count() by {grouping_cols[0]}")
                else:
                    # Fallback to first string column
                    string_cols = schema.get('string_columns', [])
                    if string_cols:
                        query_parts.append(f"| summarize count() by {string_cols[0]}")
            else:
                query_parts.append("| summarize count()")
        
        # Filtering by column values (simple keyword matching)
        for word in intent_lower.split():
            if word in ['where', 'filter', 'contains']:
                # Add a basic where clause based on sample data
                string_cols = schema.get('string_columns', [])
                if string_cols and sample_rows:
                    first_col = string_cols[0]
                    # Use a sample value
                    sample_val = sample_rows[0].get(first_col, '')
                    if sample_val:
                        query_parts.append(f"| where {first_col} contains '{sample_val}'")
                break
        
        # Top N
        if 'top' in intent_lower or 'limit' in intent_lower:
            import re
            numbers = re.findall(r'\d+', user_intent)
            if numbers:
                query_parts.append(f"| take {numbers[0]}")
            else:
                query_parts.append("| take 100")
        elif '| take' not in ' '.join(query_parts).lower():
            # Always add a default limit for safety
            query_parts.append("| take 100")
        
        query = '\n'.join(query_parts)
        
        logger.debug(f"Generated query (iteration {iteration}): {query}")
        return query
    
    async def _validate_query_by_execution(
        self,
        cluster: str,
        database: str,
        table: str,
        query: str
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Validate query by executing it with a small limit
        
        Returns:
            (is_valid, results, error_message)
        """
        try:
            # Add limit to query for validation
            validation_query = self._add_limit_if_missing(query, self.validation_row_limit)
            
            # Execute query
            results, columns = await self.connection_manager.execute_query(
                cluster, database, validation_query
            )
            
            # Success!
            return True, results, None
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Query validation failed: {error_msg}")
            return False, None, error_msg
    
    async def _refine_query(
        self,
        cluster: str,
        database: str,
        table: str,
        current_query: str,
        error: str,
        sample_info: Dict[str, Any],
        user_intent: str,
        iteration: int,
        ctx = None
    ) -> str:
        """Refine query using AI or fallback to rules."""
        # Try AI-powered refinement first if ctx available
        if ctx and hasattr(ctx, 'sample'):
            try:
                from ..utils.sampling_client import SamplingClient
                
                sampling_client = SamplingClient(ctx)
                
                # Extract schema information
                schema_dict = sample_info.get('schema', {})
                
                # Refine query using AI
                logger.info("Attempting AI-powered query refinement")
                result = await sampling_client.refine_query(
                    original_query=current_query,
                    error_message=error,
                    cluster=cluster,
                    database=database,
                    table=table,
                    schema=schema_dict,
                    user_intent=user_intent,
                    attempt_count=iteration
                )
                
                logger.info(f"AI refined query with confidence: {result.get('confidence', 'unknown')}")
                return result['refined_query']
                
            except Exception as e:
                logger.warning(f"AI query refinement failed, falling back to rule-based: {str(e)}")
                # Fall through to rule-based refinement
        
        # FALLBACK: Rule-based refinement
        logger.info("Using rule-based query refinement (AI unavailable)")
        # Simple error-based corrections
        error_lower = error.lower()
        
        # Column name errors
        if 'column' in error_lower or 'field' in error_lower or 'not found' in error_lower:
            # Try to extract column name from error
            import re
            quoted = re.findall(r"'([^']+)'", error)
            
            if quoted:
                bad_column = quoted[0]
                schema = sample_info.get('schema', {})
                all_columns = schema.get('columns', [])
                
                # Find similar column
                from ..utils.helpers import calculate_similarity
                
                best_match = None
                best_score = 0
                
                for col in all_columns:
                    col_name = col['name']
                    score = calculate_similarity(bad_column, col_name)
                    if score > best_score:
                        best_score = score
                        best_match = col_name
                
                if best_match and best_score > 0.5:
                    # Replace bad column with best match
                    refined_query = current_query.replace(bad_column, best_match)
                    logger.info(f"Replaced column '{bad_column}' with '{best_match}'")
                    return refined_query
        
        # Syntax errors - try simplifying
        if 'syntax' in error_lower or 'parse' in error_lower:
            # Remove complex parts and try again
            lines = current_query.split('\n')
            if len(lines) > 2:
                # Remove last pipe operation
                refined_query = '\n'.join(lines[:-1])
                logger.info(f"Simplified query by removing last operation")
                return refined_query
        
        # Fallback: regenerate from scratch
        logger.info(f"Regenerating query from scratch for iteration {iteration}")
        return await self._generate_query(
            cluster, database, table, user_intent, sample_info, iteration, ctx=ctx
        )
    
    def _add_limit_if_missing(self, query: str, limit: int) -> str:
        """Add a TAKE/LIMIT clause if query doesn't have one"""
        query_lower = query.lower()
        
        if 'take' not in query_lower and 'limit' not in query_lower:
            return f"{query}\n| take {limit}"
        
        return query
    
    async def suggest_query_improvements(
        self,
        cluster: str,
        database: str,
        table: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Analyze a query and suggest improvements
        
        Wrapper around query_sampler's suggest_query_improvements
        """
        return await self.query_sampler.suggest_query_improvements(
            cluster, database, table, query
        )


def create_ai_query_builder() -> AIQueryBuilder:
    """Create and configure AI query builder"""
    return AIQueryBuilder()
