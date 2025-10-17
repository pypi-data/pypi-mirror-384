"""HTML content extraction functions using BeautifulSoup."""

from typing import Any

from bs4 import BeautifulSoup
from loguru import logger


def extract_page_title(html: str) -> str | None:
    """Extract the page title from HTML content.

    Args:
        html: HTML content as string

    Returns:
        Page title or None if not found
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
    except Exception:
        logger.exception("Error extracting page title")
        return None
    else:
        return None


def extract_meta_description(html: str) -> str | None:
    """Extract the meta description from HTML content.

    Args:
        html: HTML content as string

    Returns:
        Meta description or None if not found
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()
    except Exception:
        logger.exception("Error extracting meta description")
        return None
    else:
        return None


def extract_open_graph_metadata(html: str) -> dict[str, Any]:
    """Extract Open Graph metadata from HTML content.

    Args:
        html: HTML content as string

    Returns:
        Dictionary containing Open Graph metadata
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        og_data = {}

        # Find all Open Graph meta tags
        og_tags = soup.find_all(
            "meta", attrs={"property": lambda x: x and x.startswith("og:")}
        )

        for tag in og_tags:
            property_name = tag.get("property", "").replace("og:", "")
            content = tag.get("content", "").strip()
            if property_name and content:
                og_data[property_name] = content

    except Exception:
        logger.exception("Error extracting Open Graph metadata")
        return {}
    else:
        return og_data


def extract_h1_headers(html: str) -> list[str]:
    """Extract all H1 header text from HTML content.

    Args:
        html: HTML content as string

    Returns:
        List of H1 header texts
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        h1_tags = soup.find_all("h1")
        headers = []

        for tag in h1_tags:
            text = tag.get_text(strip=True)
            if text:
                headers.append(text)

    except Exception:
        logger.exception("Error extracting H1 headers")
        return []
    else:
        return headers


def extract_h2_headers(html: str) -> list[str]:
    """Extract all H2 header text from HTML content.

    Args:
        html: HTML content as string

    Returns:
        List of H2 header texts
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        h2_tags = soup.find_all("h2")
        headers = []

        for tag in h2_tags:
            text = tag.get_text(strip=True)
            if text:
                headers.append(text)

    except Exception:
        logger.exception("Error extracting H2 headers")
        return []
    else:
        return headers


def extract_h3_headers(html: str) -> list[str]:
    """Extract all H3 header text from HTML content.

    Args:
        html: HTML content as string

    Returns:
        List of H3 header texts
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        h3_tags = soup.find_all("h3")
        headers = []

        for tag in h3_tags:
            text = tag.get_text(strip=True)
            if text:
                headers.append(text)

    except Exception:
        logger.exception("Error extracting H3 headers")
        return []
    else:
        return headers


def extract_all_headers(html: str) -> dict[str, list[str]]:
    """Extract all header levels (H1-H6) from HTML content.

    Args:
        html: HTML content as string

    Returns:
        Dictionary with header levels as keys and lists of texts as values
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        headers = {}

        for level in range(1, 7):  # H1 through H6
            tag_name = f"h{level}"
            tags = soup.find_all(tag_name)
            header_texts = []

            for tag in tags:
                text = tag.get_text(strip=True)
                if text:
                    header_texts.append(text)

            headers[tag_name] = header_texts

    except Exception:
        logger.exception("Error extracting all headers")
        return {}
    else:
        return headers


def extract_links(html: str) -> list[dict[str, str]]:
    """Extract all links from HTML content.

    Args:
        html: HTML content as string

    Returns:
        List of dictionaries with 'url' and 'text' keys
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        links = []

        for link in soup.find_all("a", href=True):
            url = link["href"].strip()
            text = link.get_text(strip=True)
            if url:
                links.append({"url": url, "text": text or ""})

    except Exception:
        logger.exception("Error extracting links")
        return []
    else:
        return links


def extract_images(html: str) -> list[dict[str, str]]:
    """Extract all images from HTML content.

    Args:
        html: HTML content as string

    Returns:
        List of dictionaries with 'src', 'alt', and 'title' keys
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        images = []

        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            alt = img.get("alt", "").strip()
            title = img.get("title", "").strip()

            if src:
                images.append({"src": src, "alt": alt, "title": title})

    except Exception:
        logger.exception("Error extracting images")
        return []
    else:
        return images
