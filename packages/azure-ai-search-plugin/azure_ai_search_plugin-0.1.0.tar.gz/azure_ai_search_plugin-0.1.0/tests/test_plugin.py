import asyncio
import os
from azure_ai_search_plugin import AzureSearchPlugin  # ✅ from your package

async def test_plugin():
    # Initialize the AzureSearchPlugin using environment variables
    plugin = AzureSearchPlugin(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", "https://your-endpoint.search.windows.net"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY", "your-api-key"),
        index_name=os.getenv("AZURE_SEARCH_RULES_INDEX", "your-index-name"),
        semantic_config=os.getenv("AZURE_SEARCH_RULES_SEMANTIC_CONFIG", "your-semantic-config")
    )

    # Example search query
    query = "give me the email must include Procurement.Indirects@tesa.com"
    
    # Call the search method (handle async if needed)
    result = plugin.search_top(query)

    print("Search Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_plugin())
