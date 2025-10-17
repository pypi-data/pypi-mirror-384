"""
Query Optimization Analyzer

Analyzes KQL queries for performance issues, suggests optimizations,
estimates costs, and provides best practice recommendations.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..core.exceptions import ValidationError

logger = get_logger("query_optimizer")


class QueryOptimizationAnalyzer:
    """
    Analyzes KQL queries and suggests performance optimizations
    
    Features:
    - Query complexity analysis
    - Performance anti-patterns detection
    - Index suggestions
    - Cost estimation
    - Best practice recommendations
    - Query rewriting suggestions
    """
    
    def __init__(self):
        self.logger = logger
        
        # Performance anti-patterns
        self.anti_patterns = {
            "no_time_filter": {
                "severity": "high",
                "message": "Query lacks time filter - will scan entire table",
                "recommendation": "Add time filter using 'where Timestamp > ago(1h)'"
            },
            "no_limit": {
                "severity": "medium",
                "message": "Query lacks result limit - may return huge dataset",
                "recommendation": "Add 'take N' or 'limit N' to restrict results"
            },
            "select_star": {
                "severity": "low",
                "message": "Using SELECT * loads unnecessary columns",
                "recommendation": "Specify only needed columns with 'project column1, column2'"
            },
            "no_where_before_extend": {
                "severity": "medium",
                "message": "Filters after extend/project - inefficient order",
                "recommendation": "Move 'where' clauses before 'extend' and 'project'"
            },
            "string_contains_no_index": {
                "severity": "medium",
                "message": "Using 'contains' on large text columns - slow",
                "recommendation": "Consider using 'has' for whole words or add index"
            },
            "multiple_joins": {
                "severity": "high",
                "message": "Multiple joins detected - may be slow",
                "recommendation": "Minimize joins, pre-aggregate data, or use materialized views"
            },
            "no_aggregation_limit": {
                "severity": "medium",
                "message": "Summarize without limit - may create huge result set",
                "recommendation": "Add 'top N by column' after summarize"
            },
            "inefficient_distinct": {
                "severity": "low",
                "message": "Using distinct on many columns - consider alternatives",
                "recommendation": "Use 'summarize by columns' or reduce column count"
            },
            "nested_queries": {
                "severity": "high",
                "message": "Nested subqueries detected - impacts performance",
                "recommendation": "Flatten queries or use 'let' statements"
            },
            "regex_on_large_column": {
                "severity": "high",
                "message": "Regular expressions on large text - very slow",
                "recommendation": "Use simpler string operations or add computed columns"
            }
        }
        
        # Best practices checklist
        self.best_practices = [
            "Time filters on time-series data",
            "Result limits on queries",
            "Specific column selection",
            "Filters before transformations",
            "Appropriate use of indexes",
            "Minimal joins",
            "Efficient aggregations",
            "Proper data types"
        ]
    
    @measure_operation("analyze_query_optimization")
    def analyze_query(
        self,
        query: str,
        table_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive query optimization analysis
        
        Args:
            query: KQL query to analyze
            table_metadata: Optional metadata about the table being queried
        
        Returns:
            Analysis with issues, recommendations, complexity score, and optimized query
        """
        analysis = {
            "query": query,
            "analyzed_at": datetime.now().isoformat(),
            "complexity_score": 0,
            "performance_issues": [],
            "recommendations": [],
            "best_practices_score": 0,
            "estimated_cost": "unknown",
            "optimized_query": None
        }
        
        # Parse query structure
        structure = self._parse_query_structure(query)
        analysis["structure"] = structure
        
        # Calculate complexity
        complexity = self._calculate_complexity(structure)
        analysis["complexity_score"] = complexity["score"]
        analysis["complexity_factors"] = complexity["factors"]
        
        # Detect anti-patterns
        issues = self._detect_anti_patterns(query, structure, table_metadata)
        analysis["performance_issues"] = issues
        
        # Generate recommendations
        recommendations = self._generate_recommendations(query, structure, issues, table_metadata)
        analysis["recommendations"] = recommendations
        
        # Check best practices
        best_practices = self._check_best_practices(query, structure)
        analysis["best_practices_score"] = best_practices["score"]
        analysis["best_practices_met"] = best_practices["met"]
        analysis["best_practices_failed"] = best_practices["failed"]
        
        # Estimate cost
        cost = self._estimate_cost(structure, table_metadata)
        analysis["estimated_cost"] = cost
        
        # Generate optimized query
        if issues:
            optimized = self._optimize_query(query, structure, issues)
            analysis["optimized_query"] = optimized
            analysis["optimization_applied"] = True
        else:
            analysis["optimization_applied"] = False
            analysis["message"] = "Query already follows best practices"
        
        return analysis
    
    def _parse_query_structure(self, query: str) -> Dict[str, Any]:
        """Parse query to understand its structure"""
        query_lower = query.lower()
        
        structure = {
            "has_time_filter": False,
            "has_limit": False,
            "has_project": False,
            "has_where": False,
            "has_summarize": False,
            "has_join": False,
            "has_extend": False,
            "has_distinct": False,
            "has_regex": False,
            "operator_count": 0,
            "operators": [],
            "table_name": None
        }
        
        # Extract table name
        table_match = re.match(r'^\s*(\w+)', query)
        if table_match:
            structure["table_name"] = table_match.group(1)
        
        # Check for operators
        operators = ['where', 'project', 'extend', 'summarize', 'join', 'union', 
                    'take', 'limit', 'top', 'distinct', 'sort', 'order']
        
        for op in operators:
            if re.search(rf'\|\s*{op}\b', query_lower):
                structure["operators"].append(op)
                structure["operator_count"] += 1
                
                if op in ['where']:
                    structure["has_where"] = True
                    # Check for time filter
                    if 'ago(' in query_lower or 'between(' in query_lower:
                        structure["has_time_filter"] = True
                elif op in ['take', 'limit', 'top']:
                    structure["has_limit"] = True
                elif op == 'project':
                    structure["has_project"] = True
                elif op == 'summarize':
                    structure["has_summarize"] = True
                elif op == 'join':
                    structure["has_join"] = True
                    # Count joins
                    structure["join_count"] = query_lower.count('| join')
                elif op == 'extend':
                    structure["has_extend"] = True
                elif op == 'distinct':
                    structure["has_distinct"] = True
        
        # Check for regex usage
        if re.search(r'matches\s+regex|extract\(|parse\s+', query_lower):
            structure["has_regex"] = True
        
        # Check for string operations
        structure["has_contains"] = 'contains' in query_lower
        structure["has_has"] = ' has ' in query_lower
        
        # Operator order
        structure["operator_order"] = self._extract_operator_order(query)
        
        return structure
    
    def _extract_operator_order(self, query: str) -> List[str]:
        """Extract the order of operators in the query"""
        operators = []
        for match in re.finditer(r'\|\s*(\w+)', query.lower()):
            operators.append(match.group(1))
        return operators
    
    def _calculate_complexity(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate query complexity score"""
        score = 0
        factors = []
        
        # Base complexity from operator count
        score += structure["operator_count"] * 10
        factors.append(f"Base operators: {structure['operator_count']} (+{structure['operator_count'] * 10})")
        
        # Joins add significant complexity
        if structure["has_join"]:
            join_count = structure.get("join_count", 1)
            score += join_count * 30
            factors.append(f"Joins: {join_count} (+{join_count * 30})")
        
        # Regex is expensive
        if structure["has_regex"]:
            score += 25
            factors.append("Regex operations (+25)")
        
        # No time filter on time-series data
        if not structure["has_time_filter"] and structure["operator_count"] > 0:
            score += 40
            factors.append("No time filter (+40)")
        
        # No limit is problematic
        if not structure["has_limit"]:
            score += 20
            factors.append("No result limit (+20)")
        
        # Distinct can be expensive
        if structure["has_distinct"]:
            score += 15
            factors.append("Distinct operation (+15)")
        
        # Complexity rating
        if score <= 30:
            rating = "low"
        elif score <= 60:
            rating = "medium"
        elif score <= 100:
            rating = "high"
        else:
            rating = "very high"
        
        return {
            "score": score,
            "rating": rating,
            "factors": factors
        }
    
    def _detect_anti_patterns(
        self,
        query: str,
        structure: Dict[str, Any],
        table_metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect performance anti-patterns"""
        issues = []
        
        # No time filter
        if not structure["has_time_filter"] and structure["operator_count"] > 0:
            issue = self.anti_patterns["no_time_filter"].copy()
            issues.append(issue)
        
        # No limit
        if not structure["has_limit"]:
            issue = self.anti_patterns["no_limit"].copy()
            issues.append(issue)
        
        # Check for SELECT *
        if not structure["has_project"] and structure["operator_count"] > 1:
            issue = self.anti_patterns["select_star"].copy()
            issues.append(issue)
        
        # Check operator order
        order = structure["operator_order"]
        if 'extend' in order and 'where' in order:
            extend_idx = order.index('extend')
            where_indices = [i for i, x in enumerate(order) if x == 'where']
            if where_indices and any(i > extend_idx for i in where_indices):
                issue = self.anti_patterns["no_where_before_extend"].copy()
                issues.append(issue)
        
        # String operations
        if structure["has_contains"] and not structure["has_has"]:
            issue = self.anti_patterns["string_contains_no_index"].copy()
            issues.append(issue)
        
        # Multiple joins
        if structure.get("join_count", 0) > 1:
            issue = self.anti_patterns["multiple_joins"].copy()
            issues.append(issue)
        
        # Summarize without limit
        if structure["has_summarize"] and not structure["has_limit"]:
            issue = self.anti_patterns["no_aggregation_limit"].copy()
            issues.append(issue)
        
        # Regex usage
        if structure["has_regex"]:
            issue = self.anti_patterns["regex_on_large_column"].copy()
            issues.append(issue)
        
        return issues
    
    def _generate_recommendations(
        self,
        query: str,
        structure: Dict[str, Any],
        issues: List[Dict[str, Any]],
        table_metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Add recommendations from issues
        for issue in issues:
            recommendations.append({
                "category": "performance",
                "priority": issue["severity"],
                "recommendation": issue["recommendation"]
            })
        
        # Additional recommendations based on table metadata
        if table_metadata:
            # Suggest indexes
            if not structure["has_time_filter"] and table_metadata.get("time_columns"):
                recommendations.append({
                    "category": "indexing",
                    "priority": "high",
                    "recommendation": f"Add index on time column: {table_metadata['time_columns'][0]}"
                })
            
            # Suggest column selection
            if not structure["has_project"] and len(table_metadata.get("columns", [])) > 10:
                recommendations.append({
                    "category": "column_selection",
                    "priority": "medium",
                    "recommendation": "Select only needed columns to reduce data transfer"
                })
        
        # Query structure recommendations
        if structure["operator_count"] > 5:
            recommendations.append({
                "category": "complexity",
                "priority": "low",
                "recommendation": "Consider breaking complex query into simpler steps using 'let' statements"
            })
        
        return recommendations
    
    def _check_best_practices(
        self,
        query: str,
        structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check query against best practices"""
        met = []
        failed = []
        
        # Time filter
        if structure["has_time_filter"]:
            met.append("Has time filter")
        else:
            failed.append("Missing time filter")
        
        # Result limit
        if structure["has_limit"]:
            met.append("Has result limit")
        else:
            failed.append("Missing result limit")
        
        # Column selection
        if structure["has_project"]:
            met.append("Specific column selection")
        else:
            failed.append("No column selection (using all columns)")
        
        # Filters before transformations
        order = structure["operator_order"]
        if 'where' in order and 'extend' in order:
            where_first = order.index('where') < order.index('extend')
            if where_first:
                met.append("Filters before transformations")
            else:
                failed.append("Filters after transformations")
        
        # Calculate score
        total = len(met) + len(failed)
        score = (len(met) / total * 100) if total > 0 else 0
        
        return {
            "score": score,
            "met": met,
            "failed": failed
        }
    
    def _estimate_cost(
        self,
        structure: Dict[str, Any],
        table_metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Estimate query execution cost"""
        # Simple heuristic-based cost estimation
        cost_score = 0
        
        # No time filter = scan entire table
        if not structure["has_time_filter"]:
            cost_score += 50
        
        # No limit = return all results
        if not structure["has_limit"]:
            cost_score += 30
        
        # Joins are expensive
        if structure["has_join"]:
            cost_score += structure.get("join_count", 1) * 25
        
        # Regex is very expensive
        if structure["has_regex"]:
            cost_score += 40
        
        # Estimate based on score
        if cost_score <= 30:
            return "low"
        elif cost_score <= 60:
            return "medium"
        elif cost_score <= 100:
            return "high"
        else:
            return "very high"
    
    def _optimize_query(
        self,
        query: str,
        structure: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> str:
        """Generate an optimized version of the query"""
        optimized = query
        
        # Add time filter if missing
        if not structure["has_time_filter"]:
            # Insert after table name
            table_name = structure.get("table_name")
            if table_name:
                optimized = re.sub(
                    rf'^(\s*{table_name}\s*)',
                    r'\1\n| where Timestamp > ago(24h)  // Added time filter',
                    optimized,
                    flags=re.MULTILINE
                )
        
        # Add limit if missing
        if not structure["has_limit"]:
            if not optimized.strip().endswith(';'):
                optimized += "\n| take 1000  // Added result limit"
        
        # Add project if missing (suggest common columns)
        if not structure["has_project"] and structure["operator_count"] > 0:
            table_name = structure.get("table_name")
            if table_name:
                # Insert after time filter if it exists, otherwise after table
                if '| where' in optimized:
                    optimized = re.sub(
                        r'(\|\s*where[^\n]+)',
                        r'\1\n| project Timestamp, *  // TODO: Select only needed columns',
                        optimized,
                        count=1
                    )
        
        return optimized
    
    @measure_operation("suggest_indexes")
    def suggest_indexes(
        self,
        query: str,
        table_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest indexes based on query patterns"""
        suggestions = []
        
        # Extract WHERE clauses
        where_clauses = re.findall(r'where\s+(\w+)', query, re.IGNORECASE)
        
        for column in where_clauses:
            # Check if column exists in metadata
            all_columns = [c["name"] for c in table_metadata.get("columns", [])]
            if column in all_columns:
                suggestions.append({
                    "column": column,
                    "index_type": "range",
                    "reason": f"Column '{column}' used in WHERE clause",
                    "priority": "high" if query.lower().count(f"where {column.lower()}") > 1 else "medium"
                })
        
        # Suggest time column index
        time_columns = table_metadata.get("time_columns", [])
        if time_columns and 'ago(' in query.lower():
            suggestions.append({
                "column": time_columns[0],
                "index_type": "datetime",
                "reason": "Primary time column used in time-based filter",
                "priority": "high"
            })
        
        return suggestions
    
    @measure_operation("compare_queries")
    def compare_queries(
        self,
        query1: str,
        query2: str
    ) -> Dict[str, Any]:
        """Compare two queries for performance characteristics"""
        analysis1 = self.analyze_query(query1)
        analysis2 = self.analyze_query(query2)
        
        comparison = {
            "query1": {
                "complexity_score": analysis1["complexity_score"],
                "estimated_cost": analysis1["estimated_cost"],
                "issues_count": len(analysis1["performance_issues"]),
                "best_practices_score": analysis1["best_practices_score"]
            },
            "query2": {
                "complexity_score": analysis2["complexity_score"],
                "estimated_cost": analysis2["estimated_cost"],
                "issues_count": len(analysis2["performance_issues"]),
                "best_practices_score": analysis2["best_practices_score"]
            },
            "recommendation": None
        }
        
        # Determine which is better
        score1 = analysis1["best_practices_score"] - analysis1["complexity_score"]
        score2 = analysis2["best_practices_score"] - analysis2["complexity_score"]
        
        if score1 > score2:
            comparison["recommendation"] = "Query 1 is more optimized"
        elif score2 > score1:
            comparison["recommendation"] = "Query 2 is more optimized"
        else:
            comparison["recommendation"] = "Queries are similarly optimized"
        
        return comparison


def create_query_optimizer() -> QueryOptimizationAnalyzer:
    """Create query optimization analyzer instance"""
    return QueryOptimizationAnalyzer()
