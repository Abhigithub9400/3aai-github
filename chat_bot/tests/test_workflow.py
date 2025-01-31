import base64
import pytest

from unittest import mock
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from chat_bot.tools.chat_pipeline import EventType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "re_generate,action_type,query",
    [
        (False, "audio_message", base64.b64encode("explain admin module configuration".encode()).decode()),
        (True, "audio_message", base64.b64encode("explain admin module configuration".encode()).decode()),
        (False, "text_message", "explain admin module configuration"),
        (True, "text_message", "explain admin module configuration")
    ]
)
@mock.patch("chat_bot.tools.retriever.AsyncQdrantClient.delete")
@mock.patch("chat_bot.tools.retriever.AsyncQdrantClient.upsert")
@mock.patch("chat_bot.tools.retriever.AsyncQdrantClient.query_points")
@mock.patch("chat_bot.tools.llm.OpenAIEmbeddings.aembed_query")
@mock.patch("chat_bot.tools.llm.AsyncOpenAI")
@mock.patch("chat_bot.tools.llm.ChatOpenAI.ainvoke")
@mock.patch("chat_bot.tools.llm.ChatOpenAI.astream")
async def test_websocket_with_jwt(
    openai_stream_mock: MagicMock,
    openai_ainvoke_mock: MagicMock,
    openai_whisper_mock: MagicMock,
    openai_embedding_mock: MagicMock,
    qdrant_query_points_mock: MagicMock,
    qdrant_query_upsert_mock: MagicMock,
    qdrant_query_delete_mock: MagicMock,
    re_generate: bool,
    action_type: str,
    query: str,
    client: TestClient,
    jwt_token: str
):
    """
    Test the WebSocket endpoint with a JWT token.

    Mocks the Qdrant and OpenAI libraries to mock the responses.
    """

    async def astream():
        """
        Mock the astream method to return a response.

        The astream method is used to retrieve the text from the audio message.
        """
        yield  "TEST-MOCK-RESPONSE"

    openai_stream_mock.return_value = astream()
    return_value = MagicMock(text="TEST-VOICE-TEXT-RESPONSE")
    create = AsyncMock(return_value=return_value)
    transcriptions = MagicMock(create=create)
    audio = MagicMock(transcriptions=transcriptions)
    openai_whisper_mock.return_value = MagicMock(audio=audio)
    openai_embedding_mock.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    openai_ainvoke_mock.return_value = """
        1. question 1?
        2. question 2?
        3. question 3?
    """
    qdrant_query_upsert_mock.return_value = True
    qdrant_query_delete_mock.return_value = True
    qdrant_query_points_mock.return_value = MagicMock(
        points=[
            MagicMock(
                id="739af4ef1f9f4c34a3b4fced617c92b2",
                payload={
                    "metadata": {
                        "page_number": 1,
                        "suggested_questions": ["question 1?", "question 2?", "question 3?"],
                        "document": "admin_guide",
                    },
                    "page_content": "MOCK_QDRANT_RESPONSE",
                    "llm_response": "MOCK_QDRANT_RESPONSE"
                }
            )
        ]
    )

    with client.websocket_connect(f"/ws?token={jwt_token}") as websocket:
        websocket.send_json({
            "type": action_type,
            "payload": {
                "data": query,
                "suggested_question": True,
                "response_language": "english",
                "re_generate": re_generate,
                "document": "admin_guide",
                "point_id": "739af4ef1f9f4c34a3b4fced617c92b2"
            }
        })
        while True:
            data = websocket.receive_json()
            assert data['type'] != EventType.EXCEPTION.value
            if data['type'] == EventType.TRANSACTION.value and data['payload']['data'] == 'chat_transaction_end':
                break

