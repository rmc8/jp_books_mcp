"""FastMCP server exposing Japanese Books operations as MCP tools."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json

from mcp.server.fastmcp import FastMCP

from jp_books_mcp.client import BooksOrJpClient


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[BooksOrJpClient]:
    """Manage the lifecycle of the HTTP client."""
    client = BooksOrJpClient()
    try:
        yield client
    finally:
        await client.close()


# Initialise the FastMCP server instance with lifespan management.
mcp = FastMCP("jp_books", lifespan=lifespan)


@mcp.tool()
async def jp_books_search(query: str) -> str:
    """Search for Japanese books on books.or.jp.

    Args:
        query: The search query / keywords.

    Returns:
        A JSON string containing a list of book search results or an error message.
    """
    if not query or not query.strip():
        return json.dumps([])

    try:
        client: BooksOrJpClient = mcp.get_context().request_context.lifespan_context
        results = await client.search_books(query)
        # Serialize list of Pydantic models
        return json.dumps(
            [r.model_dump() for r in results], indent=2, ensure_ascii=False
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to search books: {e}"}, ensure_ascii=False
        )


@mcp.tool()
async def ndl_books_search(query: str) -> str:
    """Search for Japanese books on National Diet Library (NDL) Search.

    Args:
        query: The search query / title.

    Returns:
        A JSON string containing a list of search results from NDL or an error.
    """
    if not query or not query.strip():
        return json.dumps([])

    try:
        client: BooksOrJpClient = mcp.get_context().request_context.lifespan_context
        results = await client.ndl_search_books(query)
        # Serialize list of Pydantic models
        return json.dumps(
            [r.model_dump() for r in results], indent=2, ensure_ascii=False
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to search NDL books: {e}"}, ensure_ascii=False
        )


@mcp.tool()
async def jp_books_get_details(isbn: str) -> str:
    """Get detailed information for a Japanese book by ISBN or URL.

    Args:
        isbn: The ISBN code of the book (with or without hyphens)
            or the books.or.jp URL.

    Returns:
        A JSON string containing detailed book metadata or an error message.
    """
    if not isbn or not isbn.strip():
        return json.dumps({"error": "ISBN or URL cannot be empty"})

    try:
        client: BooksOrJpClient = mcp.get_context().request_context.lifespan_context
        details = await client.get_book_details(isbn)
        # Serialize Pydantic model
        return json.dumps(details.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to get book details: {e}"}, ensure_ascii=False
        )


def main() -> None:
    """Entry-point for the ``jp-books-mcp`` CLI command."""
    mcp.run()


if __name__ == "__main__":
    main()
