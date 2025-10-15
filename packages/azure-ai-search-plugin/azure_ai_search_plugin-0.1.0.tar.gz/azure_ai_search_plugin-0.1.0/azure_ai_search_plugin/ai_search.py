# azure_ai_search_plugin/ai_search.py

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from semantic_kernel.functions import kernel_function


class AzureSearchPlugin:
    """
    A reusable Azure Cognitive Search plugin for Semantic Kernel or standalone usage.
    Supports semantic or keyword-based search over any configured index.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        semantic_config: str = None,
    ):
        """
        Initialize the search client using passed parameters.

        Args:
            endpoint (str): Azure Search endpoint URL.
            api_key (str): Azure Search API key.
            index_name (str): Name of the search index.
            semantic_config (str, optional): Semantic configuration name.
        """
        if not all([endpoint, api_key, index_name]):
            raise ValueError("Missing required Azure Search configuration values.")

        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
        self.semantic_config = semantic_config

    @kernel_function(
        description="Performs a semantic or keyword search and returns the top matching document."
    )
    def search_top(self, query: str, top_k: int = 5):
        """
        Search the Azure Cognitive Search index and return the best matching document.

        Args:
            query (str): The text query to search for.
            top_k (int): Number of top results to retrieve (default=5).

        Returns:
            dict or None: The best matching document with ID, name, description, and confidence score.
        """
        try:
            if self.semantic_config:
                results = self.client.search(
                    search_text=query,
                    query_type="semantic",
                    semantic_configuration_name=self.semantic_config,
                    top=top_k,
                )
            else:
                results = self.client.search(search_text=query, top=top_k)

            results_list = [
                {
                    "id": doc.get("id", "unknown"),
                    "name": doc.get("name", "unknown"),
                    "description": doc.get("description", "unknown"),
                    "_confidence": float(doc.get("@search.score", 0.0))
                }
                for doc in results
            ]

            if results_list:
                return max(results_list, key=lambda x: x["_confidence"])
        except Exception as e:
            print(f"AzureSearchPlugin error: {e}")

        return None
