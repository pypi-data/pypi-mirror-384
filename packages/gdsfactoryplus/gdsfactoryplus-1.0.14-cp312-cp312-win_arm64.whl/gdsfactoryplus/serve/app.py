"""GDSFactory+ Server Application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from doweb.browser import (
    get_app as _get_app,  # type: ignore[reportAttributeAccessIssue]
)
from doweb.layout_server import (
    LayoutViewServerEndpoint,  # type: ignore[reportAttributeAccessIssue]
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse

from gdsfactoryplus import logger as log
from gdsfactoryplus import project, settings
from gdsfactoryplus.core import pdk
from gdsfactoryplus.core.communication import send_message
from gdsfactoryplus.models import (
    ReloadFactoriesMessage,
    ShutdownStatusMessage,
    StartupStatusMessage,
)

__all__ = ["app"]
logger = log.get_logger()

LayoutViewServerEndpoint.mode_dump = lambda _: ("ruler", "move instances")  # type: ignore[reportAttibuteAccessIssue]

THIS_DIR = Path(__file__).resolve().parent
GFP_DIR = THIS_DIR.parent

SETTINGS = settings.get_settings()
PDK: str = SETTINGS.pdk.name
_msg = f"Using PDK: {PDK}"
logger.info(_msg)
PROJECT_DIR = project.maybe_find_project_dir() or Path.cwd().resolve()
_msg = f"{PROJECT_DIR=}"
logger.info(_msg)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    try:
        # Startup
        send_message(
            StartupStatusMessage(
                message="Server startup successful. Just a moment please..."
            )
        )

        msg = f"Activating PDK: {PDK}"
        logger.info(msg)
        pdk.get_pdk()
        try:
            pdk.register_cells()
        except Exception as e:  # noqa: BLE001
            msg = f"Failed to register cells: {e}"
            logger.warning(msg)
            logger.warning("Creating new database due to previous error.")
            db_path = settings.get_db_path()
            db_path.unlink(missing_ok=True)
            pdk.register_cells()
        finally:
            send_message(ReloadFactoriesMessage())

        yield

    except Exception as e:
        msg = f"Server startup failed. {e}"
        logger.error(msg)  # noqa: TRY400
        send_message(
            ShutdownStatusMessage(message="Server startup failed. Please check logs...")
        )
        raise
    finally:
        # Shutdown - always send shutdown message
        send_message(
            ShutdownStatusMessage(message="Server killed. Please check logs...")
        )


app = cast("FastAPI", _get_app(fileslocation=str(PROJECT_DIR), editable=True))

# Modern way to set lifespan - replaces @app.on_event("startup")
app.router.lifespan_context = lifespan


def _needs_to_be_removed(path: str) -> bool:
    return path == "/" or path.startswith(("/file", "/gds"))


app.router.routes = [
    r for r in app.routes if not _needs_to_be_removed(getattr(r, "path", ""))
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def redirect() -> RedirectResponse:
    """Index should redirect to /code to make online workspaces open in code editor."""
    return RedirectResponse("/code/")


@app.get("/code")
def code() -> PlainTextResponse:
    """Dummy response which will be overwritten in online workspaces."""
    return PlainTextResponse("gfp server is running.")


def get_app() -> FastAPI:
    """Get the FastAPI app instance."""
    return app
