#!/usr/bin/env python3
"""
Wrapper pour connecter au MCP server paper-search via Docker network.
Ce script remplace la commande docker run par une connexion au conteneur existant.
"""

import sys
import subprocess

def main():
    """Execute docker exec to connect to the running MCP server."""
    try:
        # Se connecter au conteneur paper-search-mcp en cours d'exécution
        result = subprocess.run(
            [
                "docker", "exec", "-i",
                "paper-search-mcp",
                "python", "-m", "paper_search_mcp.server"
            ],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error connecting to MCP server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
