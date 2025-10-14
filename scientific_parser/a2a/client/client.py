import asyncio
import httpx
from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart
import uuid

# --- Agent Discovery ---

async def fetch_agent_card(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{url}/.well-known/agent-card.json")
        resp.raise_for_status()
        return resp.json()

async def discover_agents(agent_urls):
    agents = []
    for url in agent_urls:
        try:
            card = await fetch_agent_card(url)
            agents.append({'url': url, 'card': card})
        except Exception as e:
            print(f"Failed to fetch agent card from {url}: {e}")
    return agents

# --- Skill Matching (simple string match for demo) ---

def select_agent(agents, prompt):
    prompt_lower = prompt.lower()
    for agent in agents:
        for skill in agent['card'].get('skills', []):
            if any(tag in prompt_lower for tag in skill.get('tags', [])):
                return agent
    # fallback: return first agent
    return agents[0] if agents else None

# --- Orchestrator Main Logic ---

async def orchestrate_task(agent_urls, prompt):
    agents = await discover_agents(agent_urls)
    agent = select_agent(agents, prompt)
    if not agent:
        raise Exception("No suitable agent found")
    print(f"Routing to agent: {agent['card']['name']} at {agent['url']}")
    client = A2AClient(base_url=agent['url'])
    message = Message(
        role="user",
        parts=[TextPart(kind="text", text=prompt)],
        kind="message",
        message_id=str(uuid.uuid4())
    )
    send_response = await client.send_message(message)
    print("send response: ",send_response)
    task_id = send_response["result"]["id"]
    # Poll for result
    while True:
        get_response = await client.get_task(task_id)
        print("get response: ",get_response)
        task = get_response["result"]
        state = task["status"]["state"]
        if state == "completed":
            # Get the agent's reply
            for msg in task["history"]:
                if msg["role"] == "agent":
                    for part in msg["parts"]:
                        if part["kind"] == "text":
                            print(f"Agent reply: {part['text']}")
            break
        elif state in ("failed", "canceled", "rejected"):
            print(f"Task ended with state: {state}")
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    from discovery import AgentDiscovery
    import logging
    logging.basicConfig(level=logging.INFO)
    discovery = AgentDiscovery()
    prompt = input("What do you want to do? ")
    asyncio.run(orchestrate_task(discovery.urls, prompt))