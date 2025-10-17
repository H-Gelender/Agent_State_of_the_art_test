#!/usr/bin/env python
"""
query_agent.py (Version de Débogage de la Réponse)

Interroge un agent A2A et affiche la structure complète de la réponse.
"""
import asyncio
import logging
from uuid import uuid4
import json

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, Role, TextPart, Part, Message

# --- Configuration ---
AGENT_BASE_URL = 'http://localhost:8000'
QUESTION_TO_AGENT = "Find recent papers about attention mechanisms in Large Language Models from arXiv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Fonction principale du client."""
    
    logger.info(f"🚀 Lancement du client pour interroger l'agent à {AGENT_BASE_URL}")

    # Increase timeout to 120 seconds for AI processing
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=AGENT_BASE_URL,
        )
        agent_card = await resolver.get_agent_card(relative_card_path='/.well-known/agent-card.json')
        logger.info("✅ Carte d'agent récupérée avec succès !")

        client = A2AClient(
            httpx_client=httpx_client, 
            agent_card=agent_card
        )
        logger.info("✅ Client A2A initialisé.")

        logger.info(f"❓ Envoi de la question : '{QUESTION_TO_AGENT}'")
        send_message_payload = {
            'message': {
                'role': 'user', 'parts': [{'kind': 'text', 'text': QUESTION_TO_AGENT}], 'messageId': uuid4().hex
            }
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        response = await client.send_message(request)

        logger.info("🎉 Réponse reçue de l'agent !")
        
        # --- DÉBOGAGE : AFFICHER LA STRUCTURE DE LA RÉPONSE ---
        print("\n=================== DÉBUT DE LA RÉPONSE BRUTE ===================\n")
        try:
            # La meilleure façon de voir le contenu d'un objet Pydantic est model_dump_json
            response_dict_str = response.model_dump_json(indent=2, exclude_none=True)
            print("Type de l'objet response:", type(response))
            print("Contenu de la réponse (JSON) :")
            print(response_dict_str)
        except AttributeError:
            # Si ce n'est pas un objet Pydantic, on l'affiche directement
            print("La réponse n'est pas un objet Pydantic standard. Affichage direct :")
            print(response)
        print("\n==================== FIN DE LA RÉPONSE BRUTE ====================\n")
        
        # --- Affichage de la réponse interprétée (le code qui fonctionne déjà) ---
        if isinstance(response, Message) and response.parts:
            for part in response.parts:
                text_to_display = ""
                if isinstance(part, TextPart):
                    text_to_display = part.text
                elif isinstance(part, Part) and isinstance(part.root, TextPart):
                    text_to_display = part.root.text
                
                if text_to_display:
                    print("\n--- Réponse finale de l'agent (interprétée) ---\n")
                    print(text_to_display)
                    print("\n-----------------------------------------------\n")

if __name__ == '__main__':
    asyncio.run(main())