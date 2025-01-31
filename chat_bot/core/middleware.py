import logging

from fastapi.middleware import Middleware
from jwt.exceptions import PyJWTError
from starlette.authentication import AuthenticationBackend
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection

from .security import User, decode_jwt

logger = logging.getLogger("chatbot")


class AuthBackend(AuthenticationBackend):
    def __init__(self, white_list_apis: list[str] | None = None):
        self.white_list_apis = white_list_apis or []

    @staticmethod
    def get_token(conn: HTTPConnection) -> str | None:
        """
        Get the token from the query parameters.

        @param conn: The HTTP connection to get the token from.
        @return: The token from the query parameters.
        """
        # Get the token from the query parameters
        credentials: str = conn.query_params.get("token", None)
        return credentials

    async def authenticate(self, conn: HTTPConnection) -> tuple[bool, User] | None:
        """
        This function validates the JWT token in the Authorization header.

        If the token is valid, it will return a tuple containing a boolean indicating
        whether the authentication was successful and a User object containing the user's
        information. If the token is invalid, it will return None.

        @param conn: The HTTP connection to authenticate.
        @return: A tuple containing a boolean indicating whether the authentication was
                 successful and a User object containing the user's information.
        """
        # Check if the endpoint is in the whitelist
        if conn.scope["path"] in self.white_list_apis:  # pragma: no cover
            return None

        # Get the token from the Authorization header
        token = self.get_token(conn)

        # Check if the token is None
        if not token:  # pragma: no cover
            # Raise an exception if the token is None
            raise RuntimeError("Invalid Token")

        try:
            # Decode the token and get the user's information
            payload = decode_jwt(token, allow_expired=True)
            current_user = User(**payload)
        except PyJWTError as e:  # pragma: no cover
            # Raise an exception if the token validation fails
            raise RuntimeError("Token validation failed") from e

        # Return a tuple containing a boolean indicating whether the authentication was
        # successful and a User object containing the user's information
        return True, current_user


def make_middleware() -> list[Middleware]:
    """
    This function returns a list of middleware that should be registered with the FastAPI app.
    The middleware is responsible for authenticating the user and setting the user's context.
    """
    # Create a list of middleware
    middleware = [
        Middleware(
            # Use the AuthenticationMiddleware with the AuthBackend
            AuthenticationMiddleware,
            backend=AuthBackend(white_list_apis=["/", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/static/workflow.png"]),
        ),
    ]
    # Return the list of middleware
    return middleware
