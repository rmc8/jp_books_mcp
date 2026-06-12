"""Pydantic data models for Japanese Books MCP."""

from pydantic import BaseModel, Field


class BookSearchResult(BaseModel):
    """Data model representing a book search result from various sources."""

    title: str = Field(description="The title of the book.")
    author: str = Field(default="", description="The authors/creators of the book.")
    publisher: str = Field(default="", description="The publisher of the book.")
    publish_date: str = Field(
        default="", description="The publication or release date of the book."
    )
    url: str = Field(description="The detail page URL of the book.")
    isbn: str = Field(default="", description="The ISBN code or identification code.")
    price: str | None = Field(
        default=None, description="The price of the book if available."
    )
    pages: str | None = Field(
        default=None, description="The page count of the book if available."
    )
    source: str = Field(
        description="The source of search (e.g., 'books.or.jp', 'ndl')."
    )


class BookDetail(BaseModel):
    """Data model representing detailed information of a book."""

    title: str = Field(description="The title of the book.")
    authors: list[str] = Field(
        default_factory=list,
        description="List of authors, supervisors, translators.",
    )
    publisher: str = Field(default="", description="The publisher of the book.")
    description: str = Field(
        default="", description="The description or content intro."
    )
    cover_image: str = Field(
        default="", description="The cover image URL if available."
    )
    url: str = Field(description="The detail URL of the book.")
    isbn: str = Field(default="", description="The ISBN code of the book.")
    size: str = Field(default="", description="The physical size/format of the book.")
    pages: str = Field(default="", description="The page count of the book.")
    price: str = Field(default="", description="The price of the book.")
    publish_date: str = Field(
        default="", description="The publication date (year/month)."
    )
    release_date: str = Field(default="", description="The exact release date.")
    raw_metadata: dict[str, str] = Field(
        default_factory=dict, description="Raw metadata fields parsed from the page."
    )
