"""Tests for the parser module."""

from bs4 import BeautifulSoup

from jp_books_mcp.parser import (
    _clean_author,
    _clean_isbn,
    _clean_publisher,
    _extract_authors,
    _extract_cover_image,
    _extract_description,
    _extract_metadata,
    _extract_publisher_from_detail,
    parse_books_or_jp_detail,
    parse_books_or_jp_search,
    parse_ndl_search,
)


def test_clean_functions() -> None:
    """Test helper cleaning functions."""
    assert _clean_isbn("978-4-8144-0007-2") == "9784814400072"
    assert _clean_isbn(" 978 4 8144 0007 2 ") == "9784814400072"

    assert _clean_author("著・文・その他：Brendan Gregg") == "Brendan Gregg"
    assert _clean_author("著者: 鈴木 太郎") == "鈴木 太郎"
    assert _clean_author("山田 花子") == "山田 花子"

    assert _clean_publisher("出版社：オライリー・ジャパン") == "オライリー・ジャパン"
    assert _clean_publisher("出版社: 翔泳社") == "翔泳社"
    assert _clean_publisher("技術評論社") == "技術評論社"


def test_parse_books_or_jp_search() -> None:
    """Test parsing books.or.jp search results page HTML."""
    html = """
    <div class="result_list_item">
        <a class="result_list_button" href="/book-details/9784814400072">Detail</a>
        <div class="result_list_discription_title">
            詳解 システム・パフォーマンス 第2版
        </div>
        <div class="result_list_discription_author">
            著・文・その他：Brendan Gregg
        </div>
        <div class="result_list_discription_publisher">
            出版社：オライリー・ジャパン
        </div>
        <div class="result_list_discription_publishdate">
            発売（予定）日：2023年01月24日
        </div>
    </div>
    """
    results = parse_books_or_jp_search(html)
    assert len(results) == 1
    book = results[0]
    assert book.title == "詳解 システム・パフォーマンス 第2版"
    assert book.author == "Brendan Gregg"
    assert book.publisher == "オライリー・ジャパン"
    assert book.publish_date == "2023年01月24日"
    assert book.isbn == "9784814400072"
    assert book.url == "https://www.books.or.jp/book-details/9784814400072"
    assert book.source == "books.or.jp"


def test_parse_books_or_jp_detail() -> None:
    """Test parsing books.or.jp book details page HTML."""
    html = """
    <div class="bookdetail_title_text">詳解 システム・パフォーマンス 第2版</div>
    <div class="bookdetail_author">著：Brendan Gregg</div>
    <div class="bookdetail_author">訳：長尾 高弘</div>
    <div class="bookdetail_publisher">出版社：オライリー・ジャパン</div>
    <div class="introduction_content_text">
        改訂版！<br>パフォーマンス分析について解説します。
    </div>
    <div class="main_image">
        <img src="/9784814400072.jpg" />
    </div>
    <div class="otherdata">
        <p>
            ISBN：9784814400072<br>
            出版社：オライリー・ジャパン<br>
            判型：B5変<br>
            ページ数：940ページ<br>
            定価：6000円（本体）。<br>
            発行年月日：2023年01月<br>
            発売日：2023年01月24日。
        </p>
    </div>
    """
    url = "https://www.books.or.jp/book-details/9784814400072"
    detail = parse_books_or_jp_detail(html, url)

    assert detail.title == "詳解 システム・パフォーマンス 第2版"
    assert detail.authors == ["著：Brendan Gregg", "訳：長尾 高弘"]
    assert detail.publisher == "オライリー・ジャパン"
    assert detail.description == "改訂版！\nパフォーマンス分析について解説します。"
    assert detail.cover_image == "https://www.books.or.jp/9784814400072.jpg"
    assert detail.isbn == "9784814400072"
    assert detail.size == "B5変"
    assert detail.pages == "940ページ"
    assert detail.price == "6000円（本体）"
    assert detail.publish_date == "2023年01月"
    assert detail.release_date == "2023年01月24日"


def test_parse_ndl_search() -> None:
    """Test parsing NDL Search RSS/XML response."""
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:dcterms="http://purl.org/dc/terms/"
         xmlns:dcndl="http://ndl.go.jp/dcndl/terms/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <channel>
        <item>
          <title>絵で見てわかるシステムパフォーマンスの仕組み</title>
          <link>https://ndlsearch.ndl.go.jp/books/R100000002-I025502908</link>
          <dc:creator>小田, 圭二</dc:creator>
          <dc:creator>榑松, 谷仁</dc:creator>
          <dc:publisher>翔泳社</dc:publisher>
          <dcterms:issued>2014.6</dcterms:issued>
          <dcndl:price>2580円</dcndl:price>
          <dc:extent>325p</dc:extent>
          <dc:identifier xsi:type="dcterms:ISBN">978-4-7981-3460-4</dc:identifier>
        </item>
      </channel>
    </rss>
    """
    results = parse_ndl_search(xml_data)
    assert len(results) == 1
    book = results[0]
    assert book.title == "絵で見てわかるシステムパフォーマンスの仕組み"
    assert book.author == "小田, 圭二, 榑松, 谷仁"
    assert book.publisher == "翔泳社"
    assert book.publish_date == "2014.6"
    assert book.url == "https://ndlsearch.ndl.go.jp/books/R100000002-I025502908"
    assert book.isbn == "9784798134604"
    assert book.price == "2580円"
    assert book.pages == "325p"
    assert book.source == "ndl"


def test_helper_extractors() -> None:
    """Test individual _extract_* functions with partial HTML."""
    soup = BeautifulSoup(
        '<div class="bookdetail_author">Author A</div>', "html.parser"
    )
    assert _extract_authors(soup) == ["Author A"]

    soup2 = BeautifulSoup(
        '<div class="bookdetail_publisher">出版社：Publisher B</div>',
        "html.parser",
    )
    assert _extract_publisher_from_detail(soup2) == "Publisher B"

    soup3 = BeautifulSoup(
        '<div class="introduction_content_text">Line 1<br>Line 2</div>',
        "html.parser",
    )
    assert _extract_description(soup3) == "Line 1\nLine 2"

    soup4 = BeautifulSoup(
        '<div class="main_image"><img src="/image.jpg" /></div>',
        "html.parser",
    )
    assert _extract_cover_image(soup4) == "https://www.books.or.jp/image.jpg"

    soup5 = BeautifulSoup(
        '<div class="otherdata"><p>定価：1000円。<br>ページ数：200p</p></div>',
        "html.parser",
    )
    metadata = _extract_metadata(soup5)
    assert metadata.get("定価") == "1000円"
    assert metadata.get("ページ数") == "200p"
