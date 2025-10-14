"""Scientific paper parser agent with A2A protocol and MCP integration.

This agent searches for scientific papers using an MCP server, extracts key information,
and saves them to a configured directory.

Run the MCP server first:
    python arxiv_mcp_server.py

Then run this agent:
    python paper_parser_a2a.py
"""

import os
import json
from pathlib import Path
from typing import List
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configuration
OUTPUT_DIR = Path(os.environ.get('PAPER_OUTPUT_DIR', './parsed_papers'))

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_mcp_servers(config_path=None):
    """Load MCP servers from configuration file.
    
    Args:
        config_path: Path to the MCP configuration file. If None, will check
                    MCP_CONFIG environment variable or use default "mcp_config.json"
        
    Returns:
        List of MCPServerStreamableHTTP instances
    """
    if config_path is None:
        config_path = os.environ.get('MCP_CONFIG', 'mcp_config.json')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If config_path is not absolute, make it relative to script directory
    if not os.path.isabs(config_path):
        config_path = os.path.join(script_dir, config_path)
    
    if not os.path.exists(config_path):
        print(f"Warning: MCP config file not found at {config_path}")
        # Fallback to default configuration
        return [MCPServerStreamableHTTP("http://localhost:8000/mcp")]
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        servers = []
        for server_name, server_cfg in config.get("mcpServers", {}).items():
            if "url" in server_cfg:
                url = server_cfg["url"]
            else:
                # Fallback URL construction
                url = "http://localhost:8000/mcp"
            
            print(f"Loading MCP server: {server_name} at {url}")
            servers.append(MCPServerStreamableHTTP(url))
        
        if not servers:
            print("No MCP servers found in config, using default")
            return [MCPServerStreamableHTTP("http://localhost:8000/mcp")]
            
        return servers
    except Exception as e:
        print(f"Error loading MCP config: {e}")
        # Fallback to default configuration
        return [MCPServerStreamableHTTP("http://localhost:8000/mcp")]


class PaperInfo(BaseModel):
    """Structured information extracted from a scientific paper."""
    
    title: str = Field(description="The title of the paper")
    authors: List[str] = Field(description="List of paper authors")
    summary: str = Field(description="Paper summary/abstract")
    topics: List[str] = Field(
        description="Key topics and keywords extracted from the paper (in CAPITAL LETTERS)"
    )
    overview: str = Field(
        description="A concise overview of the paper's main contributions and findings"
    )
    pdf_url: str = Field(description="URL to the paper's PDF")
    useful: bool = Field(
        default=True,
        description="Whether this paper is useful for the query"
    )
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the paper was retrieved"
    )


class PaperSearchResult(BaseModel):
    """Results from the paper search."""
    
    papers: List[PaperInfo] = Field(
        description="List of papers found for the query"
    )
    query: str = Field(description="The search query used")
    total_found: int = Field(description="Total number of papers found")


# Initialize the MCP servers from config
mcp_servers = load_mcp_servers()


# Convert agent to A2A app
def create_paper_parser_app():
    """Create the paper parser A2A app with current MCP configuration."""
    # Check for Gemini API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini API")
    
    mcp_servers = load_mcp_servers()
    
    agent = Agent(
        'google-gla:gemini-2.5-flash-lite',
        output_type=PaperSearchResult,
        toolsets=mcp_servers,
        system_prompt="""You are a scientific paper analysis assistant. Your job is to:
        1. ALWAYS use the arxiv_retriever tool to search for scientific papers
        2. Extract key information including topics, keywords, and overviews
        3. Evaluate the usefulness of each paper for the given query
        4. Provide structured output that can be saved for later reference
        
        IMPORTANT: You MUST use the arxiv_retriever tool to search for papers. Never return empty results without using this tool.
        
        For topics, always use CAPITAL LETTERS for keywords.
        Be thorough and accurate in your extraction of information.
        Mark papers as useful=True if they are relevant to the query, False otherwise.
        """,
    )
    
    
    # Add the save_paper_results tool to the agent
    @agent.tool
    async def save_paper_results(
        ctx: RunContext,
        result: PaperSearchResult,
        filename: str | None = None
    ) -> str:
        """Save the paper search results to disk in the configured output directory.
        
        Args:
            ctx: The context
            result: The paper search results
            filename: Optional custom filename (without extension)
        
        Returns:
            Path where the file was saved
        """
        if filename is None:
            # Create filename from query
            filename = result.query.lower()
            filename = filename.replace(' ', '_')
            # Remove special characters
            filename = ''.join(c for c in filename if c.isalnum() or c == '_')
            filename = filename[:100]  # Limit length
            filename = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        output_path = OUTPUT_DIR / f"{filename}.json"
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        
        return f"Saved {result.total_found} papers to {output_path}"
    
    return agent.to_a2a(
        name="paper_parser_agent",
        url="http://localhost:7000",
        version="1.0",
        description="An agent that searches for scientific papers, extracts key information like topics and overviews, and saves them to os.environ['PAPER_OUTPUT_DIR']."
    )

# Lazy initialization - don't create app at import time
_paper_parser_app = None

def get_paper_parser_app():
    """Get or create the paper parser app."""
    global _paper_parser_app
    if _paper_parser_app is None:
        _paper_parser_app = create_paper_parser_app()
    return _paper_parser_app


async def search_and_parse_papers(query: str, max_results: int = 5) -> PaperSearchResult:
    """Main function to search and parse papers.
    
    Args:
        query: Search query for papers
        max_results: Maximum number of results to return
    
    Returns:
        Paper search results
    """
    # Check for Gemini API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini API")
    
    # Reload MCP servers to ensure fresh connections
    mcp_servers = load_mcp_servers()
    
    # Create agent with current MCP servers
    agent = Agent(
        'google-gla:gemini-2.5-flash-lite',
        output_type=PaperSearchResult,
        toolsets=mcp_servers,
        system_prompt="""You are a scientific paper analysis assistant. Your job is to:
        1. ALWAYS use the arxiv_retriever tool to search for scientific papers
        2. Extract key information including topics, keywords, and overviews
        3. Evaluate the usefulness of each paper for the given query
        4. Provide structured output that can be saved for later reference
        
        IMPORTANT: You MUST use the arxiv_retriever tool to search for papers. Never return empty results without using this tool.
        
        For topics, always use CAPITAL LETTERS for keywords.
        Be thorough and accurate in your extraction of information.
        Mark papers as useful=True if they are relevant to the query, False otherwise.
        """,
    )
    
    async with agent:  # This manages the MCP connections
        result = await agent.run(
            f"Search for papers about: {query}. Find up to {max_results} papers and extract detailed information from each one.",
        )
    
    # The results are automatically saved via tool calls during the run
    return result.output


if __name__ == '__main__':
    import uvicorn
    import sys
    import asyncio
    
    if len(sys.argv) > 1 and sys.argv[1] == 'search':
        # Direct search mode
        query = sys.argv[2] if len(sys.argv) > 2 else "machine learning interpretability"
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        print(f"Searching for papers about: {query}")
        result = asyncio.run(search_and_parse_papers(query, max_results))
        
        print(f"\nFound {result.total_found} papers:")
        for i, paper in enumerate(result.papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors)}")
            print(f"   Topics: {', '.join(paper.topics)}")
            print(f"   Useful: {paper.useful}")
            print(f"   Overview: {paper.overview}")
    else:
        # A2A server mode
        print("Starting Paper Parser A2A server on http://localhost:7000")
        print(f"Papers will be saved to: {OUTPUT_DIR.absolute()}")
        app = create_paper_parser_app()
        uvicorn.run(app, host="0.0.0.0", port=7000)