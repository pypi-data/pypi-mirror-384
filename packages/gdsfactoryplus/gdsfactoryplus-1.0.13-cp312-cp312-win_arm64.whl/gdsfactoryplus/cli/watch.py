"""GDSFactory+ File Watcher."""

from __future__ import annotations

import os
from typing import Annotated

import typer

from .app import app

__all__ = ["watch"]


@app.command()
def watch(path: Annotated[str, typer.Argument()] = "", server_url: str = "") -> None:
    """Watch a folder for changes.

    Args:
        path: Path to the folder.
        server_url: URL of the GDSFactory+ server.
    """
    import gdsfactoryplus.core.watch as watcher

    if not server_url:
        server_url = os.environ.get("SERVER_URL", "")

    if not server_url:
        host = os.environ.get("GFP_KWEB_HOST", "localhost")
        if os.environ.get("GFP_KWEB_HTTPS", "false") == "true":
            server_url = f"https://{host}"
        else:
            server_url = f"http://{host}:8787"

    if not path:
        from gdsfactoryplus import settings

        path = str(settings.get_pics_dir().resolve())
    return watcher.watch(path, server_url)
