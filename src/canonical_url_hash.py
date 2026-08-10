"""建立 canonical URL 使用的穩定 SHA-256 hash。"""

import hashlib


def create_canonical_url_hash(canonical_url):
    """將非空白 canonical URL 轉成 64 字元 SHA-256。"""
    if not isinstance(canonical_url, str) or not canonical_url.strip():
        raise ValueError("Canonical URL 必須是非空白文字。")

    encoded_url = canonical_url.encode("utf-8")
    return hashlib.sha256(encoded_url).hexdigest()
