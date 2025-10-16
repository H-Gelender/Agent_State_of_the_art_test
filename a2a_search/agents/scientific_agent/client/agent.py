#!/usr/bin/env python
"""
agents.py

Ce fichier contient toute la logique de l'agent et du LLM.
Modifiez ce fichier pour changer le modèle, la température, ou le type d'agent.
"""

import os
from typing import List, Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent


class AgentWrapper:
    """
    Wrapper qui unifie l'interface de différents types d'agents.
    Permet de changer d'agent sans modifier __main__.py
    """
    
    def __init__(self, agent, agent_type: str = "react"):
        """
        Args:
            agent: L'agent sous-jacent (React, simple LLM, etc.)
            agent_type: Type d'agent ("react" ou "simple")
        """
        self.agent = agent
        self.agent_type = agent_type
    
    async def ainvoke(self, query: str) -> str:
        """
        Invoque l'agent et retourne une réponse sous forme de string.
        Gère automatiquement les différences entre les types d'agents.
        
        Args:
            query: La question de l'utilisateur
            
        Returns:
            str: La réponse de l'agent
        """
        try:
            if self.agent_type == "react":
                # Format pour React agent
                response = await self.agent.ainvoke({"messages": [("user", query)]})
                if "messages" in response:
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        return last_message.content
                    return str(last_message)
                return str(response)
            
            elif self.agent_type == "simple":
                # Format pour LLM simple
                response = await self.agent.ainvoke(query)
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
            
            else:
                # Fallback générique
                response = await self.agent.ainvoke(query)
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
                
        except Exception as e:
            return f"❌ Error in agent invocation: {e}"


def get_agent(tools: List[Any]) -> AgentWrapper:
    """
    Crée et configure l'agent avec le LLM de votre choix.
    
    Modifiez cette fonction pour:
    - Changer le modèle (model="gemini-2.0-flash")
    - Ajuster la température
    - Modifier les paramètres du LLM
    - Utiliser un autre LLM (OpenAI, Anthropic, etc.)
    - Changer le type d'agent (React, simple, custom)
    
    Args:
        tools: Liste des outils MCP chargés
        
    Returns:
        AgentWrapper: Agent configuré et prêt à être utilisé
    """
    # Configuration du LLM - MODIFIEZ ICI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ GOOGLE_API_KEY not found in environment variables.")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # Changez le modèle ici
        temperature=0,              # Ajustez la température ici
        max_retries=2,              # Nombre de tentatives en cas d'erreur
        google_api_key=api_key
    )
    
    # CHOISISSEZ VOTRE TYPE D'AGENT ICI:
    
    # Option 1: Agent React (recommandé pour utiliser les outils)
    if tools:
        agent = create_react_agent(llm, tools)
        agent_type = "react"
        print(f"\n✅ React Agent created with {len(tools)} tools.")
    else:
        # Option 2: LLM simple (si pas d'outils)
        agent = llm
        agent_type = "simple"
        print(f"\n✅ Simple LLM created (no tools).")
    
    # Option 3: Si vous voulez forcer un LLM simple même avec des outils:
    # agent = llm.bind_tools(tools) if tools else llm
    # agent_type = "simple"
    # print(f"\n✅ Simple LLM with tools created.")
    
    print(f"   Model: gemini-2.0-flash")
    print(f"   Temperature: 0")
    
    return AgentWrapper(agent, agent_type)