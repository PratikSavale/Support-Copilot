"""Attachment parsing helpers for chat issue intake.

The parser turns user evidence files into a clean issue description. It does
not add anything to the knowledge base; RAG still searches only admin-provided
documentation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from config.settings import get_settings

logger = logging.getLogger(__name__)

AttachmentKind = Literal["auto", "image", "pdf", "log", "video"]

MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
TEXT_PREVIEW_LIMIT = 12000


@dataclass
class ParsedAttachment:
    attachment_type: str
    file_name: str
    mime_type: str
    issue_summary: str
    extracted_text: str = ""
    detected_error: str | None = None
    screen_or_area: str | None = None
    visible_steps: list[str] = field(default_factory=list)
    important_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.55
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_type": self.attachment_type,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "issue_summary": self.issue_summary,
            "extracted_text": self.extracted_text,
            "detected_error": self.detected_error,
            "screen_or_area": self.screen_or_area,
            "visible_steps": self.visible_steps,
            "important_evidence": self.important_evidence,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


class AttachmentSummarySchema(BaseModel):
    detected_error: str | None = Field(None, description="Any visible error messages, exception tracebacks, status codes, or failure details.")
    screen_or_area: str | None = Field(None, description="The name of the screen, webpage URL, module, or UI area shown.")
    visible_steps: list[str] = Field(default_factory=list, description="A step-by-step sequence of user actions or visual steps leading to the error.")
    important_evidence: list[str] = Field(default_factory=list, description="Crucial visual evidence, request IDs, logs, metrics, or timestamps shown.")
    issue_summary: str = Field(..., description="A detailed natural language summary of the issue shown in the attachment.")


class AttachmentParser:
    """Parse uploaded support evidence into a concise issue summary."""

    def __init__(self) -> None:
        self.settings = get_settings()
        from ai.llm_engine import get_llm_engine
        self.llm_engine = get_llm_engine()

    async def parse(
        self,
        *,
        file_name: str,
        mime_type: str,
        data: bytes,
        attachment_type: AttachmentKind = "auto",
    ) -> ParsedAttachment:
        if len(data) > MAX_ATTACHMENT_BYTES:
            raise ValueError("Attachment is too large. Please upload a file under 50 MB.")

        kind = self._resolve_kind(file_name, mime_type, attachment_type)
        if kind in {"log", "pdf"}:
            extracted_text = await self._extract_document_text(kind, data)
            return await self._summarize_text_attachment(
                file_name=file_name,
                mime_type=mime_type,
                attachment_type=kind,
                text=extracted_text,
            )

        if kind in {"image", "video"}:
            return await self._summarize_multimodal_attachment(
                file_name=file_name,
                mime_type=mime_type,
                attachment_type=kind,
                data=data,
            )

        text = self._decode_text(data)
        return await self._summarize_text_attachment(
            file_name=file_name,
            mime_type=mime_type,
            attachment_type="log",
            text=text,
        )

    def _resolve_kind(
        self, file_name: str, mime_type: str, attachment_type: AttachmentKind
    ) -> str:
        if attachment_type != "auto":
            return attachment_type

        suffix = Path(file_name).suffix.lower()
        if mime_type.startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            return "image"
        if mime_type.startswith("video/") or suffix in {".mp4", ".mov", ".webm", ".mkv"}:
            return "video"
        if mime_type == "application/pdf" or suffix == ".pdf":
            return "pdf"
        return "log"

    async def _extract_document_text(self, kind: str, data: bytes) -> str:
        if kind == "pdf":
            return await asyncio.to_thread(self._extract_pdf_text, data)
        return self._decode_text(data)

    def _extract_pdf_text(self, data: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            return (
                "PDF text extraction dependency is not installed. "
                "Install pypdf from requirements.txt to extract PDF content."
            )

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(data)
            tmp.flush()
            reader = PdfReader(tmp.name)
            pages = []
            for page in reader.pages[:12]:
                pages.append(page.extract_text() or "")
            return "\n\n".join(pages).strip()

    def _decode_text(self, data: bytes) -> str:
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return data.decode(encoding, errors="replace").strip()
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace").strip()

    async def _summarize_text_attachment(
        self,
        *,
        file_name: str,
        mime_type: str,
        attachment_type: str,
        text: str,
    ) -> ParsedAttachment:
        cleaned = self._clean_text(text)
        heuristic = self._heuristic_text_summary(cleaned)

        if self.settings.GEMINI_API_KEY and cleaned:
            prompt = self._summary_prompt() + "\n\nAttachment text:\n" + cleaned[:TEXT_PREVIEW_LIMIT]
            try:
                llm_result = await self.llm_engine.generate_multimodal_response(
                    prompt=prompt,
                    mime_type="text/plain",
                    file_bytes=cleaned.encode("utf-8"),
                    response_schema=AttachmentSummarySchema
                )
                if isinstance(llm_result, dict):
                    heuristic.update({k: v for k, v in llm_result.items() if v})
            except Exception as exc:
                logger.warning("LLM text attachment parsing failed: %s", exc)

        summary = self._build_issue_summary(
            file_name=file_name,
            attachment_type=attachment_type,
            detected_error=heuristic.get("detected_error"),
            screen_or_area=heuristic.get("screen_or_area"),
            visible_steps=heuristic.get("visible_steps") or [],
            important_evidence=heuristic.get("important_evidence") or [],
            fallback_text=cleaned,
        )

        warnings = []
        if not cleaned:
            warnings.append("No readable text was found in this attachment.")

        return ParsedAttachment(
            attachment_type=attachment_type,
            file_name=file_name,
            mime_type=mime_type,
            issue_summary=summary,
            extracted_text=cleaned[:TEXT_PREVIEW_LIMIT],
            detected_error=heuristic.get("detected_error"),
            screen_or_area=heuristic.get("screen_or_area"),
            visible_steps=heuristic.get("visible_steps") or [],
            important_evidence=heuristic.get("important_evidence") or [],
            confidence=0.78 if cleaned else 0.35,
            warnings=warnings,
        )

    async def _summarize_multimodal_attachment(
        self,
        *,
        file_name: str,
        mime_type: str,
        attachment_type: str,
        data: bytes,
    ) -> ParsedAttachment:
        if not self.settings.GEMINI_API_KEY:
            summary = (
                f"User attached a {attachment_type} named {file_name}. "
                "Visual parsing needs GEMINI_API_KEY, so ask the user for the visible "
                "error, page name, and steps if this summary is not enough."
            )
            return ParsedAttachment(
                attachment_type=attachment_type,
                file_name=file_name,
                mime_type=mime_type,
                issue_summary=summary,
                confidence=0.25,
                warnings=["Visual parsing is disabled because GEMINI_API_KEY is not configured."],
            )

        try:
            parsed = await self.llm_engine.generate_multimodal_response(
                prompt=self._summary_prompt(),
                mime_type=mime_type,
                file_bytes=data,
                response_schema=AttachmentSummarySchema
            )
        except Exception as exc:
            logger.warning("LLM multimodal attachment parsing failed: %s", exc)
            parsed = None

        if parsed and isinstance(parsed, dict):
            summary = self._build_issue_summary(
                file_name=file_name,
                attachment_type=attachment_type,
                detected_error=parsed.get("detected_error"),
                screen_or_area=parsed.get("screen_or_area"),
                visible_steps=parsed.get("visible_steps") or [],
                important_evidence=parsed.get("important_evidence") or [],
                fallback_text=parsed.get("issue_summary", ""),
            )
            return ParsedAttachment(
                attachment_type=attachment_type,
                file_name=file_name,
                mime_type=mime_type,
                issue_summary=summary,
                detected_error=parsed.get("detected_error"),
                screen_or_area=parsed.get("screen_or_area"),
                visible_steps=parsed.get("visible_steps") or [],
                important_evidence=parsed.get("important_evidence") or [],
                confidence=0.82,
            )

        return ParsedAttachment(
            attachment_type=attachment_type,
            file_name=file_name,
            mime_type=mime_type,
            issue_summary=(
                f"User attached a {attachment_type} named {file_name}, but the file "
                "could not be parsed automatically. Ask for visible error and steps."
            ),
            confidence=0.3,
            warnings=["Automatic visual parsing failed."],
        )

    def _summary_prompt(self) -> str:
        return (
            "You are extracting evidence from a customer support attachment. "
            "Do not solve the issue and do not use external product knowledge. "
            "Extract visual and textual content from this attachment. "
            "Focus on visible errors, page/screen names, user actions, logs, timestamps, "
            "request IDs, and anything useful for searching trusted documentation."
        )

    def _heuristic_text_summary(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        error_pattern = re.compile(
            r"(error|exception|failed|failure|timeout|denied|unauthorized|forbidden|"
            r"not found|traceback|500|502|503|504|400|401|403|404)",
            re.IGNORECASE,
        )
        url_pattern = re.compile(r"(https?://\S+|/[a-z0-9_\-/]+)", re.IGNORECASE)
        step_pattern = re.compile(r"^(\d+[\).:-]|\-|\*)\s+|click|open|select|enter|submit", re.IGNORECASE)

        evidence = [line for line in lines if error_pattern.search(line)][:6]
        steps = [line for line in lines if step_pattern.search(line)][:5]
        urls = []
        for line in lines:
            match = url_pattern.search(line)
            if match:
                urls.append(match.group(0).rstrip(".,;"))
            if len(urls) >= 3:
                break

        detected_error = evidence[0] if evidence else None
        screen_or_area = urls[0] if urls else None

        return {
            "detected_error": detected_error,
            "screen_or_area": screen_or_area,
            "visible_steps": steps,
            "important_evidence": evidence,
        }

    def _build_issue_summary(
        self,
        *,
        file_name: str,
        attachment_type: str,
        detected_error: str | None,
        screen_or_area: str | None,
        visible_steps: list[str],
        important_evidence: list[str],
        fallback_text: str,
    ) -> str:
        parts = [f"Attachment parsed from {attachment_type}: {file_name}."]
        if detected_error:
            parts.append(f"Detected error: {detected_error}")
        if screen_or_area:
            parts.append(f"Screen/page or area: {screen_or_area}")
        if visible_steps:
            parts.append("Visible steps: " + " -> ".join(visible_steps[:5]))
        if important_evidence:
            parts.append("Important evidence: " + " | ".join(important_evidence[:5]))
        if len(parts) == 1 and fallback_text:
            parts.append("Relevant extracted content: " + fallback_text[:900])
        return "\n".join(parts)

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{4,}", "\n\n", text)
        return text.strip()
