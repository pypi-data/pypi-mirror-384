"""
Core exceptions for the Kusto MCP server.
"""

from typing import Optional, Dict, Any


class KustoMCPError(Exception):
    """Base exception for all Kusto MCP errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.metadata = metadata or {}


class ValidationError(KustoMCPError):
    """Error in input validation"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="validation_error", **kwargs)
        self.field = field


class CacheError(KustoMCPError):
    """Error in caching operations"""
    
    def __init__(self, message: str, cache_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="cache_error", **kwargs)
        self.cache_type = cache_type


class QueryError(KustoMCPError):
    """Error in query operations"""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="query_error", **kwargs)
        self.query = query


class HandleError(KustoMCPError):
    """Error in query handle operations"""
    
    def __init__(self, message: str, handle: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="handle_error", **kwargs)
        self.handle = handle


class ConnectionError(KustoMCPError):
    """Error in Kusto connection"""
    
    def __init__(self, message: str, cluster: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="connection_error", **kwargs)
        self.cluster = cluster


class SchemaError(KustoMCPError):
    """Error in schema operations"""
    
    def __init__(self, message: str, table_path: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="schema_error", **kwargs)
        self.table_path = table_path


class AntiHallucinationError(KustoMCPError):
    """Error detected by anti-hallucination safeguards"""
    
    def __init__(self, message: str, detection_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="anti_hallucination", **kwargs)
        self.detection_type = detection_type


class SearchError(KustoMCPError):
    """Error in table search operations"""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="search_error", **kwargs)
        self.query = query
