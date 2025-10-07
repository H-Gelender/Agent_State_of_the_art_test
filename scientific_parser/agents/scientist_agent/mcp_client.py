import os
import json
import asyncio

from typing import List, Any
from pydantic import BaseModel, Field

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv
load_dotenv()

class KeywordPapers(BaseModel):
    keywords: List[str] = Field(..., description="Extract the keywords of the document (in capital letters).")
    usefull: bool = Field(..., description="Whether the papers found are useful.")
    title: str = Field(..., description="The title of the paper.")

class ArxivPaper(BaseModel):
    paper: List[KeywordPapers] = Field(..., description="List of papers found for the keywords.")
def load_mcp_servers(config_path="mcp_config.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_path)
    with open(config_path, "r") as f:
        config = json.load(f)
    servers = []
    for server_name, server_cfg in config.get("mcpServers", {}).items():
        # You can expand this logic to support different hosts/ports if needed
        # For now, we assume all servers run on localhost with an incremented port
        # Or you can add "host"/"port" fields to your JSON if needed
        # Here, as an example, we stick with the original URL pattern:
        url = f"http://localhost:8000/mcp"  # Default; adjust if server_cfg has host/port info
        servers.append(MCPServerStreamableHTTP(url))
    return servers


async def main():
    """Main function to run the agent."""
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    # Load MCP servers from config
    toolsets = load_mcp_servers()

    # Create the agent with all servers as toolsets
    agent = Agent(
        model="google-gla:gemini-2.5-flash-lite",
        toolsets=toolsets,
        output_type=ArxivPaper,
        system_prompt="You're a helpful research assistant that finds scientific papers on arXiv based on user queries, and parse it."
    )

    async with agent:
        print("Agent is connected to the MCP servers. What papers are you looking for?")
        user_query = input("> ")

        if user_query.lower() in ["exit", "quit"]:
            return

        result = await agent.run(user_query)
        for paper in result.output.paper:
            json_path = os.path.join("data/metadata/", f"{paper.title}.json")

            # We use .model_dump_json() which is a convenient Pydantic method
            # to convert the object to a nicely formatted JSON string.
            if paper.usefull:
                print(f"📄 Found useful paper: '{paper.title}'")
                print(f"    Keywords: {paper.keywords}")
                dico = {"keywords": paper.keywords}
                json_content = json.dumps(dico, indent=4)

                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(json_content)
                print(f"✅ Saved metadata for: '{paper.title}'")
            
            else:
                pdf_path = "data/pdf/" + f"{paper.title}.pdf"
                # If the paper is NOT useful, just remove the PDF
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    print(f"❌ Removed PDF for non-useful paper: '{paper.title}'")
                    
        print("\nAssistant:")
        print(result.output)

if __name__ == "__main__":
    asyncio.run(main())