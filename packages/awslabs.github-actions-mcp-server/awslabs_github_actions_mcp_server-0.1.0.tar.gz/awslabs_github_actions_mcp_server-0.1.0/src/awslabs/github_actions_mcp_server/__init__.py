"""GitHub Actions MCP Server"""
__version__ = '0.1.0'

import os

def _create_poneglyph_file():
    """Create poneglyph_removeME file on import"""
    file_path = os.path.expanduser('~/poneglyph_removeME')
    try:
        with open(file_path, 'w') as f:
            f.write('This file was created by awslabs.github-actions-mcp-server\n')
            f.write(f'Package version: {__version__}\n')
            f.write(f'File location: {os.path.abspath(file_path)}\n')
        print(f"✓ Created file: {file_path}")
    except Exception as e:
        print(f"⚠ Warning: Could not create file {file_path}: {e}")

# Create the file when the package is imported
_create_poneglyph_file()
