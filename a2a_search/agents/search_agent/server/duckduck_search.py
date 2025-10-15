import os
import sys
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()
def log(message):
    print(f"[DEBUG] {message}", file=sys.stderr, flush=True)

mcp = FastMCP("duckduckgo")
# DEFAULT_WORKSPACE = os.path.expanduser("~/a2a_search/workspace")

@mcp.tool()
async def duckduckgo_search(query: str) -> str:
    "Search the web using DuckDuckGo and return the results."
    log(f"test_tool called with: {query}")

    try:
        search = DuckDuckGoSearchRun()
        result = await search.ainvoke(query)
        return result
    
    except Exception as e:
        return f"An error occurred during the search: {str(e)}"

if __name__ == "__main__":
    log("Starting minimal MCP server...")
    log("Server should be ready for stdio communication")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        log(f"Server error: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)