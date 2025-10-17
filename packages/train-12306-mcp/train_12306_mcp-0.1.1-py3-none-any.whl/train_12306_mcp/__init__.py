import argparse
from .server import mcp
def main():
    """12306 MCP server, implementing the ticket inquiry feature."""
    parser = argparse.ArgumentParser(
        description="12306 MCP server, implementing the ticket inquiry feature."
    )
    parser.add_argument('--port', help='sse端口')
    args=parser.parse_args()
    if not args.port:
        mcp.run()
    else:
        mcp.run(transport="sse",port=int(args.port))
if __name__ == "__main__":
    main()