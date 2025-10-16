.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

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

# 	@echo creating structure client
# 	echo. > client/client.py
# 	echo. > client/orchestrator.py
# 	echo. > client/__main__.py
# 	@echo creating uv structure
	uv init

.PHONY: client-search-agent
client-search-agent:
	@echo "Starting duckduck go search client..."
	python -m agents.search_agent.client

.PHONY: client-scientist-search
client-scientist-search:
	@echo "Starting scientist search client..."
	python -m agents.scientific_agent.client

.PHONY: build-docker-search
build-docker-search:
	@echo "Building Docker image..."
	docker build -t duckduck -f agents/search_agent/server/Dockerfile agents/search_agent/server

.PHONY: run-docker-search
run-docker-search:
	@echo "Running Docker container..."
	docker run --rm -it duckduck

.PHONY: build-docker-scientist-search
build-docker-scientist-search:
	@echo "Building Docker image..."
	docker build -t scientist-search -f agents/scientific_agent/paper-search-mcp/Dockerfile agents/scientific_agent/paper-search-mcp

.PHONY: run-docker-scientist-search
run-docker-scientist-search:
	@echo "Running Docker container..."
	docker run --rm -it scientist-search