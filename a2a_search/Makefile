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
	
.PHONY: run-langgraph
run-langgraph:
	@echo "Starting langgraph server..."
	uv run python -m agents.search_agent

.PHONY: run-client
run-client:
	@echo "Starting a2a client..."
	python agents/search_agent/client/agent_executor.py

.PHONY: client
client:
	@echo "Starting a2a client..."
	python -m agents.search_agent.client

.PHONY: build-docker
build-docker:
	@echo "Building Docker image..."
	docker build -t duckduck -f agents/search_agent/server/Dockerfile agents/search_agent/server

.PHONY: run-docker
run-docker:
	@echo "Running Docker container..."
	docker run --rm -it duckduck