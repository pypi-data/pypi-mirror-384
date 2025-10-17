"""Configuration settings for the arXiv MCP server."""

import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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
        # 默认使用 .mcp 目录下的 arxiv-papers 子目录
        path = Path.cwd() / ".mcp" / "arxiv-papers"
        path = path.resolve()
        
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot create storage directory {path}: {e}")
            # Use a fallback directory in user home
            path = Path.home() / ".mcp" / "arxiv-papers"
            path = path.resolve()
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using fallback storage directory: {path}")
            except (OSError, PermissionError) as e2:
                logger.warning(f"Cannot create fallback directory {path}: {e2}")
                # Final fallback to temp directory
                import tempfile
                path = Path(tempfile.gettempdir()) / "arxiv-mcp-server" / "papers"
                path = path.resolve()
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using temp storage directory: {path}")
        
        return path
