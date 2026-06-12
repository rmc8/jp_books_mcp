# Japanese Books MCP Server (`jp-books-mcp`)

[![PyPI version](https://img.shields.io/pypi/v/jp-books-mcp.svg)](https://pypi.org/project/jp-books-mcp/)
[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)

A Model Context Protocol (MCP) server that provides tools to search Japanese books and retrieve rich metadata. It integrates search results from:
1. **[books.or.jp](https://www.books.or.jp/)** (Japan Book Publishers Association)
2. **[National Diet Library (NDL) Search](https://ndlsearch.ndl.go.jp/)** (National Diet Library Search)

## Features

- **Book Search**: Query books on `books.or.jp` or the National Diet Library (NDL).
- **Rich Metadata Extraction**: Retrieve full book descriptions, publishers, formats (size), pages, prices, publication dates, and cover image URLs.
- **Robust Schema**: Data is validated and structured using Pydantic v2.

---

## Tools

The server registers three tools:

### 1. `jp_books_search`
Searches for books on `books.or.jp` by title, author, publisher, or other keywords.
- **Arguments**:
  - `query` (string, required): The search query (e.g., book title, author name, or keyword).
- **Returns**: A list of search results including title, author, publisher, publish date, URL, and ISBN/Code.

### 2. `ndl_books_search`
Searches for books in the National Diet Library (NDL) Database using their OpenSearch API.
- **Arguments**:
  - `query` (string, required): The search query.
- **Returns**: A list of NDL catalog results including title, authors, publisher, publication date, NDL link, ISBN, price, and pages.

### 3. `jp_books_get_details`
Retrieves rich details and descriptions for a specific book from `books.or.jp` using its ISBN or internal code.
- **Arguments**:
  - `isbn` (string, required): The 13-digit ISBN or JPRO book code.
- **Returns**: Detailed book metadata including title, author list, publisher, description, cover image URL, size, pages, price, publish/release dates, and raw metadata.

---

## Configuration

You can easily run this MCP server using `uvx` (part of the `uv` toolchain) or `npx`/`pipx`.

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

#### Using `uvx` (Recommended)

```json
{
  "mcpServers": {
    "jp-books-mcp": {
      "command": "uvx",
      "args": [
        "jp-books-mcp"
      ]
    }
  }
}
```

#### Using `python` (if installed globally or in a virtualenv)

```json
{
  "mcpServers": {
    "jp-books-mcp": {
      "command": "python",
      "args": [
        "-m",
        "jp_books_mcp.server"
      ]
    }
  }
}
```

### Cursor Configuration

To use it in Cursor:
1. Go to **Settings** > **Features** > **MCP**.
2. Click **+ Add New MCP Server**.
3. Set the details:
   - **Name**: `jp-books-mcp`
   - **Type**: `command`
   - **Command**: `uvx jp-books-mcp`

---

## Development

To set up the project locally for development, make sure you have `uv` installed.

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/rmc8/jp_books_mcp.git
cd jp_books_mcp
uv sync
```

### 2. Running the server locally

```bash
uv run jp-books-mcp
```

### 3. Running tests and linting

```bash
# Code formatting and lint check
uv run ruff check src

# Type checking
uv run mypy src
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.