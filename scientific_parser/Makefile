.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

.PHONY: run-scientist
run-scientist:
	@echo "Starting Scientist Agent..."
	uv run -m agents.scientist_agent

.PHONY: run
run:
	@echo "Starting main application..."
	uv run -m agents.orchestrator_agent chat "Find me the latest papers on large language models"

.PHONY: run-server
run-server:
	@echo "Starting MCP server..."
	uv run -m agents.scientist_agent.mcp_server

.PHONY: run-client
run-client:
	@echo "Starting MCP client..."
	uv run -m agents.scientist_agent.mcp_client