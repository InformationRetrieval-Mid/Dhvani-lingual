"""URL Normalization and Canonicalization."""

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_url(raw_url: str) -> str:
    """Normalize URL by stripping tracking parameters, normalizing scheme,

    resolving AMP paths, and stripping trailing slashes.
    """
    if not raw_url:
        return ""
    # Normalize scheme & lower host
    parsed = urlparse(raw_url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()

    # Drop tracking query params
    clean_params = {}
    if parsed.query:
        for k, v in parse_qs(parsed.query).items():
            if not k.startswith("utm_") and k not in {"fbclid", "ref", "amp_js_v", "amp"}:
                clean_params[k] = v[0]

    query_str = urlencode(clean_params) if clean_params else ""

    # Map AMP to canonical path
    path = parsed.path
    path = re.sub(r"^/amp(/|$)", "/", path)
    path = re.sub(r"/amp/?$", "", path)
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]

    return urlunparse((scheme, netloc, path, "", query_str, ""))
