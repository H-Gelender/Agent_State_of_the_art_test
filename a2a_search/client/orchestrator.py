
import httpx
import logging
import os
from uuid import uuid4
from typing import Any

from a2a.types import MessageSendParams, SendMessageRequest

from dotenv import load_dotenv

from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from .prompt import PROMPT

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .registry import IntelligentAgentRegistry


# --- Pydantic AI Agent setup for orchestrator ---
@dataclass
class OrchestratorDeps:
    api_key: str
    http_client: httpx.AsyncClient

orchestrator_agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    output_type=str,
    deps_type=OrchestratorDeps,
)

@orchestrator_agent.system_prompt
def get_system_prompt(ctx: RunContext[OrchestratorDeps]) -> str:
    # The system prompt is static, loaded from the prompt file
    return "You are an intelligent agent orchestrator."

async def call_gemini_api(prompt: str) -> Any:
    """Use a Pydantic AI Agent to orchestrate the workflow and delegate tasks."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    async with httpx.AsyncClient() as http_client:
        deps = OrchestratorDeps(api_key=api_key, http_client=http_client)
        result = await orchestrator_agent.run(prompt, deps=deps)
        return result.output

async def smart_fallback_routing(registry: IntelligentAgentRegistry, query: str) -> str:
    """Smart keyword-based routing when LLM is not available."""
    query_lower = query.lower().strip()
    
    for agent_name, info in registry.agent_cards.items():
        description = info['description'].lower()
        skills_text = ' '.join([
            f"{skill['name']} {skill['description']} {' '.join(skill.get('examples', []))}"
            for skill in info['skills']
        ]).lower()
        tags_text = ' '.join(info.get('tags', [])).lower()  # <-- Ajout des tags

        # Recherche dans description, skills et tags
        # Debugging client.
        if any(keyword in query_lower for keyword in ['time', 'clock', 'hour', 'when', 'minute']):
            if any(keyword in description + ' ' + skills_text + ' ' + tags_text for keyword in ['time', 'clock', 'current']):
                logger.info(f"🎯 Smart routing: {query} → {agent_name} (time-related)")
                return agent_name

        if any(keyword in query_lower for keyword in ['hello', 'hi', 'greet', 'how are you', 'good morning']):
            if any(keyword in description + ' ' + skills_text + ' ' + tags_text for keyword in ['greet', 'friendly', 'conversation', 'hello']):
                logger.info(f"🎯 Smart routing: {query} → {agent_name} (greeting)")
                return agent_name

        # Recherche générique sur les tags
        if any(tag in query_lower for tag in info.get('tags', [])):
            logger.info(f"🎯 Smart routing: {query} → {agent_name} (tag match)")
            return agent_name

    # Fallback to first agent
    first_agent = next(iter(registry.agent_cards.keys()))
    logger.info(f"🎯 Smart routing: {query} → {first_agent} (fallback)")
    return first_agent

async def intelligent_route_query(registry: IntelligentAgentRegistry, query: str) -> str:
    """Use LLM to intelligently route query to the most appropriate agent."""
    
    # Handle list agents command
    if query.lower().strip() in ['list', 'agents', 'list agents', 'show agents']:
        return registry.get_agents_info()
    
    if not registry.agent_cards:
        return "❌ No agents available"
    
    # Try LLM routing first, then smart fallback
    try:
        # Get agent information for LLM context
        agents_context = registry.get_agents_info()
        
        # Create prompt for agent selection
        prompt = PROMPT.format(agents_context=agents_context, query=query)

        # Try Gemini API first
        gemini_response = await call_gemini_api(prompt)
        
        if gemini_response:
            selected_agent = gemini_response.strip().lower()
            
            # Validate the selected agent exists
            if selected_agent in registry.agent_cards:
                logger.info(f"🎯 LLM selected agent: {selected_agent}")
                return await send_to_agent(registry, query, selected_agent)
            else:
                # Try partial match
                for agent_name in registry.agent_cards.keys():
                    if agent_name in selected_agent or selected_agent in agent_name:
                        logger.info(f"🎯 LLM selected agent (partial match): {agent_name}")
                        return await send_to_agent(registry, query, agent_name)
        
        # Fallback to smart routing if LLM fails or no API key
        logger.info("🧠 Using smart fallback routing")
        selected_agent = await smart_fallback_routing(registry, query)
        return await send_to_agent(registry, query, selected_agent)
            
    except Exception as e:
        logger.warning(f"⚠️ LLM routing failed: {e}")
        # Use smart fallback routing
        logger.info("🧠 Using smart fallback routing")
        selected_agent = await smart_fallback_routing(registry, query)
        return await send_to_agent(registry, query, selected_agent)

async def send_to_agent(registry: IntelligentAgentRegistry, query: str, agent_name: str) -> str:
    """Send query to specific agent."""
    client = registry.get_client(agent_name)
    if not client:
        return f"❌ Agent {agent_name} not available"
    
    try:
        # Send message
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
        response = await client.send_message(request)
        
        # Extract response (same pattern as working client)
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            task = response.root.result
            if task.artifacts and task.artifacts[0].parts:
                return task.artifacts[0].parts[0].root.text
            return str(task)
        return str(response)
        
    except Exception as e:
        return f"❌ Error: {e}"


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