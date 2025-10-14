"""ArXiv MCP Server for scientific paper search using FastMCP.

Run with:
    python arxiv_mcp_server.py
"""

import traceback
from typing import List
from pathlib import Path
import arxiv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


# Create an instance of the FastMCP application
app = FastMCP(name="ArXiv Search Server")

# Ensure data directory exists
PDF_DIR = Path("data/pdf")
PDF_DIR.mkdir(parents=True, exist_ok=True)

class ArxivPaper(BaseModel):
    """Represents a paper from the arXiv repository."""
    title: str = Field(..., description="The title of the paper.")
    authors: List[str] = Field(..., description="A list of authors of the paper.")
    summary: str = Field(..., description="A summary of the paper.")
    pdf_url: str = Field(..., description="The URL to the paper's PDF on arXiv.")


@app.tool()
def arxiv_retriever(query: str, max_results: int = 3) -> List[ArxivPaper]:
    """Searches the arXiv repository for scientific papers matching a query.
    
    Args:
        query: The search query for papers
        max_results: Maximum number of papers to return (default: 3)
    
    Returns:
        A list of ArxivPaper objects with paper details
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
            try:
                # Create safe filename
                safe_title = "".join(
                    c for c in result.title if c.isalnum() or c in (' ', '-', '_')
                ).rstrip()
                safe_title = safe_title[:100]  # Limit filename length
                
                # Download PDF
                pdf_path = PDF_DIR / f"{safe_title}.pdf"
                print(f"MCP Server: Downloading PDF to {pdf_path}")
                result.download_pdf(filename=str(pdf_path))
                
                # Extract author names
                author_names = [author.name for author in result.authors]
                
                papers.append(ArxivPaper(
                    title=result.title,
                    authors=author_names,
                    summary=result.summary,
                    pdf_url=result.pdf_url
                ))
            except Exception as e:
                print(f"MCP Server: Error processing paper '{result.title}': {e}")
                continue
        
        print(f"MCP Server: Found {len(papers)} papers. Returning to client.")
        return papers

    except Exception as e:
        print(f"MCP Server: An unexpected error occurred: {e}")
        print("--- Traceback ---")
        traceback.print_exc()
        print("-----------------")
        return []


if __name__ == '__main__':
    print("Starting ArXiv MCP server on http://localhost:8000")
    print(f"PDFs will be saved to: {PDF_DIR.absolute()}")
    # Use streamable-http as it's the recommended modern transport
    app.run(transport='streamable-http')