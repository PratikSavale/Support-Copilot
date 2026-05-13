"""
Web scraper utility for knowledge ingestion.

Fetches web pages and extracts clean text using httpx + BeautifulSoup.
"""

import asyncio
import logging
import re
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    """Fetches and cleans web content for knowledge ingestion."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def fetch_content(self, url: str) -> str:
        """Fetch a URL and return cleaned text content using Jina AI Reader.

        Args:
            url: The URL to fetch.

        Returns:
            Cleaned plain-text (markdown) content.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(f"https://r.jina.ai/{url}", headers=headers)
            if response.status_code != 200:
                logger.warning("Fetch failed for %s: Status %s", url, response.status_code)
            response.raise_for_status()
            return response.text

    # ------------------------------------------------------------------
    # Crawling functionality
    # ------------------------------------------------------------------

    async def crawl_website(self, start_url: str, max_pages: int = 200, max_concurrent: int = 5) -> list[str]:
        """Crawl a website recursively, restricted to the start_url path.

        Uses a single shared HTTP client for connection reuse and adds
        polite delays between requests to avoid being rate-limited or
        blocked by the target server.

        Args:
            start_url: Root URL to start crawling from.
            max_pages: Maximum number of pages to fetch.
            max_concurrent: Maximum concurrent HTTP requests.

        Returns:
            List of cleaned text content strings, one per page.
        """
        # Prepare scope: we want to stay on the same domain and under the same path prefix.
        # We strip query and fragment from start_url to determine the allowed path.
        parsed_start = urlparse(start_url)
        path = parsed_start.path
        if not path.endswith("/"):
            # If it's a file (has an extension), take the parent directory.
            if "." in path.split("/")[-1]:
                path = "/".join(path.split("/")[:-1]) + "/"
            else:
                path += "/"
        
        scope_prefix = f"{parsed_start.scheme}://{parsed_start.netloc}{path}"

        parsed_start = urlparse(start_url)
        base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

        visited: set[str] = {start_url}
        queue: list[str] = [start_url]
        results: list[str] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(client: httpx.AsyncClient, url: str) -> tuple[str, list[str]]:
            """Fetch a single page and extract its text + discovered links."""
            async with semaphore:
                try:
                    # 1. Fetch raw HTML (Fast, good for legacy framesets like Java Docs)
                    raw_resp = await client.get(url, headers=headers)
                    html = raw_resp.text
                    
                    # 2. Fetch Jina AI Markdown (Executes JS, good for React SPAs)
                    jina_resp = await client.get(f"https://r.jina.ai/{url}", headers=headers)
                    text = jina_resp.text
                    
                except httpx.HTTPStatusError as exc:
                    logger.warning("HTTP %s for %s", exc.response.status_code, url)
                    return "", []
                except Exception as exc:
                    logger.warning("Failed to fetch %s: %s", url, exc)
                    return "", []

                new_urls: list[str] = []
                
                # --- extract links from raw HTML ---
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup.find_all(["a", "frame", "iframe"]):
                    href = tag.get("href") or tag.get("src")
                    if isinstance(href, str):
                        abs_url = urljoin(url, href)
                        abs_url, _ = urldefrag(abs_url)
                        
                        # Check if abs_url starts with our scope prefix (ignoring query/params)
                        parsed_abs = urlparse(abs_url)
                        abs_path_only = f"{parsed_abs.scheme}://{parsed_abs.netloc}{parsed_abs.path}"
                        
                        if abs_path_only.startswith(scope_prefix):
                            new_urls.append(abs_url)

                # --- extract links from Jina Markdown (for React/JS SPAs) ---
                for match in re.finditer(r'\]\((https?://[^\s\)]+)\)', text):
                    abs_url = match.group(1)
                    abs_url, _ = urldefrag(abs_url)
                    if abs_url.startswith(base_domain):
                        new_urls.append(abs_url)

                # --- Storybook SPA Heuristic ---
                # Storybook loads its actual content inside an iframe. If we detect a Storybook URL,
                # we also fetch the iframe content directly to ensure we don't just index the sidebar.
                storybook_match = re.search(r'\?path=/docs/(.*?)$', url)
                if storybook_match:
                    try:
                        story_id = storybook_match.group(1).replace('--docs', '').replace('&viewMode=docs', '')
                        iframe_url = urljoin(url, f"/iframe.html?id={story_id}&viewMode=docs")
                        logger.info("Detected Storybook URL. Fetching iframe content: %s", iframe_url)
                        iframe_resp = await client.get(f"https://r.jina.ai/{iframe_url}", headers=headers)
                        if iframe_resp.status_code == 200 and iframe_resp.text:
                            # Append the iframe content to the shell text so we capture the actual component info
                            text += "\n\n" + iframe_resp.text
                    except Exception as e:
                        logger.warning("Failed to fetch Storybook iframe for %s: %s", url, e)

                # Small delay per request to be polite to the server.
                await asyncio.sleep(0.3)

                return text, new_urls

        logger.info("Starting crawl of %s (scope_prefix=%s, max_pages=%d)", start_url, scope_prefix, max_pages)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            while queue and len(results) < max_pages:
                # Take a batch from the queue.
                batch = queue[:max_concurrent]
                queue = queue[max_concurrent:]

                tasks = [fetch_one(client, u) for u in batch]
                batch_results = await asyncio.gather(*tasks)

                for text, new_urls in batch_results:
                    if text and len(text) >= 50:
                        results.append(text)
                    for u in new_urls:
                        if u not in visited and len(visited) < max_pages:
                            visited.add(u)
                            queue.append(u)

                if len(results) % 20 == 0 and results:
                    logger.info("Crawl progress: %d pages collected, %d in queue", len(results), len(queue))

        logger.info("Crawl finished: %d pages collected from %s", len(results), start_url)
        return results

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
