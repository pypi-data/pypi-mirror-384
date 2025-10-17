"""
Sampling client for VS Code Language Model API integration.

This module provides a client wrapper for calling VS Code's Language Model API
to generate KQL queries, analyze table samples, and refine queries based on errors.

Based on the pattern from enhanced-ado-mcp's SamplingClient.
"""

import json
from typing import Any, Dict, Optional
from pathlib import Path

from src.core.logging_config import get_logger
from src.core.exceptions import QueryError

logger = get_logger(__name__)


def get_system_prompts_dir() -> Path:
    """Get the path to the system prompts directory."""
    project_root = Path(__file__).parent.parent.parent
    system_prompts_dir = project_root / "prompts" / "system"
    
    if not system_prompts_dir.exists():
        raise FileNotFoundError(
            f"System prompts directory not found at {system_prompts_dir}. "
            "Please ensure prompts/system/ directory exists."
        )
    
    return system_prompts_dir


def load_system_prompt(prompt_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Load a system prompt and substitute template variables.
    
    Args:
        prompt_name: Name of the system prompt file (without .md extension)
        variables: Dictionary of template variables to substitute (e.g., {{CLUSTER}})
        
    Returns:
        The prompt content with variables substituted
        
    Example:
        >>> prompt = load_system_prompt("kql_query_generator", {
        ...     "CLUSTER": "myCluster",
        ...     "DATABASE": "myDB",
        ...     "TABLE": "myTable"
        ... })
    """
    system_prompts_dir = get_system_prompts_dir()
    prompt_file = system_prompts_dir / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"System prompt file not found: {prompt_file}"
        )
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitute template variables if provided
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"  # {{KEY}} format
            # Convert value to string, handling None and complex types
            str_value = "" if value is None else str(value)
            content = content.replace(placeholder, str_value)
    
    return content


class SamplingClient:
    """
    Client for interacting with VS Code Language Model API through fastmcp's sampling.
    
    This client provides a pattern similar to enhanced-ado-mcp's SamplingClient,
    adapted for the Kusto/KQL context using fastmcp's sampling capabilities.
    """
    
    def __init__(self, ctx):
        """
        Initialize the sampling client.
        
        Args:
            ctx: FastMCP context object with sampling capabilities
        """
        self.ctx = ctx
        self.max_attempts = 3
        self.default_max_tokens = 4000
        self.default_temperature = 0.1  # Low temperature for consistent, deterministic output
        
    async def create_message(
        self,
        system_prompt_name: str,
        user_content: str,
        variables: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Create and send a message to the VS Code Language Model API.
        
        Args:
            system_prompt_name: Name of system prompt file (e.g., "kql_query_generator")
            user_content: User message content
            variables: Template variables for the system prompt
            max_tokens: Maximum tokens for the response (default: 4000)
            temperature: Temperature for sampling (default: 0.1)
            
        Returns:
            The model's response text
            
        Raises:
            QueryError: If the API call fails or returns invalid response
        """
        try:
            # Load and prepare system prompt
            system_prompt = load_system_prompt(system_prompt_name, variables)
            
            # Use provided values or defaults
            max_tokens = max_tokens or self.default_max_tokens
            temperature = temperature or self.default_temperature
            
            logger.info(
                f"Calling language model with system prompt: {system_prompt_name}, "
                f"max_tokens={max_tokens}, temperature={temperature}"
            )
            
            # Call VS Code LM API through fastmcp's sampling
            response = await self.ctx.sample(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response text
            response_text = self._extract_response_text(response)
            
            logger.debug(f"Received response from language model: {response_text[:200]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to call language model API: {str(e)}")
            raise QueryError(f"Language model API call failed: {str(e)}")
    
    def _extract_response_text(self, response: Any) -> str:
        """
        Extract text from the language model response.
        
        Args:
            response: Response object from ctx.sample()
            
        Returns:
            Extracted response text
        """
        # Handle different response formats
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            # Try common response keys
            if "text" in response:
                return response["text"]
            elif "content" in response:
                return response["content"]
            elif "message" in response:
                msg = response["message"]
                if isinstance(msg, dict) and "content" in msg:
                    return msg["content"]
                elif isinstance(msg, str):
                    return msg
        
        # If we can't extract text, return the string representation
        return str(response)
    
    async def generate_query_with_ai(
        self,
        user_request: str,
        cluster: str,
        database: str,
        table: str,
        schema: Dict[str, str],
        columns: Optional[list[str]] = None,
        time_columns: Optional[list[str]] = None,
        primary_time_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a KQL query using AI with iterative refinement.
        
        This implements the 3-attempt pattern from enhanced-ado-mcp:
        1. Initial generation attempt
        2. If fails, provide error feedback and retry
        3. If fails again, provide more context and retry
        
        Args:
            user_request: Natural language description of what query should do
            cluster: Kusto cluster name
            database: Database name
            table: Table name
            schema: Table schema (column_name -> data_type mapping)
            columns: Optional list of interesting columns
            time_columns: Optional list of datetime columns
            primary_time_column: Optional primary time column for filtering
            
        Returns:
            Dictionary with:
                - query: Generated KQL query string
                - explanation: Human-readable explanation
                - confidence: high/medium/low
                - attempts: Number of generation attempts
        """
        variables = {
            "CLUSTER": cluster,
            "DATABASE": database,
            "TABLE": table,
            "SCHEMA": json.dumps(schema, indent=2),
            "COLUMNS": ", ".join(columns) if columns else "N/A",
            "TIME_COLUMNS": ", ".join(time_columns) if time_columns else "N/A",
            "PRIMARY_TIME_COLUMN": primary_time_column or "N/A"
        }
        
        user_content = f"""Generate a KQL query for the following request:

{user_request}

Requirements:
- Query must be valid KQL syntax
- Use only columns that exist in the schema
- Include appropriate time filters for performance
- Add result limits (| take N) to prevent overwhelming results
- Follow KQL best practices

Return the query in JSON format:
{{
  "query": "TableName | where ...",
  "explanation": "This query does X by...",
  "confidence": "high|medium|low"
}}
"""
        
        last_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"Query generation attempt {attempt}/{self.max_attempts}")
                
                # Add error feedback to user content if this is a retry
                if last_error:
                    user_content = f"""{user_content}

PREVIOUS ATTEMPT FAILED:
Error: {last_error}

Please fix the error and generate a corrected query.
"""
                
                # Call language model
                response_text = await self.create_message(
                    system_prompt_name="kql_query_generator",
                    user_content=user_content,
                    variables=variables
                )
                
                # Parse JSON response
                result = self._parse_json_response(response_text)
                
                # Add attempt count to result
                result["attempts"] = attempt
                
                logger.info(f"Successfully generated query on attempt {attempt}")
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Query generation attempt {attempt} failed: {last_error}")
                
                if attempt >= self.max_attempts:
                    # All attempts failed
                    logger.error(f"Failed to generate query after {self.max_attempts} attempts")
                    raise QueryError(
                        f"Failed to generate query after {self.max_attempts} attempts. "
                        f"Last error: {last_error}"
                    )
        
        # Should never reach here, but just in case
        raise QueryError("Query generation failed unexpectedly")
    
    async def analyze_table_sample(
        self,
        cluster: str,
        database: str,
        table: str,
        schema: Dict[str, str],
        sample_data: list[Dict[str, Any]],
        sample_size: int
    ) -> Dict[str, Any]:
        """
        Analyze a table sample and provide intelligent insights.
        
        Args:
            cluster: Kusto cluster name
            database: Database name
            table: Table name
            schema: Table schema (column_name -> data_type mapping)
            sample_data: Sample rows from the table
            sample_size: Number of rows in the sample
            
        Returns:
            Dictionary with analysis results including column insights,
            recommended queries, data characteristics, and performance tips
        """
        variables = {
            "CLUSTER": cluster,
            "DATABASE": database,
            "TABLE": table,
            "SCHEMA": json.dumps(schema, indent=2),
            "SAMPLE_DATA": json.dumps(sample_data, indent=2, default=str),
            "SAMPLE_SIZE": str(sample_size)
        }
        
        user_content = """Analyze this table sample and provide insights.

Return your analysis in the JSON format specified in the system prompt, including:
- column_insights: Analysis of each column
- recommended_queries: Suggested useful queries
- data_characteristics: Overall data patterns
- performance_tips: Query optimization suggestions
- query_building_guidance: Step-by-step query building advice
"""
        
        response_text = await self.create_message(
            system_prompt_name="intelligent_table_sampler",
            user_content=user_content,
            variables=variables,
            max_tokens=6000  # Larger for detailed analysis
        )
        
        return self._parse_json_response(response_text)
    
    async def refine_query(
        self,
        original_query: str,
        error_message: str,
        cluster: str,
        database: str,
        table: str,
        schema: Dict[str, str],
        user_intent: str,
        attempt_count: int
    ) -> Dict[str, Any]:
        """
        Refine a failed query based on error feedback.
        
        Args:
            original_query: The query that failed
            error_message: Error message from the failed query
            cluster: Kusto cluster name
            database: Database name
            table: Table name
            schema: Table schema
            user_intent: Original user request
            attempt_count: Current attempt number
            
        Returns:
            Dictionary with refined_query, changes_made, error_diagnosis, etc.
        """
        variables = {
            "ORIGINAL_QUERY": original_query,
            "ERROR_MESSAGE": error_message,
            "CLUSTER": cluster,
            "DATABASE": database,
            "TABLE": table,
            "SCHEMA": json.dumps(schema, indent=2),
            "USER_INTENT": user_intent,
            "ATTEMPT_COUNT": str(attempt_count)
        }
        
        user_content = f"""Fix this failed query:

Original Query:
{original_query}

Error:
{error_message}

User Intent:
{user_intent}

Return your refinement in the JSON format specified in the system prompt.
"""
        
        response_text = await self.create_message(
            system_prompt_name="kql_query_refiner",
            user_content=user_content,
            variables=variables
        )
        
        return self._parse_json_response(response_text)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from the language model response.
        
        Handles responses that may have JSON wrapped in markdown code blocks.
        
        Args:
            response_text: Raw response text from the language model
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            QueryError: If JSON parsing fails
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Check for ```json or ``` wrappers
        if text.startswith("```"):
            # Find the content between ``` markers
            lines = text.split("\n")
            # Skip first line (```json or ```)
            start_idx = 1
            # Find closing ```
            end_idx = len(lines)
            for i in range(1, len(lines)):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            text = "\n".join(lines[start_idx:end_idx])
        
        # Try to parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise QueryError(
                f"Failed to parse language model response as JSON: {str(e)}"
            )
