from azure.cosmos import CosmosClient, exceptions
from openai import AzureOpenAI
from math import sqrt
from typing import Dict, List
import json


# ===================================================
# Cosmos DB Client
# ===================================================
class CosmosDBClient:
    """Handles Cosmos DB operations."""

    def __init__(self, cosmos_account_uri: str, cosmos_account_key: str,
                 cosmos_database_name: str, cosmos_container_name: str):
        self.client = CosmosClient(cosmos_account_uri, credential=cosmos_account_key)
        self.database = self.client.get_database_client(cosmos_database_name)
        self.container = self.database.get_container_client(cosmos_container_name)

    def read_all_items(self) -> List[Dict]:
        """Read all items from the container."""
        try:
            return list(self.container.read_all_items())
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Cosmos DB read error: {e}")

    def upsert_item(self, item: Dict) -> None:
        """Upsert item into the container."""
        try:
            self.container.upsert_item(item)
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Cosmos DB upsert error: {e}")


# ===================================================
# Azure OpenAI Client
# ===================================================
class AzureOpenAIClient:
    """Handles Azure OpenAI embeddings."""

    def __init__(self, api_key: str, endpoint: str, api_version: str, embedding_model: str):
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


# ===================================================
# Utility: Cosine Similarity
# ===================================================
def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sqrt(sum(a * a for a in v1))
    norm2 = sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0


# ===================================================
# AI + Cosmos Orchestrator
# ===================================================
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
