import asyncio
from .registry import IntelligentAgentRegistry
import httpx
# The orchestrator module now only exposes the orchestrator logic and main() for programmatic use.
async def main():
    """Main orchestrator entry point (for programmatic use)."""
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
        print("🧠 Orchestrator ready.")
        # No CLI loop here; use client.py for user interaction.
if __name__ == "__main__":
    asyncio.run(main())
