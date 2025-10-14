# Scientific Paper Agent with MCP Configuration

This agent searches for scientific papers using configurable MCP (Model Context Protocol) servers and extracts structured information.

## MCP Configuration

The agent now supports flexible MCP server configuration through JSON files, similar to the scientist_agent implementation.

### Default Configuration

The agent looks for `mcp_config.json` in the same directory. Default configuration:

```json
{
  "mcpServers": {
    "arxiv_server": {
      "url": "http://localhost:8000/mcp",
      "name": "ArXiv Search Server",
      "description": "Server for searching scientific papers on arXiv"
    }
  }
}
```

### Multiple Server Configuration

You can configure multiple MCP servers (see `mcp_config_multi.json`):

```json
{
  "mcpServers": {
    "arxiv_server": {
      "url": "http://localhost:8000/mcp",
      "name": "ArXiv Search Server",
      "description": "Server for searching scientific papers on arXiv"
    },
    "semantic_scholar_server": {
      "url": "http://localhost:8001/mcp",
      "name": "Semantic Scholar Server", 
      "description": "Server for searching papers via Semantic Scholar API"
    },
    "pubmed_server": {
      "url": "http://localhost:8002/mcp",
      "name": "PubMed Server",
      "description": "Server for searching medical papers on PubMed"
    }
  }
}
```

## Usage

### Starting the ArXiv MCP Server

```bash
# From the scientific_parser directory
cd c:\Users\henry\Desktop\workdir\Agent_State_of_the_art_test\scientific_parser
uv run -m a2a.agents.scientific_paper_agent arxiv-server

# Or use the batch script
.\start_arxiv_server.bat
```

### Running the Paper Parser Agent

```bash
# Start A2A server with default config
uv run -m a2a.agents.scientific_paper_agent

# Start A2A server with custom config
uv run -m a2a.agents.scientific_paper_agent server --config mcp_config_multi.json

# Direct search mode
uv run -m a2a.agents.scientific_paper_agent search "machine learning" 10

# Show help
uv run -m a2a.agents.scientific_paper_agent help
```

### Environment Variables

- `GOOGLE_API_KEY`: **Required** - Your Gemini API key for AI processing
- `PAPER_OUTPUT_DIR`: Directory to save parsed papers (default: `./parsed_papers`)
- `MCP_CONFIG`: Path to MCP configuration file (default: `mcp_config.json`)

### Setup

1. **Set up your Gemini API key** in the `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

### Example Workflow

1. **Start the ArXiv MCP Server:**
   ```bash
   uv run -m a2a.agents.scientific_paper_agent arxiv-server
   ```

2. **In another terminal, search for papers:**
   ```bash
   uv run -m a2a.agents.scientific_paper_agent search "quantum computing" 5
   ```

3. **Or start the A2A server:**
   ```bash
   uv run -m a2a.agents.scientific_paper_agent
   ```

## Key Features

- **Flexible MCP Configuration**: Load multiple MCP servers from JSON config
- **Dynamic Server Loading**: Reload configuration at runtime
- **Fallback Handling**: Graceful fallback to default configuration if config file is missing
- **Environment Variable Support**: Override config file path via `MCP_CONFIG`
- **Multiple Output Formats**: A2A server mode and direct search mode
- **Structured Output**: Extracts titles, authors, topics, overviews, and usefulness ratings

## Architecture Changes

The implementation now follows the same pattern as `scientist_agent`:

1. **Configuration Loading**: `load_mcp_servers()` function reads from `mcp_config.json`
2. **Dynamic Agent Creation**: Agents are created with current MCP server list
3. **Flexible Toolsets**: Support for multiple MCP servers as toolsets
4. **Runtime Configuration**: Can specify different config files at startup

This makes the agent more modular and easier to extend with additional MCP servers for different paper sources.