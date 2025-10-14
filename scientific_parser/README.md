# Scientific Paper Agent - A2A Framework Implementation

This repository contains a scientific paper search agent that demonstrates the integration of **Model Context Protocol (MCP)** servers with **Agent-to-Agent (A2A)** communication using both Pydantic AI and framework-agnostic A2A SDK approaches.

## Overview

The agent searches ArXiv for scientific papers, downloads PDFs, extracts metadata, and provides structured results. It showcases:

- **MCP Integration**: Uses ArXiv MCP server for paper retrieval
- **A2A Communication**: Implements both Pydantic AI and A2A SDK patterns  
- **Gemini API**: Powered by Google's Gemini 2.5 Flash Lite model
- **Async Architecture**: Proper event loop and connection management

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   A2A Client    │───▶│  Scientific      │───▶│   ArXiv MCP     │
│                 │    │  Paper Agent     │    │   Server        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              │                        ▼
                              ▼                ┌─────────────────┐
                       ┌──────────────────┐    │   ArXiv API     │
                       │  Gemini API      │    │   PDF Download  │
                       │  (LLM Processing)│    │   Metadata Ext. │
                       └──────────────────┘    └─────────────────┘
```

## Components

### 1. ArXiv MCP Server (`a2a/agents/scientific_paper_agent/arxiv_server.py`)
- **Purpose**: MCP server that provides `arxiv_retriever` tool
- **Port**: 8000
- **Features**: 
  - Paper search via ArXiv API
  - PDF download and storage
  - Metadata extraction
  - Structured response format

### 2. Scientific Paper Agent - Pydantic AI Version (`a2a/agents/scientific_paper_agent/`)
- **Purpose**: Original Pydantic AI agent with `.to_a2a()` integration
- **Port**: 7000
- **Features**:
  - Direct MCP connection management
  - Gemini API integration  
  - Structured paper analysis
  - **Issue**: A2A integration doesn't properly manage MCP connections

### 3. Scientific Paper Agent - A2A SDK Version (`agents/orchestrator_agent/`)
- **Purpose**: Framework-agnostic A2A SDK implementation
- **Port**: 7000  
- **Features**:
  - `AgentExecutor` pattern for proper async context management
  - Separate event loop for MCP operations
  - Full A2A SDK compliance with `AgentCard` and skills
  - **Advantage**: Bypasses Pydantic AI A2A connection issues

## Setup Instructions

### Prerequisites
```bash
# Environment Variables Required
GOOGLE_API_KEY=your_gemini_api_key_here
PAPER_OUTPUT_DIR=./data  # Optional, defaults to ./data
MCP_CONFIG=mcp_config.json  # Optional, defaults to mcp_config.json
```

### Installation
```bash
cd scientific_parser
pip install -r requirements.txt
```

## Usage Workflow

### Option 1: Direct Search (Recommended for Testing)
```bash
# Navigate to scientific_parser directory
cd scientific_parser

# Run direct search (bypasses A2A, uses MCP directly)
.venv\Scripts\python.exe a2a\agents\scientific_paper_agent\__main__.py search "machine learning" 3

# This will:
# 1. Connect to MCP server on localhost:8000
# 2. Search ArXiv for papers
# 3. Download PDFs to ./data/pdf/
# 4. Extract metadata to ./data/metadata/
# 5. Display structured results
```

### Option 2: Full A2A Workflow (Advanced)

#### Step 1: Start ArXiv MCP Server
```bash
# Terminal 1 - Start MCP Server
.venv\Scripts\python.exe a2a\agents\scientific_paper_agent\arxiv_server.py

# Output: Starting ArXiv MCP server on http://localhost:8000
```

#### Step 2: Start A2A SDK Agent  
```bash
# Terminal 2 - Start A2A SDK Agent
.venv\Scripts\python.exe agents\orchestrator_agent\__main___a2a_sdk.py

# Output: 
# Loading MCP server: arxiv_server at http://localhost:8000/mcp
# INFO:__main__:Starting Scientific Paper A2A Agent Server (A2A SDK version)...
# INFO:__main__:Server will run on http://localhost:7000
```

#### Step 3: Interact with A2A Client
```bash
# Terminal 3 - Start A2A Client
.venv\Scripts\python.exe a2a\client\client.py

# Input: "Find papers about quantum computing"
# The client will:
# 1. Discover agents via agent card
# 2. Select scientific paper agent
# 3. Send task request
# 4. Receive structured results with papers
```

## Agent Card & Skills

The A2A SDK agent exposes the following skills:

```json
{
  "name": "Scientific Paper Agent",
  "skills": [
    {
      "id": "arxiv_search",
      "name": "ArXiv Paper Search",
      "description": "Search ArXiv for scientific papers on any topic and download PDFs with metadata extraction.",
      "examples": [
        "Find papers about machine learning",
        "Search for quantum computing research",
        "Look for papers on climate change"
      ]
    },
    {
      "id": "scientific_research", 
      "name": "Scientific Research Assistant",
      "description": "Comprehensive scientific literature search and analysis with automatic PDF download and metadata extraction."
    }
  ]
}
```

## Example Results

### Direct Search Output
```
Searching for papers about: machine learning

Found 2 papers:

1. Lecture Notes: Optimization for Machine Learning
   Authors: Elad Hazan
   Topics: OPTIMIZATION, MACHINE LEARNING, GRADIENT DESCENT
   Useful: True
   Overview: This paper provides lecture notes on optimization for machine learning...

2. An Optimal Control View of Adversarial Machine Learning  
   Authors: Xiaojin Zhu
   Topics: ADVERSARIAL MACHINE LEARNING, OPTIMAL CONTROL
   Useful: True
   Overview: This paper presents an optimal control perspective on adversarial machine learning...
```

### File Structure After Search
```
data/
├── pdf/
│   ├── 1909.03550v1.pdf
│   └── 1811.04422v1.pdf
└── metadata/
    ├── 1909.03550v1.json
    └── 1811.04422v1.json
```

## Makefile Commands

```bash
# Install dependencies
make install

# Start MCP server
make run-mcp-server

# Start Pydantic AI A2A agent
make run-scientific-agent  

# Start A2A SDK agent (recommended)
make run-scientific-agent-sdk

# Direct search
make search QUERY='machine learning' RESULTS=3

# Start A2A client
make a2a-client

# Show help
make help
```

## Technical Implementation Details

### MCP Connection Management
The A2A SDK version uses proper async context management:
```python
# Separate event loop for MCP operations
def _run_paper_search_sync(self, query: str) -> dict:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop) 
    try:
        result = loop.run_until_complete(search_and_parse_papers(query, max_results))
        return result
    finally:
        loop.close()
```

### A2A SDK Pattern
```python
class ScientificPaperAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Get user input
        query = context.get_user_input()
        
        # Run search in separate thread to avoid blocking
        result = await asyncio.to_thread(self._run_paper_search_sync, query)
        
        # Send results via event queue
        await event_queue.enqueue_event(TaskArtifactUpdateEvent(...))
```

### Gemini API Integration
```python
agent = Agent(
    'google-gla:gemini-2.5-flash-lite',
    output_type=PaperSearchResult,
    toolsets=mcp_servers,  # ArXiv MCP server tools
    system_prompt="You are a scientific paper analysis assistant..."
)
```

## Known Issues & Solutions

### Issue 1: Pydantic AI A2A Integration
**Problem**: `.to_a2a()` method doesn't properly manage MCP connections
**Solution**: Use A2A SDK version (`agents/orchestrator_agent/`) instead

### Issue 2: A2A Server Shutdown
**Problem**: A2A server shuts down when accessed via HTTP  
**Status**: Under investigation - may be related to server lifecycle management
**Workaround**: Use direct search method for reliable functionality

### Issue 3: Windows Path Issues
**Problem**: PowerShell path resolution issues
**Solution**: Use absolute paths in commands

## Dependencies

Key packages:
- `pydantic-ai`: AI agent framework
- `a2a-sdk`: Agent-to-Agent communication
- `mcp`: Model Context Protocol
- `google-generativeai`: Gemini API
- `arxiv`: ArXiv API access
- `fastmcp`: MCP server implementation
- `uvicorn`: ASGI server

## Configuration Files

### MCP Configuration (`a2a/agents/scientific_paper_agent/mcp_config.json`)
```json
{
  "arxiv_server": {
    "url": "http://localhost:8000/mcp",
    "description": "ArXiv paper search and retrieval server"
  }
}
```

### Agent Registry (`a2a/client/agent_registry.json`)
```json
{
  "scientific_paper_agent": "http://localhost:7000"
}
```

## Troubleshooting

1. **MCP Connection Failed**: Ensure ArXiv MCP server is running on port 8000
2. **Gemini API Error**: Check `GOOGLE_API_KEY` environment variable
3. **No Papers Found**: Verify MCP server is accessible and query is valid
4. **A2A Client Issues**: Check agent registry URLs match running servers

## Future Improvements

1. Resolve A2A server HTTP access issues
2. Add more MCP servers for different paper sources  
3. Implement paper analysis and summarization features
4. Add web interface for easier interaction
5. Support for other LLM providers