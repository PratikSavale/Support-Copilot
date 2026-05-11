"""
Web scraper utility for knowledge ingestion.

Fetches web pages and extracts clean text using httpx + BeautifulSoup.
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup


class WebScraper:
    """Fetches and cleans web content for knowledge ingestion."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def fetch_content(self, url: str) -> str:
        """Fetch a URL and return cleaned text content.

        Args:
            url: The URL to fetch.

        Returns:
            Cleaned plain-text content.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CopilotBot/1.0)",
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return self._parse_html(response.text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_html(html: str) -> str:
        """Strip boilerplate elements and return plain text."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements.
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")

        # Collapse excessive whitespace while preserving paragraph breaks.
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)

        # Collapse runs of 3+ newlines into 2.
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Stub methods for non-HTML content (future work)
    # ------------------------------------------------------------------

    async def fetch_pdf(self, url: str) -> str:
        """Fetch and extract text from a PDF (placeholder)."""
        # TODO: Implement with PyPDF2 or pdfplumber if needed.
        raise NotImplementedError("PDF ingestion not yet implemented")

    async def fetch_docx(self, url: str) -> str:
        """Fetch and extract text from a DOCX file (placeholder)."""
        # TODO: Implement with python-docx if needed.
        raise NotImplementedError("DOCX ingestion not yet implemented")
