import argparse
from .server import mcp
def main():
    """12306 MCP server, implementing the ticket inquiry feature."""
    parser = argparse.ArgumentParser(
        description="12306 MCP server, implementing the ticket inquiry feature."
    )
    parser.parse_args()
    mcp.run()
if __name__ == "__main__":
    main()