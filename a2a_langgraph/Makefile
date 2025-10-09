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
	python client/client.py

.PHONY: run-orchestrator
run-orchestrator:
	@echo "Starting a2a orchestrator..."
	python client/orchestrator.py

.PHONY: run-simple-orchestrator
run-simple-orchestrator:
	@echo "Starting simple orchestrator (registry-based)..."
	python client/simple_orchestrator.py

.PHONY: run-clean-orchestrator
run-clean-orchestrator:
	@echo "Starting clean orchestrator (minimal code)..."
	python client/orchestrator_clean.py