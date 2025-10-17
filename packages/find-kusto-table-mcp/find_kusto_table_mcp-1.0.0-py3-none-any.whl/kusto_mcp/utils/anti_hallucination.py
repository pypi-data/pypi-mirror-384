"""
Anti-hallucination utilities for the Kusto MCP server.

These utilities help prevent AI agents from hallucinating table names,
column names, and query results by providing validation layers.
"""

import re
import hashlib
from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime

from ..core.exceptions import AntiHallucinationError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation

logger = get_logger("validation")


class SchemaValidator:
    """Validates that table and column names exist in actual schema"""
    
    def __init__(self, schema_cache_service):
        self.schema_cache = schema_cache_service
        self.validated_schemas = {}  # Cache of validated schemas
    
    def validate_table_exists(self, cluster: str, database: str, table: str) -> bool:
        """Validate that a table exists"""
        with measure_operation("validate_table_exists"):
            schema = self.schema_cache.get_schema(cluster, database, table)
            return schema is not None
    
    def validate_columns_exist(
        self, 
        cluster: str, 
        database: str, 
        table: str, 
        columns: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Validate that columns exist in a table
        
        Returns:
            (valid_columns, invalid_columns)
        """
        with measure_operation("validate_columns_exist", {'column_count': len(columns)}):
            schema = self.schema_cache.get_schema(cluster, database, table)
            if not schema:
                return [], columns
            
            existing_columns = {col['name'] for col in schema.columns}
            
            valid_columns = []
            invalid_columns = []
            
            for column in columns:
                if column in existing_columns:
                    valid_columns.append(column)
                else:
                    invalid_columns.append(column)
            
            return valid_columns, invalid_columns
    
    def suggest_similar_columns(
        self, 
        cluster: str, 
        database: str, 
        table: str, 
        column: str, 
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Suggest similar column names for typos using multiple similarity metrics.
        
        Uses:
        - Case-insensitive exact matching
        - Substring matching
        - Levenshtein distance (edit distance)
        - Common prefix matching
        """
        schema = self.schema_cache.get_schema(cluster, database, table)
        if not schema:
            return []
        
        existing_columns = [col['name'] for col in schema.columns]
        
        # Calculate similarity scores
        suggestions = []
        column_lower = column.lower()
        
        for existing_col in existing_columns:
            existing_lower = existing_col.lower()
            score = 0
            
            # Exact case-insensitive match (highest priority)
            if column_lower == existing_lower:
                score = 1000
            # Contains the search term (high priority)
            elif column_lower in existing_lower:
                score = 500
            # Search term contains existing column name
            elif existing_lower in column_lower:
                score = 400
            # Common prefix (moderate priority)
            else:
                common_prefix_len = 0
                for i in range(min(len(column_lower), len(existing_lower))):
                    if column_lower[i] == existing_lower[i]:
                        common_prefix_len += 1
                    else:
                        break
                
                if common_prefix_len >= 3:  # At least 3 char prefix match
                    score = common_prefix_len * 10
                
                # Levenshtein distance (simple approximation)
                if score == 0:
                    # Calculate edit distance (simplified)
                    len_diff = abs(len(column_lower) - len(existing_lower))
                    if len_diff <= 3:  # Close in length
                        score = max(0, 100 - len_diff * 20)
            
            if score > 0:
                suggestions.append((score, existing_col))
        
        # Sort by score (descending) and return top N
        suggestions.sort(key=lambda x: x[0], reverse=True)
        return [col for _, col in suggestions[:max_suggestions]]


class QueryValidator:
    """Validates KQL queries for potential issues"""
    
    def __init__(self):
        self.dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'TRUNCATE\s+TABLE',
            r'ALTER\s+TABLE',
            r'CREATE\s+TABLE'
        ]
        
        self.suspicious_patterns = [
            r'\*\s*FROM\s+\w+\s*$',  # SELECT * without LIMIT
            r'WHERE\s+1\s*=\s*1',    # Always true condition
            r'UNION\s+ALL.*UNION\s+ALL',  # Multiple UNIONs (potential injection)
        ]
    
    def validate_query_safety(self, query: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate query for safety issues
        
        Returns:
            (is_safe, errors, warnings)
        """
        with measure_operation("validate_query_safety"):
            errors = []
            warnings = []
            
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    errors.append(f"Dangerous operation detected: {pattern}")
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    warnings.append(f"Suspicious pattern detected: {pattern}")
            
            # Check for balanced parentheses
            if query.count('(') != query.count(')'):
                errors.append("Unbalanced parentheses in query")
            
            # Check for balanced quotes
            single_quotes = query.count("'")
            if single_quotes % 2 != 0:
                errors.append("Unbalanced single quotes in query")
            
            is_safe = len(errors) == 0
            return is_safe, errors, warnings
    
    def extract_table_references(self, query: str) -> List[str]:
        """Extract table references from KQL query"""
        # Enhanced pattern matching for KQL table references
        patterns = [
            r'^(\w+(?:\.\w+)?(?:\.\w+)?)',  # Start of query: table or database.table or cluster.database.table
            r'FROM\s+(\w+(?:\.\w+)?(?:\.\w+)?)',  # FROM clause
            r'JOIN\s+(\w+(?:\.\w+)?(?:\.\w+)?)',  # JOIN clause
            r'\|\s*union\s+(\w+(?:\.\w+)?)',  # UNION operator
            r'materialize\s*\(\s*(\w+(?:\.\w+)?)',  # materialize() function
        ]
        
        table_refs = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE | re.MULTILINE)
            table_refs.update(matches)
        
        return list(table_refs)
    
    def extract_column_references(self, query: str) -> List[str]:
        """
        Extract column references from KQL query.
        
        Returns list of potential column names referenced in the query.
        This is more sophisticated than simple regex matching.
        """
        # Patterns for column references in KQL
        patterns = [
            r'(\w+)\s*[=<>!]=',  # Comparison operators
            r'(\w+)\s*(?:contains|startswith|endswith|has|in)',  # String operators
            r'(?:where|and|or)\s+(\w+)',  # After where/and/or
            r'(?:project|extend|summarize)\s+(\w+)',  # After project/extend/summarize
            r'by\s+(\w+)',  # Group by column
            r'sort\s+by\s+(\w+)',  # Sort by column
            r'\[\s*["\'](\w+)["\']\s*\]',  # Bracket notation: ["ColumnName"]
        ]
        
        column_refs = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    column_refs.update(m for m in match if m)
                else:
                    column_refs.add(match)
        
        # Remove KQL keywords and functions (common false positives)
        kql_keywords = {
            'ago', 'now', 'datetime', 'timespan', 'bin', 'count', 'sum', 'avg', 
            'min', 'max', 'where', 'and', 'or', 'not', 'true', 'false', 'null',
            'let', 'set', 'print', 'take', 'limit', 'top', 'distinct', 'join',
            'union', 'range', 'evaluate', 'invoke', 'render', 'sort', 'order',
            'project', 'extend', 'summarize', 'mv-expand', 'mv-apply'
        }
        
        return [col for col in column_refs if col.lower() not in kql_keywords]


class ResultValidator:
    """Validates query results for consistency"""
    
    def __init__(self):
        self.result_signatures = {}  # Cache of result signatures
    
    def generate_result_signature(self, results: List[Dict[str, Any]]) -> str:
        """Generate a signature for query results"""
        if not results:
            return "empty"
        
        # Create signature based on column names and types
        first_row = results[0]
        columns = sorted(first_row.keys())
        
        signature_data = {
            'columns': columns,
            'row_count': len(results),
            'sample_values': {
                col: str(first_row.get(col, ''))[:50]  # First 50 chars of sample values
                for col in columns[:10]  # First 10 columns
            }
        }
        
        signature_str = str(signature_data)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def validate_result_consistency(
        self, 
        query: str, 
        results: List[Dict[str, Any]],
        expected_columns: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate that results are consistent with expectations
        
        Returns:
            (is_consistent, warnings)
        """
        with measure_operation("validate_result_consistency"):
            warnings = []
            
            if not results:
                warnings.append("Query returned no results")
                return True, warnings
            
            # Check column consistency across rows
            first_row_columns = set(results[0].keys())
            
            for i, row in enumerate(results[1:10]):  # Check first 10 rows
                row_columns = set(row.keys())
                if row_columns != first_row_columns:
                    warnings.append(f"Column inconsistency in row {i+1}")
            
            # Validate expected columns if provided
            if expected_columns:
                actual_columns = set(results[0].keys())
                expected_set = set(expected_columns)
                
                missing_columns = expected_set - actual_columns
                if missing_columns:
                    warnings.append(f"Missing expected columns: {list(missing_columns)}")
                
                extra_columns = actual_columns - expected_set
                if extra_columns:
                    warnings.append(f"Unexpected columns: {list(extra_columns)}")
            
            # Check for suspicious data patterns
            if len(results) > 10000:
                warnings.append(f"Large result set: {len(results)} rows - consider adding LIMIT")
            
            return True, warnings


class HallucinationDetector:
    """Detects potential AI hallucination in queries and responses"""
    
    def __init__(self, schema_validator: SchemaValidator):
        self.schema_validator = schema_validator
        self.common_hallucinated_tables = {
            'Events', 'Logs', 'Metrics', 'Users', 'Sessions', 'Requests',
            'Errors', 'Traces', 'Performance', 'Security', 'Audit'
        }
        
        self.common_hallucinated_columns = {
            'id', 'timestamp', 'datetime', 'user_id', 'session_id',
            'event_type', 'message', 'level', 'source', 'target'
        }
    
    def detect_table_hallucination(
        self, 
        query: str, 
        available_tables: Set[str]
    ) -> Tuple[bool, List[str]]:
        """
        Detect if query references hallucinated tables
        
        Returns:
            (hallucination_detected, issues)
        """
        with measure_operation("detect_table_hallucination"):
            issues = []
            
            # Extract table references from query
            query_validator = QueryValidator()
            table_refs = query_validator.extract_table_references(query)
            
            for table_ref in table_refs:
                # Check if table exists in available tables
                if table_ref not in available_tables:
                    # Check if it's a commonly hallucinated name
                    table_name = table_ref.split('.')[-1]  # Get just the table name
                    if table_name in self.common_hallucinated_tables:
                        issues.append(f"Potentially hallucinated table: {table_ref} (common hallucination pattern)")
                    else:
                        issues.append(f"Unknown table reference: {table_ref}")
            
            return len(issues) > 0, issues
    
    def detect_column_hallucination(
        self,
        cluster: str,
        database: str,
        table: str,
        referenced_columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Detect if query references hallucinated columns
        
        Returns:
            (hallucination_detected, issues)
        """
        with measure_operation("detect_column_hallucination"):
            issues = []
            
            valid_columns, invalid_columns = self.schema_validator.validate_columns_exist(
                cluster, database, table, referenced_columns
            )
            
            for invalid_col in invalid_columns:
                # Suggest similar columns
                suggestions = self.schema_validator.suggest_similar_columns(
                    cluster, database, table, invalid_col
                )
                
                if suggestions:
                    issues.append(f"Column '{invalid_col}' not found. Did you mean: {', '.join(suggestions)}?")
                elif invalid_col.lower() in self.common_hallucinated_columns:
                    issues.append(f"Column '{invalid_col}' not found (common hallucination pattern)")
                else:
                    issues.append(f"Column '{invalid_col}' not found in table {table}")
            
            return len(issues) > 0, issues
    
    def validate_query_against_schema(
        self,
        query: str,
        cluster: str,
        database: str,
        table: str
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Comprehensive validation of query against actual schema.
        
        Uses improved column extraction to identify all column references
        in the query and validates them against the actual schema.
        
        Returns:
            (is_valid, errors, warnings)
        """
        with measure_operation("validate_query_against_schema"):
            errors = []
            warnings = []
            
            # Validate table exists
            if not self.schema_validator.validate_table_exists(cluster, database, table):
                errors.append(f"Table {cluster}.{database}.{table} does not exist")
                return False, errors, warnings
            
            # Use improved column extraction from QueryValidator
            query_validator = QueryValidator()
            referenced_columns = query_validator.extract_column_references(query)
            
            if referenced_columns:
                hallucination_detected, issues = self.detect_column_hallucination(
                    cluster, database, table, referenced_columns
                )
                
                if hallucination_detected:
                    errors.extend(issues)
            else:
                warnings.append("No column references detected in query - validation skipped")
            
            return len(errors) == 0, errors, warnings


def create_anti_hallucination_guard(schema_cache_service) -> HallucinationDetector:
    """Create and configure anti-hallucination guard"""
    schema_validator = SchemaValidator(schema_cache_service)
    return HallucinationDetector(schema_validator)