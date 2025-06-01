import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Chinook SQLite MCP")

@mcp.resource("schema://main")
def get_schema() -> str:
    conn = sqlite3.connect("chinook.db")
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n".join(sql[0] for sql in schema if sql[0])

@mcp.tool()
def query_database(sql: str) -> str:
    conn = sqlite3.connect("chinook.db")
    try:
        result = conn.execute(sql).fetchall()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
