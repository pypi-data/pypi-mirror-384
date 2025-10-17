"""
Prompt loader utility for loading prompt templates from markdown files.

This module provides functionality to load prompt templates from the prompts/
directory instead of hardcoding them in the server code.
"""

import os
from pathlib import Path
from typing import Dict


# Cache for loaded prompts to avoid repeated file I/O
_prompt_cache: Dict[str, str] = {}


def get_prompts_dir() -> Path:
    """Get the path to the prompts directory."""
    # Assuming kusto_server.py is at project root
    project_root = Path(__file__).parent.parent.parent
    prompts_dir = project_root / "prompts"
    
    if not prompts_dir.exists():
        raise FileNotFoundError(
            f"Prompts directory not found at {prompts_dir}. "
            "Please ensure prompts/ directory exists at project root."
        )
    
    return prompts_dir


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from a markdown file.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Check cache first
    if prompt_name in _prompt_cache:
        return _prompt_cache[prompt_name]
    
    prompts_dir = get_prompts_dir()
    prompt_file = prompts_dir / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}. "
            f"Available prompts: {list_available_prompts()}"
        )
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cache the content
    _prompt_cache[prompt_name] = content
    
    return content


def list_available_prompts() -> list[str]:
    """
    List all available prompt templates.
    
    Returns:
        List of prompt names (without .md extension)
    """
    try:
        prompts_dir = get_prompts_dir()
        return [
            f.stem for f in prompts_dir.glob("*.md")
            if f.is_file()
        ]
    except FileNotFoundError:
        return []


def clear_prompt_cache():
    """Clear the prompt cache. Useful for testing or reloading prompts."""
    _prompt_cache.clear()


def format_prompt(prompt_name: str, **kwargs) -> str:
    """
    Load a prompt and format it with the provided keyword arguments.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        **kwargs: Values to substitute in the prompt template
        
    Returns:
        Formatted prompt string
        
    Example:
        >>> prompt = format_prompt("find_and_query_table", query_description="Find errors")
    """
    template = load_prompt(prompt_name)
    return template.format(**kwargs)
