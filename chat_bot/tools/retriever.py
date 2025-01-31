import uuid

from qdrant_client import AsyncQdrantClient, models

from chat_bot.core.config import settings


class Qdrant:
    def __init__(
        self,
        cache_collection: str,
        main_collection: str,
        search_limit: int,
        cache_hit_score: float | int,
    ):
        """
        Initialize the Qdrant instance with provided collection names and settings.

        Args:
            cache_collection (str): Name of the cache collection in Qdrant.
            main_collection (str): Name of the main collection in Qdrant.
            search_limit (int): Maximum number of search results to return.
            cache_hit_score (float | int): Score threshold for cache hits.
        """
        # Assign collection names and configurations to instance variables
        self.cache_collection = cache_collection
        self.main_collection = main_collection
        self.search_limit = search_limit
        self.cache_hit_score = cache_hit_score

        # Initialize the AsyncQdrantClient with URL and API key if in cloud mode
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            https=settings.QDRANT_TLS,
            verify=False,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_CLOUD or settings.QDRANT_TLS else None,
        )

    async def search(
        self,
        collection_name: str,
        embedding: list[float],
        query_filter: list[tuple[str, str]],
        limit: int | None = 10,
        score_threshold: float | None = None,
    ) -> models.QueryResponse:
        """
        Search for similar documents in the specified Qdrant collection.

        Args:
            collection_name (str): Name of the collection to be searched.
            embedding (list[float]): Document embedding vector.
            query_filter (list[tuple[str, str]], optional): List of filter conditions to apply on the query results. Defaults to [].
            limit (int, optional): Maximum number of results to return. Defaults to 10.
            score_threshold (float | None, optional): Minimum score for a result to be returned. Defaults to None.

        Returns:
            models.QueryResponse: Query response containing the search results.
        """
        try:
            # Perform the search
            return await self.client.query_points(
                collection_name=collection_name,
                query=embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key=field, match=models.MatchValue(value=value)) for field, value in query_filter],
                ),
            )
        finally:
            # This empty finally block is here to indicate that the function call is wrapped in a try-finally block,
            # which is necessary to ensure that the Qdrant client is properly closed even if an exception occurs.
            pass

    async def upsert(
        self,
        collection: str,
        embedding: list[float],
        page_content: dict[str, str | dict[str, str | list[str]]],
    ) -> str:
        """
        Insert or update a document in the specified Qdrant collection.

        Args:
            collection (str): Name of the collection to be searched.
            embedding (list[float]): Document embedding vector.
            page_content (dict): Page content to be stored in the payload field of the document.

        Returns:
            str: Unique point ID of the inserted document.
        """
        point_id = uuid.uuid4().hex
        await self.client.upsert(
            collection_name=collection,
            points=[models.PointStruct(id=point_id, vector=embedding, payload=page_content)],
        )
        return point_id

    async def delete_point(self, point: str):
        """
        Delete a document from the cache collection in Qdrant.

        Args:
            point (str): Unique point ID of the document to be deleted.

        Returns:
            None
        """
        # Perform the delete operation on the specified point ID in the cache collection
        await self.client.delete(
            collection_name=self.cache_collection,
            points_selector=models.PointIdsList(points=[point]),
        )
