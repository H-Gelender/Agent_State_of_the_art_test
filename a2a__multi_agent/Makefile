.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install uv
	uv pip install -r requirements.txt

.PHONY: a2a-project
a2a-project:
	@echo "Create project structure"
	mkdir client
	mkdir server
	mkdir utilities
	mkdir agents
	cd agents && mkdir agent_mockdir && cd ..
	mkdir models
	mkdir app && cd app && mkdir cmd && cd ../..

	@echo "Creating __init__.py files..."
	echo. > server/__init__.py
	echo. > agents/__init__.py
	echo. > models/__init__.py
	echo. > app/cmd/__init__.py

	@echo creating structure models
	echo. > models/agent.py
	echo. > models/json_rpc.py
	echo. > models/request.py
	echo. > models/task.py

	@echo creating structure server
	echo. > server/server.py
	echo. > server/task_manager.py

	@echo creating structure agent
	echo. > agents/agent_mockdir/__main__.py
	echo. > agents/agent_mockdir/agent.py
	echo. > agents/agent_mockdir/task_manager.py

	@echo creating structure utilities
	echo. > utilities/agent_registry.json
	echo. > utilities/discovery.py

	@echo creating structure cmd
	echo. > app/cmd/cmd.py

.PHONY: run-greeting
run-greeting:
	@echo "Starting a2a server..."
	python agents/greeting_agent/agent.py

.PHONY: run-time
run-time:
	@echo "Starting a2a server..."
	python agents/time_agent/agent.py

.PHONY: run-client
run-client:
	@echo "Starting a2a client..."
	python client/client.py