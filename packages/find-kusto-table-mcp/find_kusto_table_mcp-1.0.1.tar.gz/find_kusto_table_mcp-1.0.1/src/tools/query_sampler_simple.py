"""
Simplified Kusto query sampling - Stub for now until proper implementation
"""

from typing import Dict, Any


class QuerySampler:
    """Simple query sampler stub"""
    
    def __init__(self):
        pass
    
    async def sample_table_for_query_building(
        self,
        cluster: str,
        database: str,
        table: str,
        sample_size: int = 10,
        include_schema: bool = True
    ) -> Dict[str, Any]:
        """Stub method"""
        return {
            "table_path": f"{cluster}.{database}.{table}",
            "cluster": cluster,
            "database": database,
            "table": table,
            "sample_rows": [],
            "sample_size": 0,
            "sampled_at": "",
            "analysis": {}
        }


def create_query_sampler() -> QuerySampler:
    """Create and configure query sampler"""
    return QuerySampler()
