from typing import Any


def determine_html_url(urls: list[dict[str, Any]]) -> str | None:
    for url in urls:
        if url.get("mediaType") == "text/html":
            if url.get("href"):
                return url.get("href")
    for url in urls:
        if url.get("href"):
            return url.get("href")
    return None
