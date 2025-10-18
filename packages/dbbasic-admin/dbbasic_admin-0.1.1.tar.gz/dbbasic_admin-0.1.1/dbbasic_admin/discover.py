"""
TSV table auto-discovery for admin interface
"""
import os
from pathlib import Path
from typing import List, Dict, Any


def get_data_dir() -> Path:
    """Get the data directory path"""
    # Look for data directory in current working directory
    cwd = Path.cwd()
    data_dir = cwd / "data"

    if not data_dir.exists():
        # Try _data as alternative
        data_dir = cwd / "_data"

    return data_dir


def discover_tsv_tables() -> List[Dict[str, Any]]:
    """
    Auto-discover TSV tables in the data directory.

    Returns:
        List of dicts with table metadata:
        [
            {
                'name': 'posts',
                'file': 'data/posts.tsv',
                'size': 12345,
                'rows': 42,
                'columns': ['id', 'title', 'content', 'author', 'created']
            },
            ...
        ]
    """
    data_dir = get_data_dir()

    if not data_dir.exists():
        return []

    tables = []

    # Find all .tsv files
    for tsv_file in data_dir.glob("*.tsv"):
        try:
            # Get file size
            file_size = tsv_file.stat().st_size

            # Read first line to get columns
            columns = []
            row_count = 0

            with open(tsv_file, 'r', encoding='utf-8') as f:
                # First line is column headers
                first_line = f.readline().strip()
                if first_line:
                    columns = first_line.split('\t')
                    row_count = 1  # header

                # Count remaining rows
                for line in f:
                    if line.strip():
                        row_count += 1

            tables.append({
                'name': tsv_file.stem,
                'file': str(tsv_file.relative_to(Path.cwd())),
                'size': file_size,
                'rows': max(0, row_count - 1),  # Exclude header from count
                'columns': columns
            })

        except Exception as e:
            # Skip files we can't read
            print(f"Warning: Could not read {tsv_file}: {e}")
            continue

    # Sort by name
    tables.sort(key=lambda x: x['name'])

    return tables


def read_tsv_data(table_name: str, limit: int = 100) -> List[Dict[str, str]]:
    """
    Read data from a TSV table.

    Args:
        table_name: Name of the table (without .tsv extension)
        limit: Maximum number of rows to return

    Returns:
        List of dicts, one per row
    """
    data_dir = get_data_dir()
    tsv_file = data_dir / f"{table_name}.tsv"

    if not tsv_file.exists():
        return []

    rows = []

    try:
        with open(tsv_file, 'r', encoding='utf-8') as f:
            # Read header
            header_line = f.readline().strip()
            if not header_line:
                return []

            columns = header_line.split('\t')

            # Read data rows
            for i, line in enumerate(f):
                if i >= limit:
                    break

                line = line.strip()
                if not line:
                    continue

                values = line.split('\t')

                # Pad values if needed
                while len(values) < len(columns):
                    values.append('')

                # Create dict
                row_dict = dict(zip(columns, values))
                rows.append(row_dict)

    except Exception as e:
        print(f"Error reading {tsv_file}: {e}")
        return []

    return rows


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
