import os
import arxiv
from typing import List, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
load_dotenv()
# Define a Pydantic model for the paper details.
# This helps with structured data extraction and validation.
class ArxivPaper(BaseModel):
    """Represents a paper from the arXiv repository."""
    title: str = Field(..., description="The title of the paper.")
    authors: List[str] = Field(..., description="A list of authors of the paper.")
    summary: str = Field(..., description="A summary of the paper.")
    pdf_url: str = Field(..., description="The URL to the paper on arXiv.")

class ResearchPlan(BaseModel):
    topic: str = Field(..., description="The main topic of the research.")
    keywords: List[str] = Field(..., description="Keywords to use for searching.")
    summary: str = Field(..., description="A brief summary of the research goal.")

# Create an agent instance.
# For this example, we'll use an OpenAI model.
# Make sure you have your OPENAI_API_KEY environment variable set.
# You can replace "openai:gpt-4o" with another model if you prefer.
agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    output_type=ResearchPlan,
    system_prompt="You're a helpful research assistant that finds scientific papers on arXiv based on user queries.",
)
@agent.tool_plain
def arxiv_retriever(query: str, max_results: int = 3) -> List[ArxivPaper]:
    """
    Searches the arXiv repository for scientific papers matching a query
    and returns a list of papers with their details.
    """
    try:
        # Create a search object with the query and max results.
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in search.results():
            # Extract author names from the list of author objects
            result.download_pdf("data/pdf/")
            author_names = [author.name for author in result.authors]
            
            # Create an ArxivPaper instance for each result
            papers.append(ArxivPaper(
                title=result.title,
                authors=author_names,
                summary=result.summary,
                pdf_url=result.pdf_url
            ))
        
        if not papers:
            print(f"No papers found for query: {query}")
            return []
            
        return papers

    except Exception as e:
        print(f"An error occurred while searching arXiv: {e}")
        return []


