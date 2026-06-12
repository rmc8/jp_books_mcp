"""Tests for the client module validation."""

import pytest
from jp_books_mcp.client import BooksOrJpClient


async def test_client_validation_empty_keyword() -> None:
    """Test that empty or whitespace keyword returns empty list immediately."""
    async with BooksOrJpClient() as client:
        # Empty string
        res = await client.search_books("")
        assert res == []

        # Whitespace only
        res2 = await client.search_books("   ")
        assert res2 == []


async def test_client_validation_empty_ndl_title() -> None:
    """Test that empty or whitespace NDL title returns empty list immediately."""
    async with BooksOrJpClient() as client:
        # Empty string
        res = await client.ndl_search_books("")
        assert res == []

        # Whitespace only
        res2 = await client.ndl_search_books("  \t  ")
        assert res2 == []


async def test_client_validation_empty_detail_isbn() -> None:
    """Test that empty or whitespace ISBN raises ValueError."""
    async with BooksOrJpClient() as client:
        with pytest.raises(ValueError, match="ISBN or URL cannot be empty"):
            await client.get_book_details("")

        with pytest.raises(ValueError, match="ISBN or URL cannot be empty"):
            await client.get_book_details("   ")
