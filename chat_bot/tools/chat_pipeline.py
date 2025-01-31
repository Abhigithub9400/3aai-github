from enum import Enum

from fastapi import WebSocket
from langchain_core.output_parsers import NumberedListOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client.conversions import common_types as types

from .llm import LLM, EmbeddingModel
from .prompts import CHAT_PROMPT, SUGGESTED_QUESTION_PROMPT
from .retriever import Qdrant


class EventType(str, Enum):
    STREAMING = "streaming_event"
    SUGGESTED_QUESTIONS = "suggested_questions"
    MESSAGE_THREAD = "message_thread"
    EXCEPTION = "exception"
    TRANSACTION = "chat_transaction"
    AUDIO_TO_TEXT = "audio_to_text"


class PipeLine:
    def __init__(
        self,
        llm_model: LLM,
        embedding_model: EmbeddingModel,
        vector_store: Qdrant,
        websocket: WebSocket,
        resource: str,
        response_language: str,
        chat_message_id: str | None = None,
        audio_data: str = "",
        text_data: str = "",
        suggested_question: bool = False,
        skip_cache: bool = False,
    ):
        """
        Initialize the pipeline.

        Args:
            llm_model: The LLM model to use.
            embedding_model: The EmbeddingModel to use.
            vector_store: The Qdrant vector store.
            websocket: The WebSocket to use.
            resource: The type of resource.
            chat_message_id: The ID of the chat message.
            audio_data: The base64 encoded audio data.
            text_data: The plain text data.
            suggested_question: Whether to generate a suggested question.
            skip_cache: Whether to skip the cache.
        """
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.chat_message_id = chat_message_id
        self.websocket = websocket
        self.resource: str = resource
        self.embeddings: list[float] = []
        self.similar_documents: types.QueryResponse = types.QueryResponse(points=[])
        self.cache_response: types.QueryResponse = types.QueryResponse(points=[])
        self.llm_response: str = ""
        self.b64_text: str = audio_data
        self.plain_text: str = text_data
        self.response_language: str = response_language
        self.suggested_question: bool = suggested_question
        self.suggested_question_list: list[str] = []
        self.skip_cache: bool = skip_cache

    async def emit(self, event_type: str, payload: dict[str, str | list[str]]) -> None:
        await self.websocket.send_json({"type": event_type, "payload": payload})

    async def to_vector(self, query: str) -> "PipeLine":
        """
        Convert the query to a vector using the embedding model.

        Args:
            query: The query to convert.

        Returns:
            The modified pipeline.
        """
        self.embeddings = await self.embedding_model.aembed_query(query)
        return self

    async def _query_points(
        self,
        collection: str,
        limit: int | None = None,
        score_threshold: float | None = None,
    ):
        """
        Query the vector store for points within the specified collection.

        Args:
            collection: The name of the collection to query.
            limit: The maximum number of points to return. If None, all points are returned.
            score_threshold: The minimum score a point must have to be included in the results. If None, all points are returned.

        Returns:
            A QueryResponse object containing the results of the query.
        """
        return await self.vector_store.search(
            collection_name=collection,
            embedding=self.embeddings,
            query_filter=[("metadata.resource", self.resource)],
            limit=limit,
            score_threshold=score_threshold,
        )

    async def get_from_cache(self) -> "PipeLine":
        """
        Query the cache for points within the specified collection.

        If the skip_cache flag is set to True, the cache is not queried.
        The score_threshold parameter is set to the cache_hit_score.
        Only one point is returned.

        Returns:
            The modified pipeline.
        """
        query_response = await self._query_points(
            collection=self.vector_store.cache_collection,
            score_threshold=self.vector_store.cache_hit_score,
            limit=1,
        )
        self.cache_response = query_response if query_response.points else None
        return self

    async def audio_to_text(self, audio_base64_text) -> "PipeLine":
        """
        Transcribe an audio file to text and send the text to the client.

        Args:
            audio_base64_text (str): The base64 encoded audio data.

        Returns:
            The modified pipeline.
        """

        # Transcribe the audio to text
        self.plain_text = await self.llm_model.audio_transcription(audio_base64_text)

        # Send the transcribed text to the client
        await self.emit(event_type=EventType.AUDIO_TO_TEXT, payload={"data": self.plain_text})

        return self

    async def similarity_search(self) -> "PipeLine":
        """
        Perform a similarity search on the main collection.

        The points returned from this query are the most similar to the query
        embeddings and are used to generate the suggested questions.

        Returns:
            The modified pipeline.
        """
        query_response = await self._query_points(collection=self.vector_store.main_collection)
        self.similar_documents = query_response if query_response.points else None
        return self

    async def store_llm_response(self) -> None:
        """
        Store the LLM response in the cache collection.

        Store the LLM response in the cache collection along with the suggested questions.
        The cache collection is used to store the LLM response and the suggested questions
        so that they can be retrieved quickly in case the user asks for the same thing
        again.
        """
        # Store the LLM response in the cache collection
        point_id = await self.vector_store.upsert(
            collection=self.vector_store.cache_collection,
            embedding=self.embeddings,
            page_content={
                # Store the LLM response
                "llm_response": self.llm_response,
                # Message dependencies
                "metadata": {
                    # Store the suggested questions
                    "suggested_questions": self.suggested_question_list,
                    "resource": self.resource,
                },
            },
        )
        # Send the message thread to the client
        await self.emit(event_type=EventType.MESSAGE_THREAD, payload={"data": point_id})

    async def execute(self, query: str):
        """
        Execute the query by generating a response using the language model
        and send the response as a stream of chunks to the client.

        Args:
            query (str): The user's query to execute.

        Returns:
            None
        """
        response = ""
        # Create a processing chain for the language model
        chain = ChatPromptTemplate.from_template(CHAT_PROMPT) | self.llm_model.chat_model | StrOutputParser()

        # Prepare the context by formatting each document with page numbers
        context = "\n".join(
            f"[PageNumber-{rec.payload['metadata']['page_number']}]" + rec.payload["page_content"] for rec in self.similar_documents.points
        )

        # Stream the response in chunks
        payload = {"QUERY": query, "CONTEXT": context, "RESPONSE_LANGUAGE": self.response_language}
        async for chunk in chain.astream(payload):
            response += chunk
            # Send each chunk to the client
            await self.emit(event_type=EventType.STREAMING, payload={"data": chunk})

        # Store the complete response
        self.llm_response = response

    async def generate_questions(self, query: str, response: str) -> None:
        """
        Generate a list of suggested questions based on the user's query and the response.

        Args:
            query (str): The user's query.
            response (str): The response to the user's query.

        Returns:
            None
        """
        # Create a processing chain for the language model
        chain = ChatPromptTemplate.from_template(SUGGESTED_QUESTION_PROMPT) | self.llm_model.chat_model | NumberedListOutputParser()

        # Generate the suggested questions
        payload = {"QUESTION": query, "ANSWER": response, "RESPONSE_LANGUAGE": self.response_language}
        suggested_questions: list[str] = await chain.ainvoke(payload)

        # Store the list of suggested questions
        self.suggested_question_list = suggested_questions

        # Send the suggested questions to the client
        await self.emit(
            event_type=EventType.SUGGESTED_QUESTIONS,
            payload={"data": suggested_questions},
        )

    async def process_cache_response(self) -> None:
        """
        Process the cached response.

        If there is a cache hit, this function will send the cached response
        to the client and send the suggested questions.
        """
        # Get the cached response
        llm_response = self.cache_response.points[0].payload["llm_response"]
        # Get the suggested questions
        questions = self.cache_response.points[0].payload["metadata"]["suggested_questions"]
        # Get the point ID
        point_id = self.cache_response.points[0].id

        # Send the cached response
        await self.emit(event_type=EventType.STREAMING, payload={"data": llm_response}) if llm_response else None
        # Send the end of the stream
        await self.emit(event_type=EventType.STREAMING, payload={"data": "stream_end"})
        # Send the suggested questions
        await self.emit(event_type=EventType.SUGGESTED_QUESTIONS, payload={"data": questions}) if questions else None
        # Send the message thread
        await self.emit(event_type=EventType.MESSAGE_THREAD, payload={"data": point_id}) if point_id else None

    async def process_user_query(self) -> None:
        """
        Process the user's query by performing a similarity search in the vector store,
        generating a response using the language model, and generating suggested questions.

        If there is no similar context found, it will send an exception event.
        """
        # Perform a similarity search in the vector store
        await self.similarity_search()
        # Generate a response using the language model
        if self.similar_documents:  # pragma: no cover
            # Generate a response using the language model
            await self.execute(query=self.plain_text)
        else:  # pragma: no cover
            # If there is no similar context found, send an exception event
            await self.emit(event_type=EventType.EXCEPTION, payload={"data": "No similar context found"})
            return
        # Send a stop message
        await self.emit(event_type=EventType.STREAMING, payload={"data": "stream_end"})
        # Generate suggested questions
        if self.suggested_question and self.llm_response:  # pragma: no cover
            # Generate suggested questions
            await self.generate_questions(query=self.plain_text, response=self.llm_response)
        # Store the response in the vector store
        await self.store_llm_response() if self.llm_response else None

    async def run(self) -> None:
        """
        Run the entire pipeline.

        The pipeline consists of the following steps:

        1. Transcribe the audio to text if there is no plain text.
        2. Convert the text to a vector using the embedding model.
        3. Search in the vector store for similar documents.
        4. Generate a response using the language model.
        5. Store the response in the vector store.

        If there is a cache hit, it will send the cached response to the client.
        Otherwise, it will generate a response using the language model and send it to the client.

        If there is an exception, it will send an exception event to the client.
        """
        try:
            # Send the transaction start event
            await self.emit(event_type=EventType.TRANSACTION, payload={"data": "chat_transaction_start"})

            # If there is no plain text, transcribe the audio to text
            if not self.plain_text:
                if not self.b64_text:  # pragma: no cover
                    # Send an exception event if there is no audio data
                    await self.emit(
                        event_type=EventType.EXCEPTION,
                        payload={"data": "No audio data found"},
                    )
                # Transcribe the audio to text
                await self.audio_to_text(self.b64_text)

            # Convert the text to a vector using the embedding model
            await self.to_vector(query=self.plain_text)

            # Send the stream start event
            await self.emit(event_type=EventType.STREAMING, payload={"data": "stream_start"})

            # Check if there is a cache hit
            if not self.skip_cache:
                # Get the cached response
                await self.get_from_cache()

            if self.cache_response and self.cache_response.points:
                # Process the cached response
                await self.process_cache_response()
            else:
                # Process the user query
                await self.process_user_query()

            # If there is a chat message ID and the cache is not skipped, delete the point
            if self.chat_message_id and self.skip_cache:  # pragma: no cover
                await self.vector_store.delete_point(self.chat_message_id)
        except Exception as e:  # pragma: no cover
            # Send an exception event if there is an exception
            await self.emit(event_type=EventType.EXCEPTION, payload={"data": f"Something went wrong:: {e.__class__.__name__}: {e}."})
        finally:
            # Send the transaction end event
            await self.emit(event_type=EventType.TRANSACTION, payload={"data": "chat_transaction_end"})
