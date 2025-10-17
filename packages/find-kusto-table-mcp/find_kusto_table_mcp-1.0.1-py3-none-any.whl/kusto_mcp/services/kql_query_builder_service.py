"""
KQL Query Builder with Sampling

Helps write working KQL queries by sampling table data to discover actual
schema and validate queries before execution. Prevents AI hallucination
of column names and query syntax.

Key features:
- Sample-based schema discovery
- Query validation before execution
- Safe query building with actual column names
- Context-efficient (small samples, not full results)
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TableSample:
    """Sample data from a table"""
    table_path: str
    cluster: str
    database: str
    table: str
    sample_rows: List[Dict[str, Any]]
    columns: List[Dict[str, str]]  # [{'name': 'col', 'type': 'string'}, ...]
    sample_size: int
    total_row_count: Optional[int]
    sampled_at: str
    
    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        return [col['name'] for col in self.columns]
    
    def get_column_types(self) -> Dict[str, str]:
        """Get mapping of column names to types"""
        return {col['name']: col['type'] for col in self.columns}
    
    def get_time_columns(self) -> List[str]:
        """Get list of datetime columns"""
        return [
            col['name'] for col in self.columns
            if 'datetime' in col['type'].lower() or 'timestamp' in col['type'].lower()
        ]
    
    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns"""
        numeric_types = ['int', 'long', 'real', 'decimal', 'double', 'float']
        return [
            col['name'] for col in self.columns
            if any(t in col['type'].lower() for t in numeric_types)
        ]
    
    def get_string_columns(self) -> List[str]:
        """Get list of string columns"""
        return [
            col['name'] for col in self.columns
            if 'string' in col['type'].lower()
        ]
    
    def find_column_by_pattern(self, pattern: str) -> List[str]:
        """Find columns matching a pattern (case-insensitive)"""
        pattern_lower = pattern.lower()
        return [
            col['name'] for col in self.columns
            if pattern_lower in col['name'].lower()
        ]


@dataclass
class QueryValidationResult:
    """Result of query validation"""
    valid: bool
    query: str
    errors: List[str]
    warnings: List[str]
    sample_result_count: Optional[int] = None
    sample_results: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[float] = None


class QueryBuilder:
    """
    Helper class for building KQL queries with actual column names
    """
    
    def __init__(self, sample: TableSample):
        self.sample = sample
        self.table_path = sample.table_path
        self.columns = sample.get_column_names()
        self.time_columns = sample.get_time_columns()
        self.numeric_columns = sample.get_numeric_columns()
        self.string_columns = sample.get_string_columns()
    
    def validate_column(self, column_name: str) -> Tuple[bool, Optional[str]]:
        """Validate that a column exists"""
        if column_name in self.columns:
            return True, None
        
        # Suggest similar columns
        similar = [c for c in self.columns if column_name.lower() in c.lower()]
        if similar:
            return False, f"Column '{column_name}' not found. Did you mean: {', '.join(similar[:3])}?"
        
        return False, f"Column '{column_name}' not found in table"
    
    def build_select_query(
        self,
        columns: Optional[List[str]] = None,
        limit: int = 100
    ) -> Tuple[bool, str, List[str]]:
        """
        Build a SELECT query with specified columns
        
        Args:
            columns: List of column names (None = all columns)
            limit: Row limit
        
        Returns:
            (success, query, errors)
        """
        errors = []
        
        if columns:
            # Validate all columns
            for col in columns:
                valid, error = self.validate_column(col)
                if not valid:
                    errors.append(error)
            
            if errors:
                return False, "", errors
            
            query = f"{self.table_path}\n| project {', '.join(columns)}\n| take {limit}"
        else:
            query = f"{self.table_path}\n| take {limit}"
        
        return True, query, []
    
    def build_time_range_query(
        self,
        time_column: Optional[str] = None,
        timespan: str = "1h",
        limit: int = 100
    ) -> Tuple[bool, str, List[str]]:
        """
        Build a time-range filtered query
        
        Args:
            time_column: Time column name (auto-detect if None)
            timespan: Time range (e.g., "1h", "24h", "7d")
            limit: Row limit
        
        Returns:
            (success, query, errors)
        """
        errors = []
        
        # Auto-detect time column if not specified
        if not time_column:
            if not self.time_columns:
                return False, "", ["No datetime columns found in table. Specify column name explicitly."]
            time_column = self.time_columns[0]  # Use first time column
        else:
            # Validate specified column
            valid, error = self.validate_column(time_column)
            if not valid:
                errors.append(error)
            elif time_column not in self.time_columns:
                errors.append(f"Column '{time_column}' is not a datetime type")
        
        if errors:
            return False, "", errors
        
        query = f"{self.table_path}\n| where {time_column} > ago({timespan})\n| take {limit}"
        return True, query, []
    
    def build_aggregation_query(
        self,
        group_by_columns: List[str],
        aggregations: List[Dict[str, str]],  # [{'func': 'count', 'column': 'col1', 'alias': 'total'}, ...]
        time_column: Optional[str] = None,
        time_bin: Optional[str] = None,  # e.g., "5m", "1h"
        timespan: Optional[str] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Build an aggregation query
        
        Args:
            group_by_columns: Columns to group by
            aggregations: Aggregation functions to apply
            time_column: Optional time column for time-binning
            time_bin: Time bin size (e.g., "5m", "1h")
            timespan: Optional time range filter
        
        Returns:
            (success, query, errors)
        """
        errors = []
        
        # Validate group_by columns
        for col in group_by_columns:
            valid, error = self.validate_column(col)
            if not valid:
                errors.append(error)
        
        # Validate aggregation columns
        for agg in aggregations:
            if 'column' in agg and agg['column']:
                valid, error = self.validate_column(agg['column'])
                if not valid:
                    errors.append(error)
        
        if errors:
            return False, "", errors
        
        # Build query
        query_parts = [self.table_path]
        
        # Add time filter if specified
        if timespan and time_column:
            query_parts.append(f"| where {time_column} > ago({timespan})")
        
        # Build summarize clause
        agg_clauses = []
        for agg in aggregations:
            func = agg.get('func', 'count')
            column = agg.get('column', '')
            alias = agg.get('alias', f"{func}_{column}".replace(' ', '_'))
            
            if func == 'count':
                agg_clauses.append(f"{alias}=count()")
            elif column:
                agg_clauses.append(f"{alias}={func}({column})")
        
        # Build group by clause
        group_by = group_by_columns.copy()
        if time_column and time_bin:
            group_by.insert(0, f"bin({time_column}, {time_bin})")
        
        summarize_clause = f"| summarize {', '.join(agg_clauses)} by {', '.join(group_by)}"
        query_parts.append(summarize_clause)
        
        query = '\n'.join(query_parts)
        return True, query, []
    
    def build_search_query(
        self,
        search_term: str,
        search_columns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        limit: int = 100
    ) -> Tuple[bool, str, List[str]]:
        """
        Build a search query
        
        Args:
            search_term: Term to search for
            search_columns: Columns to search in (None = all string columns)
            case_sensitive: Whether search is case-sensitive
            limit: Row limit
        
        Returns:
            (success, query, errors)
        """
        errors = []
        
        if not search_columns:
            search_columns = self.string_columns
            if not search_columns:
                return False, "", ["No string columns found in table"]
        
        # Validate columns
        for col in search_columns:
            valid, error = self.validate_column(col)
            if not valid:
                errors.append(error)
        
        if errors:
            return False, "", errors
        
        # Build search conditions
        operator = "contains_cs" if case_sensitive else "contains"
        conditions = [f"{col} {operator} '{search_term}'" for col in search_columns]
        where_clause = " or ".join(conditions)
        
        query = f"{self.table_path}\n| where {where_clause}\n| take {limit}"
        return True, query, []


class KQLQueryBuilderService:
    """
    Service for building and validating KQL queries with sampling
    """
    
    def __init__(self):
        self.samples: Dict[str, TableSample] = {}  # Cache of table samples
    
    def _make_sample_key(self, cluster: str, database: str, table: str) -> str:
        """Generate cache key for table sample"""
        return f"{cluster}.{database}.{table}"
    
    def store_sample(self, sample: TableSample):
        """Store a table sample"""
        key = self._make_sample_key(sample.cluster, sample.database, sample.table)
        self.samples[key] = sample
    
    def get_sample(self, cluster: str, database: str, table: str) -> Optional[TableSample]:
        """Get cached table sample"""
        key = self._make_sample_key(cluster, database, table)
        return self.samples.get(key)
    
    def create_query_builder(
        self,
        cluster: str,
        database: str,
        table: str,
        sample: Optional[TableSample] = None
    ) -> Optional[QueryBuilder]:
        """
        Create a query builder for a table
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            sample: Optional table sample (will use cached if not provided)
        
        Returns:
            QueryBuilder instance or None if sample not available
        """
        if not sample:
            sample = self.get_sample(cluster, database, table)
        
        if not sample:
            return None
        
        return QueryBuilder(sample)
    
    def validate_query_syntax(self, query: str) -> Tuple[bool, List[str]]:
        """
        Basic syntax validation for KQL queries
        
        Returns:
            (valid, errors)
        """
        errors = []
        
        # Check for common syntax errors
        if not query.strip():
            errors.append("Query is empty")
            return False, errors
        
        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for balanced quotes
        single_quotes = query.count("'")
        if single_quotes % 2 != 0:
            errors.append("Unbalanced single quotes")
        
        double_quotes = query.count('"')
        if double_quotes % 2 != 0:
            errors.append("Unbalanced double quotes")
        
        # Check for common KQL operators
        lines = query.split('\n')
        if len(lines) > 1:
            for line in lines[1:]:  # Skip first line (table name)
                stripped = line.strip()
                if stripped and not stripped.startswith('|'):
                    errors.append(f"Query operators must start with '|': {stripped[:50]}")
        
        return len(errors) == 0, errors
    
    def suggest_columns(
        self,
        cluster: str,
        database: str,
        table: str,
        purpose: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest columns based on purpose
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            purpose: Purpose (e.g., "time_filtering", "grouping", "aggregation")
        
        Returns:
            List of suggested columns with metadata
        """
        sample = self.get_sample(cluster, database, table)
        if not sample:
            return []
        
        suggestions = []
        
        if purpose == "time_filtering":
            for col_name in sample.get_time_columns():
                suggestions.append({
                    'name': col_name,
                    'type': sample.get_column_types()[col_name],
                    'reason': 'Datetime column suitable for time filtering'
                })
        
        elif purpose == "grouping":
            # Suggest string and low-cardinality columns
            for col_name in sample.get_string_columns():
                # Estimate cardinality from sample
                unique_vals = len(set(row.get(col_name) for row in sample.sample_rows if col_name in row))
                if unique_vals < sample.sample_size * 0.5:  # Less than 50% unique
                    suggestions.append({
                        'name': col_name,
                        'type': 'string',
                        'reason': f'Low cardinality ({unique_vals}/{sample.sample_size} unique in sample)',
                        'estimated_cardinality': unique_vals
                    })
        
        elif purpose == "aggregation":
            for col_name in sample.get_numeric_columns():
                suggestions.append({
                    'name': col_name,
                    'type': sample.get_column_types()[col_name],
                    'reason': 'Numeric column suitable for aggregation'
                })
        
        return suggestions
    
    def generate_example_queries(
        self,
        cluster: str,
        database: str,
        table: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate example queries based on table schema
        
        Returns:
            List of example queries with descriptions
        """
        sample = self.get_sample(cluster, database, table)
        if not sample:
            return []
        
        examples = []
        builder = QueryBuilder(sample)
        
        # Example 1: Basic select
        success, query, _ = builder.build_select_query(limit=10)
        if success:
            examples.append({
                'type': 'basic_select',
                'description': 'Get sample rows from table',
                'query': query
            })
        
        # Example 2: Time-filtered query (if time columns available)
        if sample.get_time_columns():
            time_col = sample.get_time_columns()[0]
            success, query, _ = builder.build_time_range_query(time_col, "1h", 100)
            if success:
                examples.append({
                    'type': 'time_filtered',
                    'description': f'Get recent data from last hour using {time_col}',
                    'query': query
                })
        
        # Example 3: Aggregation (if numeric columns available)
        if sample.get_numeric_columns() and sample.get_string_columns():
            num_col = sample.get_numeric_columns()[0]
            str_col = sample.get_string_columns()[0]
            success, query, _ = builder.build_aggregation_query(
                group_by_columns=[str_col],
                aggregations=[
                    {'func': 'count', 'column': '', 'alias': 'count'},
                    {'func': 'avg', 'column': num_col, 'alias': f'avg_{num_col}'}
                ]
            )
            if success:
                examples.append({
                    'type': 'aggregation',
                    'description': f'Aggregate {num_col} by {str_col}',
                    'query': query
                })
        
        # Example 4: Count query
        examples.append({
            'type': 'count',
            'description': 'Get total row count',
            'query': f"{sample.table_path}\n| count"
        })
        
        # Example 5: Schema discovery
        examples.append({
            'type': 'schema',
            'description': 'Discover table schema',
            'query': f"{sample.table_path}\n| getschema"
        })
        
        return examples[:count]


# Singleton instance
_kql_builder_service = KQLQueryBuilderService()


def get_kql_builder_service() -> KQLQueryBuilderService:
    """Get the singleton KQL query builder service instance"""
    return _kql_builder_service
