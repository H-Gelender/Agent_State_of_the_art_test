.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install                    Install dependencies"
	@echo ""
	@echo "A2A Wrapper (Scientific Agent):"
	@echo "  make run-a2a-scientific-agent   Run A2A wrapper locally"
	@echo "  make test-a2a-scientific-agent  Test A2A wrapper"
	@echo "  make build-docker-a2a-scientist Build Docker image for A2A wrapper"
	@echo "  make run-docker-a2a-scientist   Run Docker container for A2A wrapper"
	@echo ""
	@echo "Agents:"
	@echo "  make client-search-agent        Run DuckDuckGo search agent"
	@echo "  make client-scientist-search    Run scientific search agent"
	@echo "  make build-docker-search        Build DuckDuckGo search Docker image"
	@echo "  make run-docker-search          Run DuckDuckGo search Docker container"
	@echo "  make build-docker-scientist-search   Build scientific search Docker image"
	@echo "  make run-docker-scientist-search     Run scientific search Docker container"

# ============================================
# SETUP
# ============================================

.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

# ============================================
# A2A WRAPPER (SCIENTIFIC AGENT)
# ============================================

.PHONY: a2a-project
a2a-project:
	@echo "Create project structure"
	mkdir client
	mkdir agents
	cd agents && mkdir agent_1 && cd ..

	@echo "Creating __init__.py files..."
	echo. > agents/agent_1/__init__.py

	@echo creating structure agents
	echo. > agents/agent_1/__main__.py
	echo. > agents/agent_1/agent.py
	echo. > agents/agent_1/agent_executor.py
	uv init

.PHONY: run-a2a-scientific-agent
run-a2a-scientific-agent:
	@echo "Starting A2A wrapper for Scientific Agent on http://localhost:8000..."
	python -m agents.scientific_agent.a2a_wrapper.main

.PHONY: test-a2a-scientific-agent
test-a2a-scientific-agent:
	@echo "Testing A2A wrapper for Scientific Agent..."
	@echo "Ensure the A2A server is running in another terminal"
	python -m agents.scientific_agent.a2a_wrapper.test_client

.PHONY: build-docker-a2a-scientist
build-docker-a2a-scientist:
	@echo "Building Docker image for A2A Scientist Agent..."
	docker build -t a2a-scientific-agent -f agents/scientific_agent/Dockerfile .

.PHONY: run-docker-a2a-scientist
run-docker-a2a-scientist:
	@echo "Running Docker container for A2A Scientist Agent on http://localhost:8000"
	@echo "Press Ctrl+C to stop the container."
	docker run --rm -it -p 8000:8000 --name a2a-scientific-container a2a-scientific-agent

# ============================================
# AGENTS - SEARCH
# ============================================

.PHONY: client-search-agent
client-search-agent:
	@echo "Starting DuckDuckGo search agent..."
	python -m agents.search_agent.client

.PHONY: build-docker-search
build-docker-search:
	@echo "Building Docker image for search agent..."
	docker build -t duckduck -f agents/search_agent/server/Dockerfile agents/search_agent/server

.PHONY: run-docker-search
run-docker-search:
	@echo "Running Docker container for search agent..."
	docker run --rm -it duckduck

# ============================================
# AGENTS - SCIENTIFIC SEARCH
# ============================================

.PHONY: client-scientist-search
client-scientist-search:
	@echo "Starting scientific search agent..."
	python -m agents.scientific_agent.client

.PHONY: build-docker-scientist-search
build-docker-scientist-search:
	@echo "Building Docker image for scientific search..."
	docker build -t scientist-search -f agents/scientific_agent/paper-search-mcp agents/scientific_agent/paper-search-mcp

.PHONY: run-docker-scientist-search
run-docker-scientist-search:
	@echo "Running Docker container for scientific search..."
	docker run --rm -it scientist-search