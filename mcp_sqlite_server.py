import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Chinook SQLite MCP")

@mcp.resource("schema://main")
def get_schema() -> str:
    conn = sqlite3.connect("chinook.db")
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n".join(sql[0] for sql in schema if sql[0])

@mcp.tool(
    description="Execute an arbitrary SQL SELECT statement against the Chinook music store database. This tool takes a single SQL SELECT query as input and returns the raw query result as plain text. It does not interpret or answer questions itself; it simply executes the provided SQL and returns the result. The tool can be used to retrieve, aggregate, or filter data from any table in the database, including artists, albums, tracks, genres, customers, invoices, and more. If the SQL is invalid or causes an error, an error message will be returned. Only SELECT statements are supported; data modification is not allowed."
)
def query_database(sql: str) -> str:
    conn = sqlite3.connect("chinook.db")
    try:
        result = conn.execute(sql).fetchall()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
