"""
Utilities Module: Shared helper functions for file handling and formatting.

Functionality:
---------------
- `slugify()`: Converts titles into safe, lowercase, underscore-separated strings.
- `format_filename()`: Creates standardized filenames like `121_best_time_to_buy_and_sell_stock.cpp`.
- `ensure_dir()`: Creates parent directories if they don't exist.
- `save_solution()`: Writes code content to the specified path safely.

These helpers are used across the sync pipeline for filename generation and file system operations.

Dependencies:
-------------
- python-slugify
- os
"""

import os
from slugify import slugify as slugify_lib

def slugify(text):
    """
    Converts a title like 'Best Time to Buy and Sell Stock' to
    'best_time_to_buy_and_sell_stock'
    """
    return slugify_lib(text.replace('-', ' ')).lower().replace('-', '_')


def format_filename(problem_id, title, lang):
    """
    Returns formatted filename: <id>_<slugified_title>.<ext>
    """
    ext_map = {
        'cpp': 'cpp',
        'python': 'py',
        'java': 'java',
        'c': 'c',
        'go': 'go',
        'rust': 'rs'
    }
    ext = ext_map.get(lang.lower(), lang.lower())
    title_slug = slugify(title)
    return f"{problem_id}_{title_slug}.{ext}"


def ensure_dir(path):
    """Creates parent folders if they don’t exist."""
    os.makedirs(path, exist_ok=True)


def save_solution(path, code):
    """Writes solution code to file at the given path."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
