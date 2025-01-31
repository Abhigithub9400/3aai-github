import json
from typing import Any

import jwt
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from .config import settings

encryption_layer = Fernet(settings.JWT_PAYLOAD_ENCRY.encode())


class User(BaseModel):
    user_id: int
    user_name: str
    first_name: str
    last_name: str
    openai_key: str | None = Field(default_factory=lambda: settings.OPENAI_API_KEY)


def decode_jwt(
    encoded_token: str,
    allow_expired: bool = False,
) -> dict[str, Any]:
    """
    Decode an encoded JWT token into a dictionary of user details.

    Args:
        encoded_token (str): The encoded JWT token to decode.
        allow_expired (bool, optional): Whether to allow an expired token to be decoded. Defaults to False.

    Returns:
        dict[str, Any]: The decoded JWT token as a dictionary.
    """
    options = {}
    if allow_expired:  # pragma: no cover
        options["verify_exp"] = False

    # This call verifies the ext, iat, and nbf claims
    # This optionally verifies the exp and aud claims if enabled
    # See https://pyjwt.readthedocs.io/en/stable/usage.html#validation
    decoded_token: dict[str, Any] = jwt.decode(
        jwt=encoded_token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options=options,
    )
    ctx = decoded_token["user_details"]
    if settings.PAYLOAD_ENCRYPTION and isinstance(ctx, str):  # pragma: no cover
        # If payload encryption is enabled, decrypt the user details
        ctx_text = encryption_layer.decrypt(ctx.encode()).decode()
        ctx = json.loads(ctx_text)
    return ctx  # type: ignore[no-any-return]
