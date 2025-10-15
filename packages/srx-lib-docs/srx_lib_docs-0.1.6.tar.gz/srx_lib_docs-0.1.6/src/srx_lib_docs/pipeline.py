from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional, Protocol

import aiofiles
import httpx

from .convert import extract_text


class DocumentHandler(Protocol):
    name: str
    supported_mimetypes: List[str]

    async def convert(self, file_path: str) -> str: ...


@dataclass
class SimpleTextHandler:
    name: str
    supported_mimetypes: List[str]

    async def convert(self, file_path: str) -> str:
        # Fallback to plain text extraction based on file extension
        with open(file_path, "rb") as f:
            data = f.read()
        return extract_text(data, None)


@dataclass
class DocumentPipeline:
    handlers: List[DocumentHandler] = field(default_factory=list)
    temp_dir: str = "/tmp"

    def register(self, handler: DocumentHandler) -> None:
        self.handlers.append(handler)

    def _find_handler(self, mimetype: Optional[str]) -> Optional[DocumentHandler]:
        if not mimetype:
            return None
        for h in self.handlers:
            if mimetype in getattr(h, "supported_mimetypes", []):
                return h
        return None

    async def download_file(self, url: str) -> str:
        os.makedirs(self.temp_dir, exist_ok=True)
        tf = tempfile.NamedTemporaryFile(delete=False, dir=self.temp_dir, suffix=".bin")
        path = tf.name
        tf.close()
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        await f.write(chunk)
        return path

    async def process_url(
        self, url: str, mimetype: Optional[str] = None, metadata: Optional[dict] = None
    ) -> dict:
        temp_path = None
        try:
            temp_path = await self.download_file(url)
            handler = self._find_handler(mimetype)
            if handler is None:
                # Use simple text extractor if no specific handler is registered
                handler = SimpleTextHandler(
                    name="simple-text",
                    supported_mimetypes=[
                        "application/pdf",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ],
                )
            content = await handler.convert(temp_path)
            try:
                size = os.path.getsize(temp_path)
            except Exception:
                size = None
            file_type = None
            if mimetype:
                try:
                    file_type = mimetype.split("/")[-1].split(".")[-1]
                except Exception:
                    file_type = None
            return {
                "success": True,
                "markdown_content": content,
                "file_type": file_type or "unknown",
                "file_size": size,
                "metadata": metadata or {},
                "handler": getattr(handler, "name", "unknown"),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "metadata": metadata or {}}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
