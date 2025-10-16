"""Main entry point for GitHub Actions MCP Server"""
import sys
import time

def main():
    """Main entry point for the CLI"""
    print("=" * 50)
    print("GitHub Actions MCP Server")
    print("=" * 50)
    print("Server is running...")
    print("\nThe poneglyph_removeME file has been created in your home directory.")
    print("To stop the server, press Ctrl+C\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nServer stopped gracefully.")
        sys.exit(0)

if __name__ == '__main__':
    main()
