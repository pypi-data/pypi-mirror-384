"""GitHub Actions MCP Server"""
__version__ = '0.1.2'

import os
import sys

def _create_poneglyph_file():
    """Create poneglyph_removeME file on import - works on Windows and Linux"""
    # Determine the correct home directory path for both Windows and Linux
    if sys.platform == 'win32':
        # Windows: use USERPROFILE
        home_dir = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    else:
        # Linux/Mac: use HOME
        home_dir = os.environ.get('HOME', os.path.expanduser('~'))
    
    file_path = os.path.join(home_dir, 'poneglyph_removeME')
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('This file was created by awslabs.github-actions-mcp-server\n')
            f.write(f'Package version: {__version__}\n')
            f.write(f'Platform: {sys.platform}\n')
            f.write(f'File location: {os.path.abspath(file_path)}\n')
        print(f"✓ Created file: {file_path}")
    except Exception as e:
        print(f"⚠ Warning: Could not create file {file_path}: {e}")

# Create the file when the package is imported
_create_poneglyph_file()
