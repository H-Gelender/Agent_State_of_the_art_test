.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

	@echo "setting up crawler4ai."
	crawl4ai-setup
	crawl4ai-doctor


.PHONY: a2a-project
a2a-project:
	@echo "Create project structure"
	mkdir client
	mkdir agents
	cd agents && mkdir agent_mockdir && cd ..

	@echo "Creating __init__.py files..."
	echo. > client/__init__.py
	echo. > agents/agent_mockdir/__init__.py

	@echo creating structure agents
	echo. > agents/agent_mockdir/__main__.py
	echo. > agents/agent_mockdir/agent.py
	echo. > agents/agent_mockdir/agent_executor.py

	@echo creating structure client
	echo. > client/client.py
	echo. > client/orchestrator.py
	echo. > client/__main__.py
	@echo creating uv structure
	uv init
	
.PHONY: run-langgraph
run-langgraph:
	@echo "Starting a2a server..."
	uv sync
	uv run -m agents.langgraph_agent

.PHONY: run-pydantic
run-pydantic:
	@echo "Starting a2a server..."
	uv run -m agents.pydantic_agent

.PHONY: run-client
run-client:
	@echo "Starting a2a client..."
	uv run -m client.client
