from openai import AzureOpenAI
from typing import List


class AzureOpenAIClient:
    """Handles Azure OpenAI embeddings."""

    def __init__(self, api_key: str, endpoint: str,api_version:str, embedding_model: str):
        """
        Parameters are passed explicitly.
        """
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.model = embedding_model

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding for given text."""
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding
