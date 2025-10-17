"""
Setup script for find-kusto-table-mcp

This file exists for backward compatibility with tools that don't support pyproject.toml.
The actual configuration is in pyproject.toml.
"""

from setuptools import setup

# Read version from src/__init__.py
def get_version():
    with open('src/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.0.0'

setup(
    version=get_version(),
    # All other configuration is in pyproject.toml
)
