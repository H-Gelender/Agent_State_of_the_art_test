import uvicorn
import os 
from .agent import agent
from pydantic_ai.models.google import GoogleModel
from dotenv import load_dotenv
load_dotenv()
# --- Agent and Server Configuration ---
async def main():
    """Main function to run the agent."""
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    print("Hello! I am an agent that can search for papers on arXiv.")
    print("What topic are you interested in today?")

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            # Run the agent with the user's query
            response = await agent.run(user_input)
            print("\nAssistant:")
            print(response)
            print("\nWhat else can I help you find?")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

# --- Main entrypoint to run the server ---

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
