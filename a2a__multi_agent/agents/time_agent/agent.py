from pydantic_ai import Agent

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

llm="google-gla:gemini-2.5-flash-lite"

tell_time_agent = Agent(model = llm,
        output_type=str,
        instructions=None,
        system_prompt=f"You are a tell_time agent. you need to give the time. The time is {datetime.now().strftime('%H:%M')}."
        )


app_time = tell_time_agent.to_a2a(name="time_agent",
             url="http://localhost:6000",
             version ="0.1",
             description="An agent that can tell the current time.",
        )

if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app_time, host="0.0.0.0", port=6000)