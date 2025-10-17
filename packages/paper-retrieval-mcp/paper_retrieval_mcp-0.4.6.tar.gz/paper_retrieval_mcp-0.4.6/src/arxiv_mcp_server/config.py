"""Configuration settings for the arXiv MCP server."""

import sys
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass


class Settings(BaseSettings):
    """Server configuration settings."""

    APP_NAME: str = "arxiv-mcp-server"
    APP_VERSION: str = "0.3.0"
    MAX_RESULTS: int = 50
    BATCH_SIZE: int = 20
    REQUEST_TIMEOUT: int = 60
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    model_config = SettingsConfigDict(extra="allow")

    @property
    def STORAGE_PATH(self) -> Path:
        """Get the resolved storage path and ensure it exists.

        Returns:
            Path: The absolute storage path.
        """
        # Prefer command-line argument: --storage-path <path>
        arg_path: Path | None = None
        try:
            if "--storage-path" in sys.argv:
                idx = sys.argv.index("--storage-path")
                if idx + 1 < len(sys.argv):
                    arg_path = Path(sys.argv[idx + 1])
            elif "--storage_path" in sys.argv:  # alias
                idx = sys.argv.index("--storage_path")
                if idx + 1 < len(sys.argv):
                    arg_path = Path(sys.argv[idx + 1])
        except Exception:
            arg_path = None

        # Default location under user home
        default_path = Path.home() / ".arxiv-mcp-server" / "papers"
        path = arg_path if arg_path else default_path
        path = path.resolve()

        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        return path
