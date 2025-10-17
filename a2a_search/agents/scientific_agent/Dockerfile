# Étape 1: Base Python
FROM python:3.12-slim

# Installer Docker CLI pour pouvoir exécuter docker exec
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

# Étape 2: Répertoire de travail
WORKDIR /app

# Copier TOUT le projet dans /app
COPY . /app/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port
EXPOSE 8000

# Définir le PYTHONPATH pour que Python trouve les modules
ENV PYTHONPATH=/app

# Lancer le wrapper A2A
CMD ["python", "-m", "agents.scientific_agent.a2a_wrapper.main"]