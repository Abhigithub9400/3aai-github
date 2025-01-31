import jwt
import pytest

from datetime import UTC, datetime, timedelta
from fastapi.testclient import TestClient
from chat_bot.core.config import settings
from chat_bot.server import app


@pytest.fixture(autouse=True)
def client():
    """
    Fixture to create a TestClient instance for the app. This fixture is autouse=True, meaning it will be executed before every test.

    Returns:
        TestClient: The TestClient instance for the app.
    """
    return TestClient(app)

@pytest.fixture(autouse=True)
def jwt_token():
    """
    Generate a JWT token to be used in the tests. The token is generated with the
    user details and an expiration time of 1 hour from now.

    Returns:
        str: The JWT token.
    """

    # Generate payload with user details and expiration time
    payload = {
        "user_details": {
            "user_id": 123,
            "user_name": "alimon",
            "first_name": "Alimon",
            "last_name": "Khader",
            "openai_key": "sk-1234567890"
        },
        "exp": datetime.now(UTC) + timedelta(hours=1)
    }

    # Generate JWT token using the payload and secret key
    access_token = jwt.encode(
        payload=payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return access_token