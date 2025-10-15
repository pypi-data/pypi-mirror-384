from azure.cosmos import CosmosClient, exceptions
from typing import Dict, List



class CosmosDBClient:
    """Handles Cosmos DB operations."""

    def __init__(self, cosmos_account_uri: str, cosmos_account_key: str, cosmos_database_name: str, cosmos_container_name: str):
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
