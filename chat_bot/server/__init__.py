import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chat_bot.api import apply_routers
from chat_bot.core.audit_log import setup_logger
from chat_bot.core.config import get_config
from chat_bot.core.middleware import make_middleware

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


MARKDOWN_TEXT = """

## Introduction
Welcome to the documentation for our advanced Chatbot! This Chatbot is designed to provide seamless interactions by utilizing cutting-edge technologies like natural language processing, vector stores, and language models. It transcribes audio, generates meaningful text-based insights, and offers a wide range of functional capabilities to enhance user engagement and support.

## Features

- **24/7 Availability:** Our Chatbot is always on, ready to assist users at any time of day.
- **Audio Transcription:** Supports audio to text transcription for seamless conversion and interaction.
- **Vector Store Integration:** Utilizes vector stores for efficient information retrieval and response generation.
- **Dynamic Response Generation:** Leverages language models to provide accurate and context-aware responses.
- **Cache Optimization:** Implements a smart caching mechanism to provide quick responses and minimize computational demands.

# Chatbot Workflow Steps

<img src="/static/workflow.png" width="800" height="1500" alt="360InControl, Chatbot Workflow">

## Step Description
| Step                                      | Explanation                                                                                                               |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Start                                     | The initial step where the workflow begins. It signifies the beginning of a transaction or user interaction.              |
| Emit "chat_transaction_start" Event       | Sends an event to signal the start of a chat transaction. This is used to initiate session logging or tracking.            |
| Check if Plain Text is Available          | Determines if there is plain text input from the user. If available, the flow proceeds with text processing.               |
| Check if Audio Data is Available          | If no plain text is available, checks for audio data. If audio is available, it will be transcribed to text.               |
| Emit "No Audio Data Found" Event          | If neither plain text nor audio is available, this event is triggered to handle exceptions or notify users of missing input.|
| Transcribe Audio to Text                  | Converts audio input to text using speech recognition technology.                                                          |
| Convert Text to Vector                    | Transforms the text input into a vector representation for more efficient searching and processing in the vector store.    |
| Check if Cache Response is Available      | Queries a cache to see if a previous response is available for the current input, which speeds up processing.              |
| Emit Cached Response                      | If a cache response is available, it emits the cached data to provide a faster response without further computation.       |
| Search in Vector Store                    | If no cached response is available, searches in the vector store to find relevant data or context for the user's query.    |
| Execute Language Model Response           | If relevant context is found, uses a language model to generate an intelligent and context-aware response for the user.    |
| Emit "stream_end" Event                   | Signifies the end of a data stream or processing step, preparing to conclude the current transaction or session.           |
| Generate Suggested Questions              | Creates follow-up or clarifying questions based on the current conversation context to keep the user engaged.              |
| Store LLM Response                        | The generated response is stored in the vector store for future reference or cache optimization.                          |
| Delete Chat Message from Vector Store     | Cleans up the vector store by deleting outdated or irrelevant chat messages if caching is not needed for them.            |
| Emit "chat_transaction_end" Event         | Sends an event to indicate the end of the chat transaction, closing the workflow and marking the completion of the session.|
| End                                       | The final step, marking the completion of this workflow instance.                                                         |

"""


def create_app() -> FastAPI:
    """Create a FastAPI application from the given configuration."""
    config = get_config(os.getenv("ENVIRONMENT", "local"))

    _app = FastAPI(
        title="360InControl",
        description=MARKDOWN_TEXT,
        version="1.0.0",
        docs_url="/",
        middleware=make_middleware(),
    )
    _app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")
    logger.info(" [✔] Application initialized")
    setup_logger(config)
    logger.info(" [✔] Logger initialized")
    apply_routers(_app)
    logger.info(" [✔] Routers applied")

    return _app


app = create_app()
