# A2A Agent Framework - Complete Guide

A comprehensive framework for building Agent-to-Agent (A2A) communication systems with intelligent orchestration and dynamic routing.

## 📚 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [Creating Your First A2A Agent](#creating-your-first-a2a-agent)
- [Agent Registry & Discovery](#agent-registry--discovery)
- [Intelligent Orchestration](#intelligent-orchestration)
- [Running the System](#running-the-system)
- [Examples in This Repo](#examples-in-this-repo)

---

## 🎯 Overview

This framework enables you to build autonomous agents that communicate seamlessly using the **A2A (Agent-to-Agent) protocol**. The system includes:

- **Agents**: Independent AI services built with any library (Pydantic AI, LangGraph, etc.)
- **Agent Executor**: Bridges your agent with the A2A protocol
- **Agent Registry**: Centralized discovery and capability mapping
- **Orchestrator**: Intelligently routes queries to the right agent using LLM or keyword matching
- **Client**: Interactive interface for users to query the system

### Key Features
✅ **Library Agnostic**: Use Pydantic AI, LangGraph, LangChain, or any custom logic  
✅ **Auto Discovery**: Agents register their capabilities automatically  
✅ **Smart Routing**: LLM-based routing with keyword fallback  
✅ **Streaming Support**: Real-time responses via Server-Sent Events  
✅ **Extensible**: Easy to add new agents without modifying existing code

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────────┐
│  Client (client.py)                         │
│  - User interaction                         │
│  - CLI interface                            │
└──────┬──────────────────────────────────────┘
       │
       v
┌─────────────────────────────────────────────┐
│  Orchestrator (orchestrator.py)             │
│  - Query routing (LLM + fallback)           │
│  - Agent selection logic                    │
└──────┬──────────────────────────────────────┘
       │
       v
┌─────────────────────────────────────────────┐
│  Registry (registry.py)                     │
│  - Agent discovery                          │
│  - Capability mapping                       │
│  - Agent card storage                       │
└──────┬──────────────────────────────────────┘
       │
       v
┌─────────────────────────────────────────────┐
│  Agent Registry JSON                        │
│  { "agent_name": "http://localhost:5000" }  │
└──────┬──────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────┐
│  Individual Agents (agents/)             │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Agent 1      │  │ Agent 2      │     │
│  │ (port 5000)  │  │ (port 8000)  │     │
│  │              │  │              │     │
│  │ - Agent      │  │ - Agent      │     │
│  │ - Executor   │  │ - Executor   │     │
│  │ - Server     │  │ - Server     │     │
│  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. **Agent (`agent.py`)**
The core AI logic of your agent. This is where you:
- Define your LLM model and configuration
- Implement agent behavior and personality
- Add tools, functions, or capabilities
- Use **any library** you prefer (Pydantic AI, LangGraph, custom)

**Key Responsibility**: Process queries and generate responses

**Example Structure**:
```python
# Can use Pydantic AI, LangGraph, or custom implementation
agent = Agent(
    model="google-gla:gemini-2.5-flash-lite",
    system_prompt="Your agent's personality and instructions"
)
```

---

### 2. **Agent Executor (`agent_executor.py`)**
The bridge between your agent and the A2A protocol. This component:
- Receives requests via the A2A protocol standard
- Extracts user input from the request context
- Calls your agent logic to process the query
- Sends back responses using A2A events (working, artifacts, completed)
- Handles errors and status updates

**Key Responsibility**: Protocol compliance and event management

**Flow**:
1. Receive request → Extract user input
2. Create task → Send "working" status
3. Call your agent → Get response
4. Send artifact (result) → Send "completed" status

**Important Classes**:
- `AgentExecutor`: Base class to implement
- `RequestContext`: Contains user message and task info
- `EventQueue`: Sends status updates and results
- `TaskStatusUpdateEvent`: Updates task state (working, completed, error)
- `TaskArtifactUpdateEvent`: Sends the actual response

---

### 3. **Agent Server (`__main__.py`)**
The HTTP server that exposes your agent to the network. It:
- Creates an A2A-compliant web server
- Exposes the **Agent Card** at `/` (describes capabilities)
- Handles incoming requests at `/a2a/message`
- Manages task storage and push notifications
- Configures host, port, and server settings

**Key Responsibility**: Network exposure and A2A protocol endpoints

**Agent Card**: A JSON description of your agent including:
- `name`: Agent identifier
- `description`: What the agent does
- `skills`: List of capabilities with examples
- `tags`: Keywords for routing
- `capabilities`: Streaming, push notifications, etc.
- `url`: Where the agent is hosted

---

### 4. **Agent Registry (`client/registry.py`)**
Manages the discovery and tracking of available agents. It:
- Loads agent URLs from `agent_registry.json`
- Queries each agent's `/` endpoint to get their Agent Card
- Stores agent capabilities, skills, tags, and descriptions
- Provides methods to get agent information
- Creates A2A clients for communication

**Key Responsibility**: Agent discovery and capability mapping

**Core Methods**:
- `load_registry()`: Reads JSON file with agent URLs
- `discover_agents()`: Fetches Agent Cards from all registered agents
- `get_agents_info()`: Returns formatted capability list for LLM routing
- `get_client()`: Returns A2A client for a specific agent

---

### 5. **Orchestrator (`client/orchestrator.py`)**
The intelligent routing system that decides which agent should handle each query. It uses:

**LLM-Based Routing** (Primary):
- Creates a Pydantic AI agent specifically for routing
- Passes agent capabilities and user query to Gemini
- Gets back the best agent name to handle the request
- Falls back to keyword matching if LLM fails

**Keyword-Based Fallback** (Secondary):
- Searches query for keywords in agent descriptions, skills, and tags
- Matches specific patterns (e.g., "time" → time agent, "hello" → greeting agent)
- Uses generic tag matching
- Defaults to first agent if nothing matches

**Key Responsibility**: Route queries to the most appropriate agent

**Key Functions**:
- `call_gemini_api()`: Uses Pydantic AI agent to select the best agent
- `intelligent_route_query()`: Main routing logic (LLM + fallback)
- `smart_fallback_routing()`: Keyword-based routing when LLM unavailable
- `send_to_agent()`: Sends the query to selected agent via A2A protocol

---

### 6. **Client (`client/client.py`)**
The user-facing interface that:
- Provides an interactive CLI loop
- Takes user input
- Calls the orchestrator to route queries
- Displays responses

**Key Responsibility**: User interaction

---

### 7. **Agent Registry JSON (`client/agent_registry.json`)**
A simple configuration file mapping agent names to URLs:
```json
{
  "greeting_agent": "http://localhost:5000",
  "telltime_agent": "http://localhost:8000"
}
```

**Key Responsibility**: Static agent location configuration

---

## 🚀 Creating Your First A2A Agent

### Step 1: Plan Your Agent
Decide:
- **Purpose**: What will your agent do?
- **Skills**: What specific capabilities will it have?
- **Tags**: Keywords for routing (e.g., "greeting", "time", "weather")
- **Library**: Pydantic AI, LangGraph, or custom?

### Step 2: Create Directory Structure
```bash
cd agents
mkdir my_new_agent
cd my_new_agent
touch __init__.py agent.py agent_executor.py __main__.py
```

### Step 3: Implement Agent Logic
In `agent.py`, create your AI agent using your preferred library. This is where your agent's "brain" lives.

**Key Points**:
- Use any LLM library you want
- Focus on the agent's behavior and responses
- Don't worry about A2A protocol here

### Step 4: Create Agent Executor
In `agent_executor.py`, implement the `AgentExecutor` class:

**Must implement**:
- `__init__()`: Initialize your agent
- `execute()`: Main method that:
  - Gets user input from `context.get_user_input()`
  - Processes with your agent
  - Sends events via `event_queue.enqueue_event()`
  - Returns results as artifacts
- `cancel()`: Optional cancellation logic

**Event Flow**:
1. Create/get task
2. Send `TaskStatusUpdateEvent` with state=`working`
3. Process query with your agent
4. Send `TaskArtifactUpdateEvent` with response
5. Send `TaskStatusUpdateEvent` with state=`completed`

### Step 5: Create Server Entry Point
In `__main__.py`:

**Define Agent Card**:
```python
AgentCard(
    name="My Agent",
    description="Clear description of what this agent does",
    skills=[
        AgentSkill(
            id="my_skill",
            name="Skill Name",
            description="What this skill does",
            tags=["keyword1", "keyword2"],  # For routing!
            examples=["Example query 1", "Example query 2"]
        )
    ]
)
```

**Setup Server**:
- Create executor instance
- Setup task store, push notifications
- Create `A2AStarletteApplication`
- Run with uvicorn

### Step 6: Register Your Agent
Add to `client/agent_registry.json`:
```json
{
  "my_new_agent": "http://localhost:YOUR_PORT"
}
```

### Step 7: Test Your Agent
```bash
# Terminal 1: Start your agent
uv run -m agents.my_new_agent --port YOUR_PORT

# Terminal 2: Start client
uv run -m client

# Type queries that match your agent's tags/skills
```

---

## 🔍 Agent Registry & Discovery

### How Discovery Works

1. **Client starts** → Reads `agent_registry.json`
2. **For each agent URL** → HTTP GET request to `/`
3. **Agent responds** → Returns Agent Card (JSON)
4. **Registry stores**:
   - Agent name, description, URL
   - Skills (with examples and tags)
   - Capabilities (streaming, etc.)
5. **Registry creates** → A2A client for each agent

### Agent Card Structure
The Agent Card is crucial for discovery and routing:

```json
{
  "name": "greeting_agent",
  "description": "An agent that can greet people",
  "url": "http://localhost:5000",
  "skills": [
    {
      "id": "greet",
      "name": "Greet User",
      "description": "Provides friendly greetings",
      "tags": ["greeting", "hello", "hi"],
      "examples": ["Hello", "Hi there", "Good morning"]
    }
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  }
}
```

**Tags are critical**: They're used for keyword-based routing when LLM routing fails!

---

## 🧠 Intelligent Orchestration

### Routing Strategy

The orchestrator uses a **two-tier routing system**:

#### Tier 1: LLM-Based Routing (Primary)
**How it works**:
1. Load prompt template from `orchestrator_prompt.py`
2. Format prompt with:
   - All available agents and their capabilities
   - User's query
3. Send to Pydantic AI agent using Gemini
4. Gemini analyzes and returns best agent name
5. Validate agent exists
6. Send query to that agent

**Advantages**:
- Understands intent, not just keywords
- Can handle complex queries
- Learns from agent descriptions

**When it fails**:
- No API key set
- API rate limit
- Network issues
- Invalid response

#### Tier 2: Keyword-Based Routing (Fallback)
**How it works**:
1. Convert query to lowercase
2. For each registered agent:
   - Check if query keywords match agent's:
     - Description
     - Skill names and descriptions
     - Tags
     - Examples
3. Return first matching agent
4. If no match, return first available agent

**Advantages**:
- Fast and reliable
- No API calls needed
- Deterministic

**When to use**:
- LLM routing unavailable
- Testing without API keys
- Guaranteed routing

### Customizing Routing

**Add more keywords** in `orchestrator.py`:
```python
if any(keyword in query_lower for keyword in ['your', 'custom', 'keywords']):
    if any(keyword in description + skills + tags for keyword in ['matching', 'terms']):
        return agent_name
```

**Improve LLM routing** by editing `orchestrator_prompt.py`:
- Add more context
- Provide better examples
- Specify routing rules

---

## 🎮 Running the System

### Setup Environment

```bash
# Install dependencies
make install

# Or manually
pip install uv
uv pip install -r requirements.txt

# Configure .env file
echo 'GOOGLE_API_KEY="your-api-key"' > .env
```

### Start Agents

```bash
# Terminal 1: Greeting Agent
uv run -m agents.pydantic_agent --port 5000

# Terminal 2: Time Agent (if you have one)
uv run -m agents.langgraph_agent --port 8000
```

### Start Client/Orchestrator

```bash
# Terminal 3: Interactive Client
uv run -m client
```

### Using the System

```
You: Hello!
🎯 LLM selected agent: greeting_agent
Assistant: Hi there! How can I help you today?

You: What time is it?
🎯 LLM selected agent: telltime_agent  
Assistant: The current time is 3:45 PM

You: exit
👋 Goodbye!
```

### Check Agent Cards

Visit in browser or curl:
```bash
curl http://localhost:5000/
# Returns Agent Card JSON
```

---

## 📦 Examples in This Repo

### 1. **Pydantic AI Agent** (`agents/pydantic_agent/`)
- Simple greeting agent
- Uses Pydantic AI library
- Demonstrates basic agent structure
- Tags: `["greeting", "conversation"]`

**Files**:
- `agent.py`: Pydantic AI agent with greeting system prompt
- `agent_executor.py`: A2A protocol executor
- `__main__.py`: Server with Agent Card

### 2. **LangGraph Agent** (`agents/langgraph_agent/`)
- More complex agent with state management
- Uses LangGraph for workflow
- Demonstrates advanced patterns
- Configurable via `config.py`

**Files**:
- `agent.py`: LangGraph agent setup
- `agent_executor.py`: A2A executor with streaming
- `config.py`: Agent configuration
- `__main__.py`: Server entry point

### 3. **Client System** (`client/`)
- Complete orchestration system
- Registry management
- LLM-based routing

**Files**:
- `registry.py`: Agent discovery and management
- `orchestrator.py`: Intelligent routing logic
- `prompt.py`: LLM routing prompts
- `client.py`: User interface
- `agent_registry.json`: Agent URL configuration

---

## 🔑 Key Concepts

### Agent Card vs Agent
- **Agent Card**: Metadata describing capabilities (exposed at `/`)
- **Agent**: The actual AI logic that processes queries

### Executor vs Agent
- **Agent**: Your AI logic (any library)
- **Executor**: A2A protocol adapter (always uses a2a library)

### Registry vs Orchestrator
- **Registry**: Discovers and tracks agents
- **Orchestrator**: Routes queries to agents

### LLM Routing vs Keyword Routing
- **LLM**: Smart, context-aware, requires API
- **Keyword**: Fast, deterministic, always available

---

## 🛠️ Makefile Commands

```bash
make install          # Install dependencies
make run-pydantic     # Run pydantic agent
make run-langgraph    # Run langgraph agent  
make run-client       # Run client/orchestrator
```

---

## 📝 Best Practices

1. **Agent Cards**:
   - Write clear descriptions
   - Add comprehensive tags
   - Provide good examples

2. **Tags**:
   - Use lowercase
   - Include synonyms
   - Think about user language

3. **Error Handling**:
   - Always send task status updates
   - Use try-except in executors
   - Log errors for debugging

4. **Ports**:
   - Use different ports for each agent
   - Document port assignments
   - Update registry JSON

5. **Testing**:
   - Test agent alone first
   - Then test with orchestrator
   - Try both LLM and fallback routing

---

## 🚨 Troubleshooting

**Agent not discovered?**
- Check agent is running
- Verify URL in `agent_registry.json`
- Test agent endpoint directly: `curl http://localhost:PORT/`

**Routing to wrong agent?**
- Check agent tags in Agent Card
- Review orchestrator fallback keywords
- Verify GOOGLE_API_KEY for LLM routing

**Agent errors?**
- Check agent logs
- Verify `.env` file has API keys
- Test agent execute method directly

---

## 📚 Further Reading

- [A2A Protocol Specification](https://github.com/google/a2a)
- [Pydantic AI Documentation](https://ai.pydantic.dev)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

**Happy Agent Building! 🤖**
