from pydantic_ai import Agent

from dotenv import load_dotenv

load_dotenv()

llm="google-gla:gemini-2.5-flash-lite"

greeting_agent = Agent(model = llm,
        output_type=str,
        instructions=None,
        system_prompt="You are a greeting agent."
        )

greeting_app = greeting_agent.to_a2a(name="greeting_agent",
             url="http://localhost:5000",
             version ="0.1",
             description="An agent that can greet people.",
        )

if __name__ == "__main__":
        import uvicorn
        uvicorn.run(greeting_app, host="0.0.0.0", port=5000)