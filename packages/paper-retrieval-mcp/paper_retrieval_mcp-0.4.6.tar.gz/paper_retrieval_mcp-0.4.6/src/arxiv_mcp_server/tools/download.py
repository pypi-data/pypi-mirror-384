"""Download functionality for the arXiv MCP server."""

import arxiv
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import mcp.types as types
from ..config import Settings
import pymupdf4llm
import logging

logger = logging.getLogger("arxiv-mcp-server")
settings = Settings()

# Global dictionary to track conversion status
conversion_statuses: Dict[str, Any] = {}


@dataclass
class ConversionStatus:
    """Track the status of a PDF to Markdown conversion."""

    paper_id: str
    status: str  # 'downloading', 'converting', 'success', 'error'
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


download_tool = types.Tool(
    name="download_paper",
    description="Download a paper and create a resource for it",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper to download",
            },
            "check_status": {
                "type": "boolean",
                "description": "If true, only check conversion status without downloading",
                "default": False,
            },
            "ouputPath": {
                "type": "string",
                "description": "Optional target directory to store files; no fallback if provided",
            },
            "outputPath": {
                "type": "string",
                "description": "Alias of ouputPath for convenience",
            },
        },
        "required": ["paper_id"],
    },
)


def get_paper_path(
    paper_id: str,
    suffix: str = ".md",
    base_dir: Optional[Path] = None,
    allow_fallback: bool = True,
) -> Path:
    """Get the absolute file path for a paper with given suffix.

    When base_dir is provided, use it strictly without fallback.
    """
    storage_path = Path(base_dir) if base_dir else Path(settings.STORAGE_PATH)

    try:
        storage_path.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        if allow_fallback:
            import tempfile
            fallback_path = Path(tempfile.gettempdir()) / "arxiv-mcp-server" / "papers"
            fallback_path.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Storage path {storage_path} is not creatable, using fallback: {fallback_path}")
            storage_path = fallback_path
        else:
            raise Exception(f"Storage path {storage_path} is not creatable: {e}")

    # Test if the directory is writable
    test_file = storage_path / ".test_write"
    try:
        test_file.touch()
        test_file.unlink()
    except (OSError, PermissionError) as e:
        if allow_fallback:
            import tempfile
            fallback_path = Path(tempfile.gettempdir()) / "arxiv-mcp-server" / "papers"
            fallback_path.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Storage path {storage_path} is not writable, using fallback: {fallback_path}")
            storage_path = fallback_path
        else:
            raise Exception(f"Storage path {storage_path} is not writable: {e}")

    return storage_path / f"{paper_id}{suffix}"


def convert_pdf_to_markdown(paper_id: str, pdf_path: Path, md_path: Path) -> None:
    """Convert PDF to Markdown in a separate thread."""
    try:
        logger.info(f"Starting conversion for {paper_id}")
        markdown = pymupdf4llm.to_markdown(pdf_path, show_progress=False)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        status = conversion_statuses.get(paper_id)
        if status:
            status.status = "success"
            status.completed_at = datetime.now()

        logger.info(f"Conversion completed for {paper_id}")

    except Exception as e:
        logger.error(f"Conversion failed for {paper_id}: {str(e)}")
        status = conversion_statuses.get(paper_id)
        if status:
            status.status = "error"
            status.completed_at = datetime.now()
            status.error = str(e)


async def handle_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper download and conversion requests."""
    try:
        paper_id = arguments["paper_id"]
        check_status = arguments.get("check_status", False)
        # Accept both keys; prefer explicit ouputPath
        provided_path = arguments.get("ouputPath") or arguments.get("outputPath")
        base_dir = Path(provided_path) if provided_path else None
        allow_fallback = base_dir is None

        md_path = get_paper_path(paper_id, ".md", base_dir=base_dir, allow_fallback=allow_fallback)
        pdf_path = get_paper_path(paper_id, ".pdf", base_dir=base_dir, allow_fallback=allow_fallback)

        # If only checking status
        if check_status:
            status = conversion_statuses.get(paper_id)
            if not status:
                if md_path.exists():
                    return [
                        types.TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "status": "success",
                                    "message": "Paper is ready",
                                    "resource_uri": f"file://{md_path}",
                                    "md_uri": f"file://{md_path}",
                                    "pdf_uri": (f"file://{pdf_path}" if pdf_path.exists() else None),
                                }
                            ),
                        )
                    ]
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "unknown",
                                "message": "No download or conversion in progress",
                            }
                        ),
                    )
                ]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": status.status,
                            "started_at": status.started_at.isoformat(),
                            "completed_at": (
                                status.completed_at.isoformat() if status.completed_at else None
                            ),
                            "error": status.error,
                            "message": f"Paper conversion {status.status}",
                            "md_uri": (f"file://{md_path}" if md_path.exists() else None),
                            "pdf_uri": (f"file://{pdf_path}" if pdf_path.exists() else None),
                        }
                    ),
                )
            ]

        # Check if paper is already converted
        if md_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "message": "Paper already available",
                            "resource_uri": f"file://{md_path}",
                            "md_uri": f"file://{md_path}",
                            "pdf_uri": (f"file://{pdf_path}" if pdf_path.exists() else None),
                        }
                    ),
                )
            ]

        # Check if already in progress
        if paper_id in conversion_statuses:
            status = conversion_statuses[paper_id]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": status.status,
                            "message": f"Paper conversion {status.status}",
                            "started_at": status.started_at.isoformat(),
                        }
                    ),
                )
            ]

        # Start new download and conversion
        client = arxiv.Client()

        # Initialize status
        conversion_statuses[paper_id] = ConversionStatus(
            paper_id=paper_id, status="downloading", started_at=datetime.now()
        )

        # Download PDF
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        paper.download_pdf(dirpath=pdf_path.parent, filename=pdf_path.name)

        # Update status and start conversion
        status = conversion_statuses[paper_id]
        status.status = "converting"

        # Start conversion in thread
        asyncio.create_task(
            asyncio.to_thread(convert_pdf_to_markdown, paper_id, pdf_path, md_path)
        )

        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "converting",
                        "message": "Paper downloaded, conversion started",
                        "started_at": status.started_at.isoformat(),
                        "pdf_uri": f"file://{pdf_path}",
                    }
                ),
            )
        ]

    except StopIteration:
        error_msg = f"Paper {paper_id} not found on arXiv"
        logger.error(error_msg)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": error_msg,
                }),
            )
        ]
    except Exception as e:
        error_msg = f"Error downloading paper: {str(e)}"
        logger.error(error_msg)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": error_msg,
                }),
            )
        ]
