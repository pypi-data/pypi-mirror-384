import logging
import os
from pathlib import Path
from .server import serve
import asyncio
from .common.constant import ENV_BASE


def main() -> None:
    """Foxit Cloud API MCP server."""

    if ENV_BASE != "prod":
        base_dir = Path(__file__).resolve().parent
        log_path = base_dir / "temp" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch(exist_ok=True)

        logging.basicConfig(
            filename=str(log_path),
            level=logging.INFO,
        )
    asyncio.run(serve())
