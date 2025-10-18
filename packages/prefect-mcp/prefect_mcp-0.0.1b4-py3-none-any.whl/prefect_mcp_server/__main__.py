"""Entry point for running the Prefect MCP server."""

from prefect_mcp_server.server import mcp


def main():
    mcp.run()


if __name__ == "__main__":
    main()
