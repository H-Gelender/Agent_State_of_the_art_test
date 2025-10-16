"""
Configuration du wrapper A2A.
"""

import os

# Configuration du serveur
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")

# Modèle LLM
MODEL = os.getenv("MODEL", "gemini-2.0-flash")

