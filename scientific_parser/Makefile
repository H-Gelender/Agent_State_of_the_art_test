.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

.PHONY: run-mcp-server
run-mcp-server:
	@echo "Starting ArXiv MCP Server on port 8000..."
	uv run python a2a/agents/scientific_paper_agent/arxiv_server.py

.PHONY: run-agent
run-agent:
	@echo "Starting Scientific Paper A2A Agent on port 7000..."
	uv run python agents/orchestrator_agent/__main___a2a_sdk.py

.PHONY: client
client:
	@echo "Starting A2A client (interactive)..."
	uv run python a2a/client/client.py

.PHONY: search
search:
	@echo "Running direct search (usage: make search QUERY='your query' RESULTS=3)..."
	@if [ -z "$(QUERY)" ]; then \
		echo "Error: Please provide a query"; \
		echo "Usage: make search QUERY='machine learning' RESULTS=5"; \
		exit 1; \
	else \
		uv run python a2a/agents/scientific_paper_agent/agent.py "$(QUERY)" $(or $(RESULTS),3); \
	fi

.PHONY: demo
demo:
	@echo "Running interactive demo..."
	uv run python demo.py $(QUERY) $(RESULTS)

.PHONY: help
help:
	@echo "🔬 Scientific Paper Agent - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install all dependencies"
	@echo ""
	@echo "Run System (3 terminals required):"
	@echo "  make run-mcp-server   - Start ArXiv MCP Server (port 8000)"
	@echo "  make run-agent        - Start Scientific Paper Agent (port 7000)"
	@echo "  make client           - Start A2A client (interactive)"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make search QUERY='ai' RESULTS=5  - Direct search (no A2A)"
	@echo "  make demo             - Interactive demo"
	@echo ""
	@echo "Example Workflow:"
	@echo "  Terminal 1: make run-mcp-server"
	@echo "  Terminal 2: make run-agent"
	@echo "  Terminal 3: make client"
	@echo ""
	@echo "For more details: See README.md"

.PHONY: clean
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"