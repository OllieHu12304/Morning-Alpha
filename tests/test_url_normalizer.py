"""測試新聞 URL 的保守正規化規則。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from url_normalizer import normalize_url  # noqa: E402


class UrlNormalizerTests(unittest.TestCase):
    def test_normalize_url_removes_common_tracking_information(self):
        url = (
            "HTTPS://WWW.TechNews.TW:443/article/"
            "?utm_source=facebook&article_id=123#comments"
        )

        result = normalize_url(url)

        self.assertEqual(
            result,
            "https://technews.tw/article/?article_id=123",
        )

    def test_normalize_url_removes_tracking_names_case_insensitively(self):
        url = (
            "https://example.com/news"
            "?UTM_MEDIUM=email&fbclid=abc&GCLID=def&mc_cid=ghi"
        )

        self.assertEqual(normalize_url(url), "https://example.com/news")

    def test_normalize_url_preserves_and_sorts_meaningful_parameters(self):
        url = "https://example.com/news?z=2&a=1&a=0"

        self.assertEqual(
            normalize_url(url),
            "https://example.com/news?a=0&a=1&z=2",
        )

    def test_normalize_url_preserves_path_and_trailing_slash(self):
        self.assertEqual(
            normalize_url("https://example.com/news/"),
            "https://example.com/news/",
        )

    def test_normalize_url_preserves_non_default_port(self):
        self.assertEqual(
            normalize_url("https://example.com:8443/news"),
            "https://example.com:8443/news",
        )

    def test_normalize_url_removes_default_http_port(self):
        self.assertEqual(
            normalize_url("http://example.com:80/news"),
            "http://example.com/news",
        )

    def test_normalize_url_rejects_unsupported_scheme(self):
        with self.assertRaisesRegex(ValueError, "http"):
            normalize_url("ftp://example.com/news")

    def test_normalize_url_rejects_missing_hostname(self):
        with self.assertRaisesRegex(ValueError, "hostname"):
            normalize_url("https:///news")


if __name__ == "__main__":
    unittest.main()
