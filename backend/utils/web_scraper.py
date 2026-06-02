"""
Web scraper utility for knowledge ingestion.

Fetches web pages and extracts clean text using httpx + BeautifulSoup.
"""

import asyncio
import logging
import re
from collections import deque
from typing import Callable, Any
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    """Fetches and cleans web content for knowledge ingestion."""

    def __init__(self, timeout: float = 30.0, polite_delay: float = 0.3) -> None:
        self.timeout = timeout
        self.polite_delay = polite_delay
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    async def fetch_content(self, url: str) -> str:
        """Fetch a URL and return cleaned text content using Jina AI Reader.

        Args:
            url: The URL to fetch.

        Returns:
            Cleaned plain-text (markdown) content.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(f"https://r.jina.ai/{url}", headers=self.headers)
            if response.status_code != 200:
                logger.warning("Fetch failed for %s: Status %s", url, response.status_code)
            response.raise_for_status()
            return response.text

    # ------------------------------------------------------------------
    # Crawling functionality
    # ------------------------------------------------------------------

    async def crawl_website(
        self,
        start_url: str,
        max_pages: int = 200,
        max_concurrent: int = 20,
        on_page_crawled: Callable[[int], Any] | None = None,
    ) -> list[str]:
        """Crawl a website recursively, restricted to the start_url path.

        Args:
            start_url: Root URL to start crawling from.
            max_pages: Maximum number of pages to fetch.
            max_concurrent: Maximum concurrent HTTP requests.
            on_page_crawled: Callback function called when a new page is processed.

        Returns:
            List of dicts with {"url": str, "content": str}.
        """
        parsed_start = urlparse(start_url)
        path = parsed_start.path
        if not path.endswith("/"):
            if "." in path.split("/")[-1]:
                path = "/".join(path.split("/")[:-1]) + "/"
            else:
                path += "/"
        
        scope_prefix = f"{parsed_start.scheme}://{parsed_start.netloc}{path}"
        base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"
        
        # Determine the base path prefix to restrict crawling to the specific documentation/subsite.
        base_path = parsed_start.path
        if not base_path.endswith('/'):
            base_path = base_path.rsplit('/', 1)[0] + '/'
                
        base_prefix = f"{base_domain}{base_path}"

        queue: asyncio.Queue[str] = asyncio.Queue()
        await queue.put(start_url)
        
        visited: set[str] = {start_url}
        results: list[dict[str, str]] = []
        results_lock = asyncio.Lock()

        async def fetch_one(client: httpx.AsyncClient, url: str) -> tuple[str, str, list[str]]:
            """Fetch a single page and extract its text + discovered links."""
            html = ""
            try:
                # 1. Fetch raw HTML
                resp = await client.get(url, headers=self.headers, timeout=10.0)
                if resp.status_code == 200:
                    html = resp.text
            except Exception as e:
                logger.debug("Raw fetch failed for %s: %s", url, e)

            text = ""
            if html:
                text = self._parse_html(html)

            # Check if local HTML parsing was clean, high-quality, and sufficient.
            # We bypass Jina AI Reader completely if local parsing succeeds with good prose.
            is_static_doc_ok = text and len(text) >= 150 and self._is_quality_page(text)
            is_storybook = "path=/docs" in url or "iframe.html" in url

            if not is_static_doc_ok or is_storybook:
                try:
                    logger.info("Falling back to Jina Reader for %s (local content len: %d)", url, len(text))
                    jina_resp = await client.get(f"https://r.jina.ai/{url}", headers=self.headers)
                    if jina_resp.status_code == 200 and jina_resp.text:
                        jina_text = jina_resp.text
                        if len(jina_text) > len(text):
                            text = jina_text
                except Exception as exc:
                    logger.warning("Failed to fetch %s via Jina fallback: %s", url, exc)
                    # Use local parsed text as fallback if Jina fails
                
            if not text:
                return "", "", []

            new_urls: list[str] = []
            
            # --- extract links from raw HTML (for JavaDocs/framesets) ---
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup.find_all(["a", "frame", "iframe"]):
                    href = tag.get("href") or tag.get("src")
                    if href:
                        abs_url = urljoin(url, href)
                        abs_url, _ = urldefrag(abs_url)
                        # Normalize URL to prevent infinite loops (e.g. from session IDs)
                        if '?' in abs_url and 'path=/docs' not in abs_url:
                            abs_url = abs_url.split('?')[0]
                        if abs_url.startswith(base_prefix):
                            new_urls.append(abs_url)

            # --- extract links from Jina Markdown / text content ---
            for match in re.finditer(r'\]\((https?://[^\s\)]+)\)', text):
                abs_url = match.group(1)
                abs_url, _ = urldefrag(abs_url)
                if '?' in abs_url and 'path=/docs' not in abs_url:
                    abs_url = abs_url.split('?')[0]
                if abs_url.startswith(base_prefix):
                    new_urls.append(abs_url)

            # --- Storybook SPA Heuristic ---
            storybook_match = re.search(r'\?path=/docs/(.*?)$', url)
            if storybook_match:
                try:
                    story_id = storybook_match.group(1).replace('--docs', '').replace('&viewMode=docs', '')
                    iframe_url = urljoin(url, f"/iframe.html?id={story_id}&viewMode=docs")
                    logger.info("Detected Storybook URL. Fetching iframe content: %s", iframe_url)
                    iframe_resp = await client.get(f"https://r.jina.ai/{iframe_url}", headers=self.headers)
                    if iframe_resp.status_code == 200 and iframe_resp.text:
                        text += "\n\n" + iframe_resp.text
                except Exception as e:
                    logger.warning("Failed to fetch Storybook iframe for %s: %s", url, e)

            # Small delay per request to be polite to the server.
            await asyncio.sleep(0.1)

            return url, text, new_urls

        async def worker(client: httpx.AsyncClient) -> None:
            """Independent worker pulling and processing pages from queue."""
            while True:
                try:
                    url = await queue.get()
                except asyncio.CancelledError:
                    break

                try:
                    async with results_lock:
                        if len(results) >= max_pages:
                            queue.task_done()
                            continue

                    fetched_url, text, new_urls = await fetch_one(client, url)

                    if text and len(text) >= 100 and self._is_quality_page(text):
                        async with results_lock:
                            if len(results) < max_pages:
                                results.append({"url": fetched_url, "content": text})
                                count = len(results)
                                if count > 0 and count % 20 == 0:
                                    logger.info("Crawl progress: %d pages collected, %d in queue", count, queue.qsize())
                                
                                # Call the progress callback if registered
                                if on_page_crawled:
                                    try:
                                        if asyncio.iscoroutinefunction(on_page_crawled):
                                            await on_page_crawled(count)
                                        else:
                                            on_page_crawled(count)
                                    except Exception as cb_err:
                                        logger.debug("Progress callback error: %s", cb_err)

                    for u in new_urls:
                        async with results_lock:
                            if u not in visited and len(visited) < max_pages:
                                visited.add(u)
                                await queue.put(u)
                except Exception as e:
                    logger.debug("Error in crawl worker for %s: %s", url, e)
                finally:
                    queue.task_done()

        logger.info("Starting crawl of %s (scope_prefix=%s, max_pages=%d)", start_url, scope_prefix, max_pages)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            num_workers = min(max_concurrent, max_pages)
            workers = [asyncio.create_task(worker(client)) for _ in range(num_workers)]

            async def wait_completion() -> None:
                await queue.join()

            async def monitor() -> None:
                while True:
                    async with results_lock:
                        if len(results) >= max_pages:
                            break
                    await asyncio.sleep(0.2)

            # Wait until either the queue is fully processed or we reach max_pages
            done, pending = await asyncio.wait(
                [asyncio.create_task(wait_completion()), asyncio.create_task(monitor())],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            for w in workers:
                w.cancel()

            await asyncio.gather(*workers, return_exceptions=True)

        logger.info("Crawl finished: %d pages collected from %s", len(results), start_url)
        return results

    @staticmethod
    def _is_quality_page(text: str) -> bool:
        """Reject pages that are just navigation indices or frameset shells.

        Catches:
          - HTML frameset boilerplate ("Frame Alert", "JavaScript is disabled")
          - Pure package/class listing pages (lines are just dotted identifiers)
          - Pages with almost no sentences (< 3 sentence-endings per 1000 chars)
        """
        # Reject frameset boilerplate
        if "Frame Alert" in text and "frames feature" in text:
            return False

        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if len(lines) < 3:
            return False

        # Count sentence-like structure
        sentence_endings = len(re.findall(r'[.!?]\s', text))
        density = sentence_endings / (len(text) / 1000) if text else 0

        # Count lines that are single dotted identifiers (java.nio.channels)
        ident_lines = sum(
            1 for ln in lines
            if re.match(r'^[\w$.]+$', ln) and len(ln) > 5
        )
        ident_ratio = ident_lines / len(lines) if lines else 0

        # Reject if >50% of lines are just identifiers (Unless it has sentences, e.g. JavaDocs)
        if ident_ratio > 0.5 and density < 0.5:
            return False

        # Reject if extremely low prose density (< 1 sentence per 1000 chars)
        # BUT allow code-heavy pages that have some structure
        if density < 0.5 and ident_ratio > 0.4:
            return False

        return True

    @staticmethod
    def _parse_html(html: str) -> str:
        """Strip boilerplate elements and return plain text (fallback if Jina not used)."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements.
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Future work
    # ------------------------------------------------------------------

    async def fetch_pdf(self, url: str) -> str:
        raise NotImplementedError("PDF ingestion not yet implemented")

    async def fetch_docx(self, url: str) -> str:
        raise NotImplementedError("DOCX ingestion not yet implemented")
