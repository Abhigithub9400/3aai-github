import base64

from cache import AsyncTTL
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import AsyncOpenAI


class LLM:
    def __init__(self, model: str, openai_key: str, temperature: float | int = 0):
        """
        Initialize the LLM model.

        This constructor sets up the language model for generating conversational responses
        and handles audio transcriptions.

        Args:
            model (str): The name of the LLM model.
            openai_key (str): The API key for accessing OpenAI services.
            temperature (float | int, optional): The temperature of the model, which controls
                the randomness of the output. Defaults to 0.
        """
        # Initialize the chat model for conversational AI
        self.chat_model = ChatOpenAI(model=model, temperature=temperature, openai_api_key=openai_key)  # type: ignore

        # Set up the transcription service for converting audio to text
        self.transcriptions = AsyncOpenAI(api_key=openai_key).audio.transcriptions  # type: ignore

    async def audio_transcription(self, audio_b64_text: str):
        """
        Transcribes audio data from a base64 encoded string using the Whisper model.

        Args:
            audio_b64_text (str): The base64 encoded audio data.

        Returns:
            str: The transcribed text from the audio.

        """
        # Decode the base64 encoded audio data
        decoded_audio = base64.b64decode(audio_b64_text.encode())

        # Create a transcription request using the Whisper model
        response = await self.transcriptions.create(model="whisper-1", file=("mmm.wav", decoded_audio))

        # Return the transcribed text
        return response.text


class EmbeddingModel:
    embedding_client: OpenAIEmbeddings

    def __init__(self, model: str, openai_key: str):
        """
        Initialize the Embedding Model.

        This constructor sets up the OpenAI Embeddings for converting text queries into embeddings.

        Args:
            model (str): The name of the Embedding Model.
            openai_key (str): The API key for accessing OpenAI services.
        """
        # Initialize the OpenAI Embeddings model
        self.embedding_model = OpenAIEmbeddings(model=model, api_key=openai_key)

        # Assign the initialized embedding model to the class-level attribute
        EmbeddingModel.embedding_client = self.embedding_model

    @staticmethod
    @AsyncTTL(time_to_live=3600, maxsize=1024)  # Cache the result for 1 hour, with a max size of 1GB
    async def aembed_query(query: str) -> list[float]:
        """
        Asynchronously generate embeddings for a given query.

        This method uses the OpenAI embedding model to convert a text query into a list of floats
        that represent the embeddings. The results are cached to improve performance for repeated queries.

        Args:
            query (str): The text query to embed.

        Returns:
            list[float]: A list of floats representing the query's embeddings.
        """
        # Generate embeddings for the query using the embedding client
        embeddings_list: list[float] = await EmbeddingModel.embedding_client.aembed_query(query)

        return embeddings_list
