import fastapi

from .ws import websocket_router


def apply_routers(app: fastapi.FastAPI):
    """

    @param app:
    """
    router = fastapi.APIRouter()

    router.include_router(router=websocket_router)

    app.include_router(router)
