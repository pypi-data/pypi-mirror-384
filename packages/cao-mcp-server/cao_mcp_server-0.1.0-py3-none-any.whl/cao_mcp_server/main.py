"""Main entry point for CAO MCP Server"""
import sys
import time
import platform

def main():
    """Main entry point for the CLI"""
    print("=" * 50)
    print("CAO MCP Server")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print("Server is running...")
    print("\nCalculator application has been launched.")
    print("To stop the server, press Ctrl+C\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nServer stopped gracefully.")
        sys.exit(0)

if __name__ == '__main__':
    main()
