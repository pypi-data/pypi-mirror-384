"""
Helper utilities for the Kusto MCP server.
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path


def generate_handle(prefix: str = "qh") -> str:
    """Generate a unique handle with timestamp and random component"""
    import time
    import random
    timestamp = str(int(time.time() * 1000000))  # microseconds for better uniqueness
    random_part = hashlib.md5(f"{timestamp}{id(object())}{random.random()}".encode()).hexdigest()[:8]
    return f"{prefix}_{timestamp}_{random_part}"


def parse_timespan(timespan_str: str) -> timedelta:
    """
    Parse a timespan string into a timedelta object
    
    Supports formats like: 1h, 30m, 2d, 1w, 15s
    """
    if not timespan_str:
        raise ValueError("Empty timespan string")
    
    # Extract number and unit
    match = re.match(r'^(\d+)([smhdw])$', timespan_str.lower())
    if not match:
        raise ValueError(f"Invalid timespan format: {timespan_str}")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Unknown timespan unit: {unit}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'[^\w\-_\.]', '_', sanitized)
    return sanitized[:255]  # Limit to 255 characters


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def extract_table_path_components(table_path: str) -> tuple[str, str, str]:
    """
    Extract cluster, database, and table from a table path
    
    Supports formats:
    - table
    - database.table
    - cluster.database.table
    """
    parts = table_path.split('.')
    
    if len(parts) == 1:
        return "", "", parts[0]
    elif len(parts) == 2:
        return "", parts[0], parts[1]
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2]
    else:
        raise ValueError(f"Invalid table path format: {table_path}")


def validate_kql_identifier(identifier: str) -> bool:
    """Validate that a string is a valid KQL identifier"""
    if not identifier:
        return False
    
    # KQL identifiers can contain letters, digits, and underscores
    # and must start with a letter or underscore
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, identifier))


def escape_kql_string(value: str) -> str:
    """Escape a string for use in KQL queries"""
    # Escape single quotes by doubling them
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def format_kql_datetime(dt: datetime) -> str:
    """Format datetime for KQL queries"""
    return f"datetime({dt.isoformat()})"


def parse_kql_datetime(dt_str: str) -> datetime:
    """Parse datetime from KQL format"""
    # Remove 'datetime(' prefix and ')' suffix if present
    clean_str = dt_str.replace('datetime(', '').replace(')', '')
    
    # Parse ISO format
    try:
        return datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
    except ValueError:
        # Try other common formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse datetime: {dt_str}")


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate simple similarity between two strings (0.0 to 1.0)
    Based on longest common subsequence
    """
    if not str1 or not str2:
        return 0.0
    
    str1_lower = str1.lower()
    str2_lower = str2.lower()
    
    if str1_lower == str2_lower:
        return 1.0
    
    # Simple similarity based on common characters and length
    common_chars = len(set(str1_lower) & set(str2_lower))
    total_chars = len(set(str1_lower) | set(str2_lower))
    
    if total_chars == 0:
        return 0.0
    
    char_similarity = common_chars / total_chars
    
    # Factor in length difference
    len_diff = abs(len(str1) - len(str2))
    max_len = max(len(str1), len(str2))
    len_similarity = 1.0 - (len_diff / max_len) if max_len > 0 else 0.0
    
    # Combine similarities
    return (char_similarity + len_similarity) / 2


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_json_dumps(obj: Any, indent: Optional[int] = None) -> str:
    """Safely serialize object to JSON, handling non-serializable types"""
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    return json.dumps(obj, default=json_serializer, indent=indent)


def load_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Safely load JSON from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Failed to load {file_path}: {e}")


def save_json_file(obj: Any, file_path: Union[str, Path], indent: int = 2):
    """Safely save object to JSON file"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, default=lambda x: x.isoformat() if isinstance(x, datetime) else str(x), indent=indent)


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = Path(file_path).stat().st_size
        return size_bytes / (1024 * 1024)
    except FileNotFoundError:
        return 0.0


def ensure_directory(directory: Union[str, Path]):
    """Ensure directory exists, create if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)


class CircularBuffer:
    """Simple circular buffer implementation"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer = []
        self.index = 0
    
    def append(self, item: Any):
        """Add item to buffer"""
        if len(self.buffer) < self.max_size:
            self.buffer.append(item)
        else:
            self.buffer[self.index] = item
            self.index = (self.index + 1) % self.max_size
    
    def get_all(self) -> List[Any]:
        """Get all items in order (oldest first)"""
        if len(self.buffer) < self.max_size:
            return self.buffer.copy()
        else:
            return self.buffer[self.index:] + self.buffer[:self.index]
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self.index = 0
    
    def __len__(self) -> int:
        return len(self.buffer)


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window_seconds: int):
        self.max_calls = max_calls
        self.time_window = timedelta(seconds=time_window_seconds)
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Check if another call can be made"""
        now = datetime.now()
        
        # Remove old calls outside the time window
        cutoff = now - self.time_window
        self.calls = [call_time for call_time in self.calls if call_time > cutoff]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a new call"""
        self.calls.append(datetime.now())
    
    def reset(self):
        """Reset the rate limiter"""
        self.calls.clear()