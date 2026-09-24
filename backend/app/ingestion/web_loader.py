import re
import ipaddress
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from exa_py import Exa

from backend.app.config import EXA_API_KEY, MAX_SIMILAR_URLS


class WebsiteFetchError(Exception):
    pass


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host or host == "localhost":
            return False
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False


def _fetch_with_exa(url: str, discover_similar: bool = False) -> list[dict]:
    client = Exa(api_key=EXA_API_KEY)

    primary = client.get_contents(urls=[url], text={"max_characters": 1_000_000})
    pages = [{"text": r.text, "url": r.url, "title": r.title} for r in primary.results]

    if discover_similar:
        similar = client.search(query=url, type="fast", num_results=MAX_SIMILAR_URLS)
        similar_urls = [r.url for r in similar.results if r.url != url]
        if similar_urls:
            extra = client.get_contents(urls=similar_urls, text={"max_characters": 1_000_000})
            pages += [{"text": r.text, "url": r.url, "title": r.title} for r in extra.results]

    if not pages or not any(p["text"].strip() for p in pages):
        raise WebsiteFetchError("Exa returned no usable content")

    return pages


def _fetch_with_requests(url: str) -> list[dict]:
    response = requests.get(url, timeout=10, headers={"User-Agent": "AgentFactoryBot/1.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = re.sub(r"\s+", " ", soup.get_text()).strip()
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    if not text:
        raise WebsiteFetchError("No text content found on page")

    return [{"text": text, "url": url, "title": title}]


def fetch_website_content(url: str, use_exa: bool = True, discover_similar: bool = True) -> list[dict]:
    if not _is_safe_url(url):
        raise WebsiteFetchError(f"Refusing to fetch unsafe URL: {url}")

    if use_exa and EXA_API_KEY:
        try:
            return _fetch_with_exa(url, discover_similar=discover_similar)
        except Exception as e:
            print(f"Exa fetch failed for {url}, falling back to plain HTTP: {e}")

    return _fetch_with_requests(url)