import logging

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from chat_bot.core.config import settings
from chat_bot.tools import LLM, EmbeddingModel, PipeLine, Qdrant

websocket_router = APIRouter(tags=["Socket"])

logger = logging.getLogger("chatbot")


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    This endpoint is for establishing a WebSocket connection.
    The client will send audio or text messages to this endpoint.
    The messages will be processed by an LLM and the response will be sent back to the client.
    """
    logger.info("[New Connection] User: %s", websocket.user.user_name)
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            resource = data["payload"].get("document", False)

            chat_message_id = data["payload"].get("point_id", None)
            skip_cache = data["payload"].get("re_generate", False)
            suggested_question = data["payload"].get("suggested_question", False)

            action_type = data["type"]
            voice_text = data["payload"]["data"] if action_type == "audio_message" else ""
            text_msg = data["payload"]["data"] if action_type == "text_message" else ""
            response_language = data["payload"].get("response_language", "english")

            try:
                # Process the message and send the response back to the client
                openai_key = websocket.user.openai_key
                await PipeLine(
                    llm_model=LLM(model=settings.OPENAI_BASE_MODEL, temperature=0, openai_key=openai_key),
                    embedding_model=EmbeddingModel(model=settings.OPENAI_EMBEDDING_BASE_MODEL, openai_key=openai_key),
                    vector_store=Qdrant(
                        cache_collection=settings.QDRANT_CACHE_COLLECTION,
                        main_collection=settings.QDRANT_MAIN_COLLECTION,
                        search_limit=settings.QDRANT_SEARCH_LIMIT,
                        cache_hit_score=settings.QDRANT_CACHE_SCORE,
                    ),
                    chat_message_id=chat_message_id,
                    websocket=websocket,
                    audio_data=voice_text,
                    text_data=text_msg,
                    suggested_question=suggested_question,
                    skip_cache=skip_cache,
                    resource=resource,
                    response_language=response_language,
                ).run()
            except Exception:  # pragma: no cover
                # If an exception occurs, continue to the next iteration
                continue
    except WebSocketDisconnect:  # pragma: no cover
        # If the client disconnects, log a warning message
        logger.warning("[Disconnected] User: %s", websocket.user.user_name)
