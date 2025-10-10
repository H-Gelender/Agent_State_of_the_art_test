import asyncio
from .orchestrator import intelligent_route_query, IntelligentAgentRegistry
import httpx

async def client_main():
    registry = IntelligentAgentRegistry()
    if not registry.load_registry():
        print("❌ Failed to load agent registry")
        return
    async with httpx.AsyncClient() as client:
        discovered = await registry.discover_agents(client)
        if discovered == 0:
            print("❌ No agents connected")
            return
        print(f"✅ Connected to {discovered} agents")
        print("🧠 Using intelligent LLM-based routing")
        print("💬 Ready! Type 'exit' to quit.\n")
        while True:
            try:
                query = input("You: ").strip()
                if not query or query.lower() in ["exit", "quit"]:
                    break
                response = await intelligent_route_query(registry, query)
                print(f"Assistant: {response}\n")
            except KeyboardInterrupt:
                break
        print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(client_main())
