import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Chinook SQLite MCP")

@mcp.resource("schema://main")
def get_schema() -> str:
    conn = sqlite3.connect("chinook.db")
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n".join(sql[0] for sql in schema if sql[0])

@mcp.tool(
    description="Run an arbitrary SQL query against the Chinook music store database. This tool allows you to answer questions about artists, albums, tracks, genres, customers, invoices, and more by providing a valid SQL SELECT statement as input.\n\nExample questions you can answer with this tool include:\n- How many tracks are there?\n- What is the average track length?\n- List all albums by AC/DC.\n- Show the top 5 most expensive tracks.\n- Which artist has the most albums?\n\nThe input should be a single SQL SELECT statement. The output will be the query result as plain text. If there is an error in the SQL, an error message will be returned."
)
def query_database(sql: str) -> str:
    """
    Examples:
    User: How many tracks are there?
    Assistant: {"tool": "query_database", "input": "SELECT COUNT(*) FROM Track;"}
    User: What is the average track length?
    Assistant: {"tool": "query_database", "input": "SELECT AVG(Milliseconds) FROM Track;"}
    User: List all albums by AC/DC.
    Assistant: {"tool": "query_database", "input": "SELECT Title FROM Album JOIN Artist ON Album.ArtistId = Artist.ArtistId WHERE Artist.Name = 'AC/DC';"}
    User: Show the top 5 most expensive tracks.
    Assistant: {"tool": "query_database", "input": "SELECT Name, UnitPrice FROM Track ORDER BY UnitPrice DESC LIMIT 5;"}
    User: Which artist has the most albums?
    Assistant: {"tool": "query_database", "input": "SELECT Artist.Name, COUNT(Album.AlbumId) as AlbumCount FROM Artist JOIN Album ON Artist.ArtistId = Album.ArtistId GROUP BY Artist.ArtistId ORDER BY AlbumCount DESC LIMIT 1;"}
    """
    conn = sqlite3.connect("chinook.db")
    try:
        result = conn.execute(sql).fetchall()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
