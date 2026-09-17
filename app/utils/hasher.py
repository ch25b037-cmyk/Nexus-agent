import hashlib
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Strips query parameters, anchors, and trailing slashes so:
    'https://site.com/jobs/dev-1?utm_source=twitter#' -> 'https://site.com/jobs/dev-1'
    """
    parsed = urlparse(url)
    # Rebuild URL with only scheme, netloc, and path
    clean_path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), clean_path, "", "", ""))


def generate_content_hash(text: str) -> str:
    """
    Produces a fixed 64-character SHA-256 hash for database indexing.
    """
    normalized_text = " ".join(text.lower().split())
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()