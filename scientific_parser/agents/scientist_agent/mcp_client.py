# arxiv_mcp_client.py
import os
import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv
load_dotenv()
# 1. Create a client that points to our running MCP server.
#    The URL must match the one the server is running on.
server = MCPServerStreamableHTTP('http://localhost:8000/mcp')

# 2. Create the agent and register the server as a 'toolset'.
#    The agent will automatically discover the 'arxiv_retriever' tool from the server.
agent = Agent(
    model = "google-gla:gemini-2.5-flash-lite", 
    toolsets=[server]
)

async def main():
    """Main function to run the agent."""
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    # 3. Use 'async with agent' to manage the connection to the MCP server.
    #    This will handle connecting before the run and disconnecting after.
    async with agent:
        print("Agent is connected to the MCP server. What papers are you looking for?")
        user_query = input("> ")
        
        if user_query.lower() in ["exit", "quit"]:
            return

        result = await agent.run(user_query)
        print("\nAssistant:")
        print(result.output)

if __name__ == "__main__":
    asyncio.run(main())