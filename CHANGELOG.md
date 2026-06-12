# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-12

### Fixed
- **`FastMCP.shutdown` AttributeError**: Replaced the deprecated `@mcp.shutdown()` decorator with the official `lifespan` context manager API. The `BooksOrJpClient` lifecycle is now managed via `FastMCP`'s `lifespan` parameter, ensuring proper initialization and cleanup of HTTP client resources.

## [0.1.0] - 2026-06-12

### Added
- Initial release of `jp-books-mcp`.
- **MCP Tools**:
  - `jp_books_search`: Search books by query on `books.or.jp`.
  - `ndl_books_search`: Search books by query on the National Diet Library (NDL).
  - `jp_books_get_details`: Retrieve rich book details (full description, pages, price, cover image URL, and other metadata) from `books.or.jp`.
- **Core Implementation**:
  - Robust parser logic using `BeautifulSoup` for HTML parsing and `xml.etree.ElementTree` for NDL XML responses.
  - Strict data validation and serialization models powered by Pydantic v2 (`BookSearchResult` and `BookDetail`).
  - Modular HTTP client wrapper using `httpx` with customized User-Agent headers.
- **Project Structure**:
  - Standardized project structure configured with `pyproject.toml` and `hatchling` build system.
  - Development tooling configuration for `ruff` and `mypy` (strict mode).
