from pathlib import Path

from qdrant_client import QdrantClient, models
from tenacity import retry, stop_after_attempt, wait_random

from chat_bot.core.config import settings


@retry(stop=stop_after_attempt(3), wait=wait_random(min=3, max=10))
def setup_knowledge_base() -> None:  # pragma: no cover
    """
    This function is called by the FastAPI Application as a startup event.
    It checks if the Qdrant collection exists, if not, it creates it.
    It also creates a payload index for the "resource_type" field in the collection.
    """
    vector_db = QdrantClient(
        https=True,
        url=settings.QDRANT_URL,
        port=None,
        api_key=settings.QDRANT_API_KEY if settings.QDRANT_CLOUD or settings.QDRANT_TLS else None,
        verify=False,
    )

    cache_collection = settings.QDRANT_CACHE_COLLECTION
    main_collection = settings.QDRANT_MAIN_COLLECTION

    # Check if the collection exists, if not, create it
    if not vector_db.collection_exists(collection_name=main_collection):
        # If the collection does not exist, try to recover it from a snapshot
        with open(Path(__file__).parent.parent / "db_snapshot/360inControl.snapshot", "rb") as snapshot:
            vector_db.http.snapshots_api.recover_from_uploaded_snapshot(collection_name=main_collection, snapshot=snapshot)
    if not vector_db.collection_exists(collection_name=cache_collection):
        # If the cache collection does not exist, create it
        vector_db.create_collection(
            collection_name=cache_collection,
            vectors_config=models.VectorParams(size=settings.EMBEDDING_DIMENSION, distance=models.Distance.COSINE),
        )
        # Create a payload index for the "resource_type" field in the collection
        vector_db.create_payload_index(
            collection_name=cache_collection,
            field_name="metadata.resource",
            field_type="keyword",
        )
