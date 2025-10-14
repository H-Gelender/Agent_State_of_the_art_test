import asyncio
from crawl4ai import AsyncWebCrawler

# La fonction elle-même ne change pas
async def crawl_website(url: str) -> str:
    """
    Crawl un site web et retourne son contenu en Markdown.

    Args:
        url: L'URL du site à crawler.

    Returns:
        Le contenu de la page en format Markdown.
    """
    print(f"Crawling du site : {url}...")
    try:
        # Initialise le crawler asynchrone
        async with AsyncWebCrawler() as crawler:
            # Exécute le crawl sur l'URL spécifiée
            result = await crawler.arun(url=url)
            
            # Retourne le contenu en Markdown
            if result and result.markdown:
                print("Crawl réussi.")
                return result.markdown
            else:
                print("Le crawl n'a retourné aucun contenu.")
                return "Erreur : Le crawl n'a retourné aucun contenu."
    except Exception as e:
        print(f"Une erreur est survenue lors du crawl : {e}")
        return f"Erreur lors du crawl de {url}: {e}"

# La fonction de test ne change pas non plus
async def test_crawl():
    # Vous pouvez changer cette URL pour tester avec d'autres sites
    target_url = "https://www.legifrance.gouv.fr/"
    markdown_content = await crawl_website(target_url)
    
    print("\n--- Contenu Markdown  ---")
    print(markdown_content)
    print("-------------------------------------------------")

# --- LA CORRECTION EST ICI ---
if __name__ == "__main__":
    print("Test de la fonction crawl_website...")
    asyncio.run(test_crawl())