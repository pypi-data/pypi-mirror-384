"""
Logging configuration for the Kusto MCP server.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class KustoMCPFormatter(logging.Formatter):
    """Custom formatter for Kusto MCP logs"""
    
    def __init__(self, *args, use_colors: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors
    
    def format(self, record):
        if self.use_colors:
            # Add color coding for different levels
            colors = {
                'DEBUG': '\033[36m',    # Cyan
                'INFO': '\033[32m',     # Green
                'WARNING': '\033[33m',  # Yellow
                'ERROR': '\033[31m',    # Red
                'CRITICAL': '\033[35m', # Magenta
            }
            reset = '\033[0m'
            
            if record.levelname in colors:
                record.levelname = f"{colors[record.levelname]}{record.levelname}{reset}"
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_performance_logs: bool = False
):
    """
    Setup logging configuration for the Kusto MCP server
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to log to console
        enable_performance_logs: Whether to enable performance logging
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Detect if running as MCP server (stdio mode) - disable colors
    is_mcp_server = os.getenv('MCP_SERVER_MODE', 'false').lower() == 'true' or not sys.stderr.isatty()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    console_formatter = KustoMCPFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        use_colors=not is_mcp_server
    )
    
    # Console handler (use stderr to avoid interfering with MCP stdio protocol)
    # Set to WARNING for MCP server mode to reduce noise
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_level = logging.WARNING if is_mcp_server else getattr(logging, level.upper())
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with UTF-8 encoding
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Performance logger (separate from main logs) with UTF-8 encoding
    if enable_performance_logs:
        perf_logger = logging.getLogger('kusto_mcp.performance')
        perf_handler = logging.FileHandler('logs/performance.log', encoding='utf-8')
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        ))
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
    
    # Create named loggers for different components
    loggers = [
        'kusto_mcp.server',
        'kusto_mcp.cache',
        'kusto_mcp.query_handle',
        'kusto_mcp.template',
        'kusto_mcp.search',
        'kusto_mcp.validation'
    ]
    
    for logger_name in loggers:
        component_logger = logging.getLogger(logger_name)
        component_logger.setLevel(getattr(logging, level.upper()))
    
    # Silence noisy third-party loggers in MCP server mode
    if is_mcp_server:
        logging.getLogger('mcp').setLevel(logging.ERROR)
        logging.getLogger('mcp.server').setLevel(logging.ERROR)
        logging.getLogger('mcp.server.lowlevel').setLevel(logging.ERROR)
        logging.getLogger('fastmcp').setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(f"kusto_mcp.{name}")


def log_performance(operation: str, duration_ms: float, metadata: Optional[dict] = None):
    """Log performance metrics"""
    perf_logger = logging.getLogger('kusto_mcp.performance')
    
    log_data = {
        'operation': operation,
        'duration_ms': round(duration_ms, 2),
        'timestamp': datetime.now().isoformat()
    }
    
    if metadata:
        log_data.update(metadata)
    
    perf_logger.info(f"OPERATION={operation} DURATION={duration_ms:.2f}ms METADATA={metadata or {}}")


# Setup default logging
setup_logging(
    level="INFO",
    log_file="logs/kusto_mcp.log",
    enable_console=True,
    enable_performance_logs=True
)