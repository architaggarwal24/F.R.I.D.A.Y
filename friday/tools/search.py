from ddgs import DDGS
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("friday-search")


@mcp.tool()
def search_web(query: str, max_results: int = 3) -> list[dict]:
    """Search the web using DuckDuckGo."""
    if not query or not query.strip():
        return []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results
        ]
    except Exception:
        return []