# arxiv_mcp_server.py
import traceback
from typing import List
import arxiv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# This is the same Pydantic model we defined before.
# It will be used to structure the output of our tool.
class ArxivPaper(BaseModel):
    """Represents a paper from the arXiv repository."""
    title: str = Field(..., description="The title of the paper.")
    authors: List[str] = Field(..., description="A list of authors of the paper.")
    summary: str = Field(..., description="A summary of the paper.")
    pdf_url: str = Field(..., description="The URL to the paper's PDF on arXiv.")

# Create an instance of the FastMCP application.
app = FastMCP(name="ArXiv Search Server")

@app.tool()
def arxiv_retriever(query: str, max_results: int = 3) -> List[ArxivPaper]:
    """
    Searches the arXiv repository for scientific papers matching a query
    and returns a list of papers with their details.
    """
    print(f"MCP Server: Received search query '{query}' with max_results={max_results}")
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in search.results():
            author_names = [author.name for author in result.authors]
            papers.append(ArxivPaper(
                title=result.title,
                authors=author_names,
                summary=result.summary,
                pdf_url=result.pdf_url
            ))
        
        print(f"MCP Server: Found {len(papers)} papers. Returning to client.")
        return papers

    except Exception as e:
        # This is the crucial part. We catch ANY exception that might occur.
        print(f"MCP Server: An unexpected error occurred: {e}")
        print("--- Traceback ---")
        traceback.print_exc()
        print("-----------------")
        # Return an empty list to the client to indicate failure without crashing.
        return []
if __name__ == '__main__':
    print("Starting ArXiv MCP server on http://localhost:8000")
    # Use the 'streamable-http' transport as it's the recommended modern approach.
    app.run(transport='streamable-http')