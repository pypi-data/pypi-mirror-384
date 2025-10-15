import json
from math import sqrt
from typing import List
from .openai_client import AzureOpenAIClient
from .cosmos_client import CosmosDBClient


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sqrt(sum(a * a for a in v1))
    norm2 = sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0


class AICosmosOrchestrator:
    """Combines Azure OpenAI + Cosmos DB for semantic search."""

    def __init__(self, cosmos_client: CosmosDBClient, openai_client: AzureOpenAIClient):
        """
        Clients are passed explicitly — no hardcoding or env vars.
        """
        self.cosmos_client = cosmos_client
        self.openai_client = openai_client

    def ensure_embeddings(self):
        """Generate embeddings for Cosmos items that don't have them."""
        items = self.cosmos_client.read_all_items()
        for item in items:
            if "vector" not in item or not item["vector"]:
                text = f"{item.get('subject','')} {item.get('body','')} {item.get('from','')}"
                item["vector"] = self.openai_client.get_embedding(text)
                self.cosmos_client.upsert_item(item)

    def semantic_search(self, query: str, top_k: int = 3, threshold: float = 0.5) -> str:
        """Perform semantic search using embeddings."""
        self.ensure_embeddings()
        query_vector = self.openai_client.get_embedding(query)

        items = self.cosmos_client.read_all_items()
        scored = []
        for item in items:
            if "vector" in item:
                sim = cosine_similarity(query_vector, item["vector"])
                if sim >= threshold:
                    scored.append((sim, item))

        top_results = sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]
        results = [
            {
                "similarity_score": round(score, 4),
                "message_id": doc.get("message_id", "N/A"),
                "subject": doc.get("subject", "N/A"),
                "body": doc.get("body", "N/A"),
                "from": doc.get("from", "N/A"),
            }
            for score, doc in top_results
        ]

        return json.dumps(results, indent=4)
