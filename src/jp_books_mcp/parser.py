"""HTML and XML parsers for Japanese Books MCP."""

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from jp_books_mcp.models import BookDetail, BookSearchResult

BASE_URL = "https://www.books.or.jp/"


def _clean_isbn(isbn: str) -> str:
    """Remove hyphens and whitespace from ISBN/Code.

    Args:
        isbn: The raw ISBN or identification code.

    Returns:
        The cleaned ISBN/code string.
    """
    return re.sub(r"[-\s]", "", isbn)


def _clean_author(author: str) -> str:
    """Clean up common author prefixes.

    Args:
        author: The raw author string.

    Returns:
        The cleaned author name.
    """
    return re.sub(r"^(著・文・その他|著者)[：:]\s*", "", author)


def _clean_publisher(publisher: str) -> str:
    """Clean up common publisher prefixes.

    Args:
        publisher: The raw publisher string.

    Returns:
        The cleaned publisher name.
    """
    return re.sub(r"^出版社[：:]\s*", "", publisher)


def _get_xml_text(
    parent: ET.Element, name: str, namespaces: dict[str, str]
) -> str:
    """Helper to safely retrieve nested text from an XML element.

    Args:
        parent: The parent XML element.
        name: The name of the child element to find.
        namespaces: The XML namespaces mapping.

    Returns:
        The text content of the child element if found, otherwise an empty string.
    """
    elm = parent.find(name, namespaces)
    return elm.text if elm is not None and elm.text else ""


def parse_books_or_jp_search(html: str) -> list[BookSearchResult]:
    """Parse search results from books.or.jp.

    Args:
        html: HTML source from books.or.jp search results page.

    Returns:
        List of parsed BookSearchResult models.
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all(class_="result_list_item")
    books = []

    for item in items:
        link_tag = item.find("a", class_="result_list_button")
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        if isinstance(href, list):
            href = href[0] if href else ""
        url = urljoin(BASE_URL, href)

        # Extract ISBN/Code from URL if possible
        isbn = ""
        isbn_match = re.search(r"/book-details/([^/]+)", url)
        if isbn_match:
            isbn = isbn_match.group(1)

        title_tag = item.find(class_="result_list_discription_title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = item.find(class_="result_list_discription_author")
        author = ""
        if author_tag:
            author = _clean_author(author_tag.get_text(strip=True))

        publisher_tag = item.find(class_="result_list_discription_publisher")
        publisher = ""
        if publisher_tag:
            publisher = _clean_publisher(publisher_tag.get_text(strip=True))

        publish_date_tag = item.find(class_="result_list_discription_publishdate")
        publish_date = ""
        if publish_date_tag:
            publish_date = publish_date_tag.get_text(strip=True)
            publish_date = re.sub(r"^発売（予定）日[：:]\s*", "", publish_date)

        books.append(
            BookSearchResult(
                title=title,
                author=author,
                publisher=publisher,
                publish_date=publish_date,
                url=url,
                isbn=isbn,
                source="books.or.jp",
            )
        )

    return books


def _extract_authors(soup: BeautifulSoup) -> list[str]:
    """Extract authors, translators, supervisors from book detail page.

    Args:
        soup: BeautifulSoup object of the book detail page.

    Returns:
        List of extracted authors, translators, and supervisors.
    """
    authors = []
    author_tags = soup.find_all(class_="bookdetail_author")
    for tag in author_tags:
        text = tag.get_text(strip=True)
        if text:
            authors.append(text)
    return authors


def _extract_publisher_from_detail(soup: BeautifulSoup) -> str:
    """Extract publisher from book detail page header.

    Args:
        soup: BeautifulSoup object of the book detail page.

    Returns:
        The cleaned publisher name if found, otherwise an empty string.
    """
    publisher_tag = soup.find(class_="bookdetail_publisher")
    if publisher_tag:
        return _clean_publisher(publisher_tag.get_text(strip=True))
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """Extract description (introduction content) with line breaks preserved.

    Args:
        soup: BeautifulSoup object of the book detail page.

    Returns:
        The description string with line breaks.
    """
    intro_tag = soup.find(class_="introduction_content_text")
    if not intro_tag:
        return ""
    # Preserve line breaks by replacing <br> with \n
    # Note: BeautifulSoup modifies the tree in-place, which is fine for our usage
    for br in intro_tag.find_all("br"):
        br.replace_with("\n")
    return intro_tag.get_text().strip()


def _extract_cover_image(soup: BeautifulSoup) -> str:
    """Extract cover image absolute URL from detail page.

    Args:
        soup: BeautifulSoup object of the book detail page.

    Returns:
        The absolute URL of the cover image, or an empty string.
    """
    image_tag = soup.find(class_="main_image")
    if not image_tag:
        return ""
    img = image_tag.find("img")
    if not img:
        return ""
    src = img.get("src", "")
    if isinstance(src, list):
        src = src[0] if src else ""
    return urljoin(BASE_URL, src) if src else ""


def _extract_metadata(soup: BeautifulSoup) -> dict[str, str]:
    """Extract other metadata block as key-value pairs.

    Args:
        soup: BeautifulSoup object of the book detail page.

    Returns:
        A dictionary mapping metadata keys to values (e.g. ISBN, pages, price).
    """
    metadata: dict[str, str] = {}
    other_data_tag = soup.find(class_="otherdata")
    if not other_data_tag:
        return metadata
    p_tag = other_data_tag.find("p")
    if not p_tag:
        return metadata

    # Replace <br> with \n so we can split
    for br in p_tag.find_all("br"):
        br.replace_with("\n")
    lines = p_tag.get_text().split("\n")
    for raw_line in lines:
        line = raw_line.strip()
        if "：" in line:
            k, v = line.split("：", 1)
            # Remove trailing periods if any
            metadata[k.strip()] = re.sub(r"。$", "", v.strip())
        elif ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip()] = re.sub(r"。$", "", v.strip())
    return metadata


def parse_books_or_jp_detail(html: str, url: str) -> BookDetail:
    """Parse detailed information of a book from books.or.jp.

    Args:
        html: HTML source of the book details page.
        url: The URL of the details page.

    Returns:
        BookDetail model with extracted information.
    """
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find(class_="bookdetail_title_text")
    title = title_tag.get_text(strip=True) if title_tag else ""

    authors = _extract_authors(soup)
    publisher = _extract_publisher_from_detail(soup)
    description = _extract_description(soup)
    cover_image = _extract_cover_image(soup)
    metadata = _extract_metadata(soup)

    # Pull fallback metadata if not parsed
    isbn = metadata.get("ISBN", "")
    if not isbn:
        isbn_match = re.search(r"/book-details/(\d+x?|\d+)", url, re.I)
        if isbn_match:
            isbn = isbn_match.group(1)

    return BookDetail(
        title=title,
        authors=authors,
        publisher=publisher or metadata.get("出版社", ""),
        description=description,
        cover_image=cover_image,
        url=url,
        isbn=isbn,
        size=metadata.get("判型", ""),
        pages=metadata.get("ページ数", ""),
        price=metadata.get("定価", ""),
        publish_date=metadata.get("発行年月日", ""),
        release_date=metadata.get("発売日", ""),
        raw_metadata=metadata,
    )


def parse_ndl_search(xml_data: str) -> list[BookSearchResult]:
    """Parse XML search results from National Diet Library Search.

    Args:
        xml_data: XML string returned by NDL Search API.

    Returns:
        List of parsed BookSearchResult models.
    """
    namespaces = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcndl": "http://ndl.go.jp/dcndl/terms/",
        "dcterms": "http://purl.org/dc/terms/",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return []

    books = []
    # Find all <item> tags (RSS 2.0 structure: channel/item)
    items = root.findall(".//item")
    for item in items:
        title = _get_xml_text(item, "title", namespaces)
        link = _get_xml_text(item, "link", namespaces)

        # Extract authors from dc:creator
        creators = []
        for creator_elm in item.findall("dc:creator", namespaces):
            if creator_elm.text:
                creators.append(creator_elm.text)
        author = ", ".join(creators)

        # Extract publisher from dc:publisher
        publisher = _get_xml_text(item, "dc:publisher", namespaces)

        # Extract issue date (dcterms:issued or dc:date)
        publish_date = _get_xml_text(item, "dcterms:issued", namespaces)
        if not publish_date:
            publish_date = _get_xml_text(item, "dc:date", namespaces)

        # Extract price (dcndl:price)
        price = _get_xml_text(item, "dcndl:price", namespaces)

        # Extract size/pages (dc:extent)
        extent = _get_xml_text(item, "dc:extent", namespaces)

        # Extract ISBN
        isbn = ""
        for ident_elm in item.findall("dc:identifier", namespaces):
            xsi_type = ident_elm.get(
                "{http://www.w3.org/2001/XMLSchema-instance}type", ""
            )
            if "ISBN" in xsi_type:
                isbn = ident_elm.text if ident_elm.text else ""
                # Clean ISBN (remove hyphens)
                isbn = _clean_isbn(isbn)
                break

        books.append(
            BookSearchResult(
                title=title,
                author=author,
                publisher=publisher,
                publish_date=publish_date,
                url=link,
                isbn=isbn,
                price=price,
                pages=extent,
                source="ndl",
            )
        )

    return books
