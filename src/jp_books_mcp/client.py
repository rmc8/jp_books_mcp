from __future__ import annotations

"""HTTP Client for books.or.jp and NDL Search scraping."""

import re
from urllib.parse import urljoin

import httpx

from jp_books_mcp.models import BookDetail, BookSearchResult
from jp_books_mcp.parser import (
    parse_books_or_jp_detail,
    parse_books_or_jp_search,
    parse_ndl_search,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)

BASE_URL = "https://www.books.or.jp/"
SEARCH_URL = "https://www.books.or.jp/search-results"


class BooksOrJpClient:
    """Scraping client for books.or.jp and NDL Search.

    Reuses the underlying httpx.AsyncClient connection pool for efficiency.
    The AsyncClient is lazily initialised on first use to avoid early resource
    allocation and to support re-initialisation after close().
    """

    def __init__(self) -> None:
        """Initialize the HTTP client with headers.

        The underlying httpx.AsyncClient is created lazily on first request
        or when entering an async context manager.
        """
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily initialise the underlying AsyncClient if not already created.

        Returns:
            The existing or newly created AsyncClient instance.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, headers=self.headers)
        return self._client

    @property
    def client(self) -> httpx.AsyncClient:
        """Access the underlying AsyncClient (must be initialised first).

        Raises:
            RuntimeError: If accessed before initialisation.
        """
        if self._client is None:
            raise RuntimeError(
                "AsyncClient has not been initialised. "
                "Call an API method or use the async context manager first."
            )
        return self._client

    async def __aenter__(self) -> BooksOrJpClient:
        """Async context manager entry — ensures the client is initialised."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client session and reset for reuse."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get_csrf_token(self) -> tuple[str, str]:
        """Fetch the home page and extract the CSRF token and cookies.

        Returns:
            A tuple of (token, cookies_header_string).

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        client = await self._ensure_client()
        resp = await client.get(BASE_URL)
        resp.raise_for_status()

        html = resp.text
        # Use regex to find <input type="hidden" name="_token" value="...">
        token_match = re.search(
            r'<input[^>]*name="_token"[^>]*value="([^"]+)"', html
        )
        token = token_match.group(1) if token_match else ""

        # Construct cookies header manually if needed, or use client.cookies
        cookie_parts = [f"{k}={v}" for k, v in resp.cookies.items()]
        cookies = "; ".join(cookie_parts)

        return token, cookies

    async def search_books(self, keyword: str) -> list[BookSearchResult]:
        """Search books on books.or.jp.

        Args:
            keyword: Search query.

        Returns:
            List of books found. If the query is empty or only contains whitespace,
            an empty list is returned without performing a request.

        Raises:
            ValueError: If the CSRF token cannot be retrieved.
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        if not keyword or not keyword.strip():
            return []

        client = await self._ensure_client()
        token, cookies = await self._get_csrf_token()
        if not token:
            raise ValueError("Failed to retrieve CSRF token from books.or.jp")

        form = {
            "_token": token,
            "searchforbooks_keyword": keyword,
            "searchforbooks_title": "",
            "searchforbooks_author": "",
            "searchforbooks_publisher": "",
            "searchforbooks_afteryear": "",
            "searchforbooks_aftermonth": "",
            "searchforbooks_afterday": "",
            "searchforbooks_beforeyear": "",
            "searchforbooks_beforemonth": "",
            "searchforbooks_beforeday": "",
            "publishtype1": "on",
            "publishtype2": "on",
            "publishtype3": "on",
            "publishtype4": "on",
            "accessible_search_flag": "0",
            "first_books_search_flag": "1",
        }

        # Override headers for form submission
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.books.or.jp",
            "Referer": BASE_URL,
            "Cookie": cookies,
        }

        resp = await client.post(SEARCH_URL, data=form, headers=headers)
        resp.raise_for_status()

        return parse_books_or_jp_search(resp.text)

    async def get_book_details(self, isbn_or_url: str) -> BookDetail:
        """Fetch book details from books.or.jp.

        Args:
            isbn_or_url: ISBN code or detail URL.

        Returns:
            Detailed book information model.

        Raises:
            ValueError: If the input is empty or invalid.
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        if not isbn_or_url or not isbn_or_url.strip():
            raise ValueError("ISBN or URL cannot be empty")

        if isbn_or_url.startswith("http://") or isbn_or_url.startswith("https://"):
            url = isbn_or_url
        else:
            # Clean ISBN (remove hyphens)
            isbn = re.sub(r"[-\s]", "", isbn_or_url)
            url = urljoin(BASE_URL, f"/book-details/{isbn}")

        client = await self._ensure_client()
        resp = await client.get(url)
        resp.raise_for_status()

        return parse_books_or_jp_detail(resp.text, url)

    async def ndl_search_books(self, title: str) -> list[BookSearchResult]:
        """Search books on National Diet Library (NDL) Search.

        Args:
            title: Title to search for.

        Returns:
            List of books found from NDL. If the title is empty or only contains
            whitespace, an empty list is returned.

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        if not title or not title.strip():
            return []

        url = "https://ndlsearch.ndl.go.jp/api/opensearch"
        params: dict[str, str | int] = {
            "title": title,
            "mediatype": "books",
            "cnt": 50,  # limit to 50 results
        }

        client = await self._ensure_client()
        resp = await client.get(url, params=params)
        resp.raise_for_status()

        return parse_ndl_search(resp.text)
