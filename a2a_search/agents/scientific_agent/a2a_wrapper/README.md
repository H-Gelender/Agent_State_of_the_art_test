# A2A Wrapper - Guide d'adaptation

Ce wrapper A2A est conçu pour être **générique et réutilisable** avec n'importe quel type d'agent.

## 📋 Vue d'ensemble

Le wrapper A2A expose un agent existant via le protocole A2A (Agent-to-Agent).

```
Ton Agent (LangGraph, ReAct, etc.)
         ↓
    Wrapper A2A
         ↓
   Serveur HTTP (FastAPI)
         ↓
    Clients A2A
```

---

## 🔧 Comment adapter le wrapper à ton agent

### **Étape 1 : Configurer les métadonnées**

Modifie [`config.py`](config.py ) :

```python
HOST = os.getenv("HOST", "0.0.0.0")           # Host d'écoute du serveur
PORT = int(os.getenv("PORT", "8000"))         # Port du serveur
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")  # Host public
MODEL = os.getenv("MODEL", "gemini-2.0-flash")      # Modèle LLM (optionnel)
```

---

### **Étape 2 : Créer l'interface de ton agent**

Ton agent doit exposer une classe `AgentWrapper` avec une méthode `ainvoke()` :

```python
# agents/ton_agent/client/agent.py

class AgentWrapper:
    """
    Interface standardisée pour tout type d'agent.
    """
    
    async def ainvoke(self, query: str) -> str:
        """
        Exécute l'agent de manière asynchrone.
        
        Args:
            query: Question ou instruction pour l'agent
            
        Returns:
            Réponse de l'agent sous forme de texte
        """
        # Implémente ta logique d'agent ici
        pass


async def create_and_initialize_agent() -> Tuple[AgentWrapper, AsyncExitStack]:
    """
    Initialise l'agent avec toutes ses dépendances.
    
    Returns:
        (agent_initialisé, context_manager)
    """
    # Initialise ton agent et retourne-le
    pass
```

---

### **Étape 3 : Adapter l'exécuteur d'agent**

Modifie [`agent_executor.py`](agent_executor.py ) pour convertir les requêtes A2A en appels à ton agent :

```python
# agents/ton_agent/a2a_wrapper/agent_executor.py

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from client.agent import AgentWrapper


class AgentExecutor(AgentExecutor):
    """
    Exécute les tâches de ton agent en respectant le contrat A2A.
    """
    
    def __init__(self, agent: AgentWrapper):
        self.agent = agent
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Exécute la requête A2A et envoie les événements.
        """
        try:
            # Récupère la question depuis la requête
            query = context.request.messages[0].content
            
            # Appelle ton agent
            response = await self.agent.ainvoke(query)
            
            # Envoie la réponse via A2A
            event_queue.put(
                new_agent_text_message(response)
            )
            
        except Exception as e:
            print(f"❌ Error: {e}")
            event_queue.put(
                new_agent_text_message(f"Error: {str(e)}")
            )
    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Annule l'exécution si nécessaire.
        """
        pass
```

---

### **Étape 4 : Mettre à jour la carte d'agent**

Modifie les métadonnées dans [`main.py`](main.py ) :

```python
# agents/ton_agent/a2a_wrapper/main.py

agent_card = {
    "name": "Ton Agent (A2A)",
    "description": "Description de ce que fait ton agent",
    "version": "1.0.0",
    "skills": [
        {
            "id": "skill_1",
            "name": "Skill Name",
            "description": "Description du skill",
            "tags": ["tag1", "tag2"],
            "examples": ["Exemple d'utilisation"]
        }
    ]
}
```

---

## 📁 Structure minimale requise

```
agents/
└── mon_agent/
    ├── client/
    │   ├── __init__.py
    │   ├── agent.py          # ← Ton agent (AgentWrapper + create_and_initialize_agent)
    │   └── __main__.py
    │
    ├── a2a_wrapper/
    │   ├── __init__.py
    │   ├── config.py         # ← Métadonnées du wrapper
    │   ├── agent_executor.py # ← Adapteur A2A
    │   ├── main.py           # ← Serveur A2A
    │   └── README.md         # ← Ce fichier
    │
    └── Dockerfile           # ← Pour le déploiement
```

---

## 🚀 Utilisation

### **Lancer le wrapper**

```bash
make run-docker-a2a-scientist
```

### **Tester le wrapper**

```bash
make test-a2a-scientific-agent
```

---

## 🔄 Checklist d'adaptation

- [ ] `config.py` : Adapter HOST, PORT, PUBLIC_HOST
- [ ] `client/agent.py` : Implémenter `AgentWrapper` avec méthode `ainvoke()`
- [ ] `client/agent.py` : Implémenter `create_and_initialize_agent()`
- [ ] `agent_executor.py` : Adapter pour convertir les requêtes A2A
- [ ] `main.py` : Mettre à jour la carte d'agent (name, description, skills)
- [ ] `Dockerfile` : S'assurer que le contexte de build est correct

---

## 💡 Conseils

1. **Keep it simple** : Le wrapper ne doit que convertir les requêtes A2A en appels à ton agent
2. **Séparation des concerns** : 
   - `client/` = Logique de ton agent
   - `a2a_wrapper/` = Exposition via A2A
3. **Réutilisabilité** : Ton agent ne doit pas connaître A2A
4. **Tests** : Teste ton agent indépendamment avant de l'intégrer au wrapper

---

## 📚 Ressources

- [A2A Protocol](https://a2a-protocol.ai/)
- [FastAPI + Uvicorn](https://fastapi.tiangolo.com/)
- [AsyncIO Python](https://docs.python.org/3/library/asyncio.html)