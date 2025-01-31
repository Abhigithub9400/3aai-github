import os
import sys
from pathlib import Path

import click
import uvicorn

sys.path.extend([str(Path(__file__).parent.parent)])  # don't change the import order


@click.command()
@click.option(
    "--environment",
    type=click.Choice(["local", "production"], case_sensitive=False),
    default="local",
    help="""
        Environment to run the application in. Can be one of:
        - local: development environment
        - production: production environment
    """,
)
@click.option(
    "--debug",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Enable debug mode, which will make the application run slower.",
)
def main(environment: str, debug: bool):  # pragma: no cover
    """
    Run the ChatBot application.

    This function sets up the environment variables from the command line arguments,
    sets up the knowledge base and runs the application with uvicorn.

    :param environment: The environment to run the application in.
    :type environment: str
    :param debug: Whether to run the application in debug mode.
    :type debug: bool
    """
    # Set environment variables
    os.environ["ENVIRONMENT"] = environment
    os.environ["DEBUG"] = str(debug)

    # Get configuration from environment variables
    from chat_bot.core.config import get_config  # noqa:E402
    from chat_bot.core.db_setup import setup_knowledge_base  # noqa:E402

    config = get_config(environment)
    setup_knowledge_base()
    # Run application
    uvicorn.run(
        app="chat_bot.server:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.RELOAD,
        workers=config.WORKERS,
        log_level=config.APP_LOG_LEVEL,
        forwarded_allow_ips=config.FORWARDED_ALLOW_IPS,
        ws_max_queue=config.WS_MAX_QUEUE,
        loop="uvloop" if os.name == "posix" else "asyncio",
        server_header=False,  # Security fix
    )


if __name__ == "__main__":
    main()
