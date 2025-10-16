#!/usr/bin/env python
"""
mcp_utils.py

Bibliothèque de fonctions utilitaires réutilisables pour les clients MCP.
Ces fonctions peuvent être utilisées dans n'importe quel projet MCP.

Fonctionnalités:
  - Lecture de configuration JSON
  - Connexion aux serveurs MCP
  - Chargement des outils MCP
  - Gestion des sessions MCP
"""

import os
import sys
import json
from pathlib import Path

from typing import Dict, Any, List, Tuple
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

def read_config_json() -> dict:
    """
    Lit le fichier de configuration JSON des serveurs MCP.

    Cherche 'mcp_config.json' dans le même répertoire que mcp_utils.py

    Returns:
        dict: Configuration JSON parsée avec les définitions des serveurs MCP
        
    Raises:
        SystemExit: Si le fichier ne peut pas être lu
    """
    # Chercher dans le même répertoire que mcp_utils.py
    utils_dir = Path(__file__).parent.resolve()
    config_path = utils_dir / "mcp_config.json"
    
    if not config_path.is_file():
        print(f"❌ Config file not found at: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, "r") as f:
            print(f"✅ Loaded config: {config_path}")
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read config file: {e}")
        sys.exit(1)


def get_mcp_servers_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait la configuration des serveurs MCP du fichier de configuration.
    
    Args:
        config: Configuration complète chargée depuis le JSON
        
    Returns:
        dict: Dictionnaire des serveurs MCP configurés
    """
    mcp_servers = config.get("mcpServers", {})
    if not mcp_servers:
        print("⚠️  No MCP servers found in the configuration.")
    return mcp_servers


async def connect_to_mcp_server(
    server_name: str,
    server_info: Dict[str, Any],
    exit_stack: AsyncExitStack
) -> Tuple[ClientSession, List[Any]]:
    """
    Se connecte à un serveur MCP et charge ses outils.
    
    Args:
        server_name: Nom du serveur MCP
        server_info: Informations de configuration du serveur (command, args)
        exit_stack: AsyncExitStack pour gérer la durée de vie de la connexion
        
    Returns:
        Tuple[ClientSession, List]: Session MCP et liste des outils chargés
        
    Raises:
        Exception: Si la connexion au serveur échoue
    """
    print(f"\n🔗 Connecting to MCP Server: {server_name}...")
    
    server_params = StdioServerParameters(
        command=server_info["command"],
        args=server_info["args"]
    )
    
    # Établir la connexion au serveur
    read, write = await exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    session = await exit_stack.enter_async_context(
        ClientSession(read, write)
    )
    await session.initialize()
    
    # Charger les outils depuis le serveur
    tools = await load_mcp_tools(session)
    
    print(f"✅ {len(tools)} tools loaded from {server_name}.")
    
    return session, tools


async def connect_to_all_mcp_servers(
    mcp_servers: Dict[str, Any],
    exit_stack: AsyncExitStack,
    verbose: bool = True
) -> List[Any]:
    """
    Se connecte à tous les serveurs MCP définis et charge tous leurs outils.
    
    Args:
        mcp_servers: Dictionnaire des configurations des serveurs MCP
        exit_stack: AsyncExitStack pour gérer toutes les connexions
        verbose: Si True, affiche les détails de chaque outil chargé
        
    Returns:
        List: Liste de tous les outils chargés depuis tous les serveurs
    """
    all_tools = []
    
    for server_name, server_info in mcp_servers.items():
        try:
            session, tools = await connect_to_mcp_server(
                server_name,
                server_info,
                exit_stack
            )
            
            if verbose:
                for tool in tools:
                    print(f"🔧 Loaded tool: {tool.name}")
            
            all_tools.extend(tools)
            
        except Exception as e:
            print(f"❌ Failed to connect to server {server_name}: {e}")
            continue
    
    return all_tools


class CustomEncoder(json.JSONEncoder):
    """
    Encodeur JSON personnalisé pour gérer les objets non-sérialisables de LangChain.
    Si l'objet a un attribut 'content', il est sérialisé en conséquence.
    """
    def default(self, o):
        if hasattr(o, "content"):
            return {"type": o.__class__.__name__, "content": o.content}
        return super().default(o)


def format_agent_response(response: Any) -> str:
    """
    Formate la réponse d'un agent en JSON lisible.
    
    Args:
        response: Réponse brute de l'agent
        
    Returns:
        str: Réponse formatée en JSON
    """
    try:
        return json.dumps(response, indent=2, cls=CustomEncoder)
    except Exception:
        return str(response)


def load_environment_variable(var_name: str, required: bool = True) -> str:
    """
    Charge une variable d'environnement.
    
    Args:
        var_name: Nom de la variable d'environnement
        required: Si True, quitte le programme si la variable n'existe pas
        
    Returns:
        str: Valeur de la variable d'environnement
        
    Raises:
        SystemExit: Si la variable est requise et n'existe pas
    """
    value = os.getenv(var_name, "")
    if required and not value:
        print(f"❌ {var_name} not found in environment variables.")
        sys.exit(1)
    return value