"""測試 canonical URL 的 SHA-256 hash。"""

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

from canonical_url_hash import create_canonical_url_hash  # noqa: E402


class CanonicalUrlHashTests(unittest.TestCase):
    def test_create_hash_returns_stable_sha256(self):
        canonical_url = "https://technews.tw/example/"

        first_hash = create_canonical_url_hash(canonical_url)
        second_hash = create_canonical_url_hash(canonical_url)

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_different_urls_have_different_hashes(self):
        first_hash = create_canonical_url_hash("https://example.com/one")
        second_hash = create_canonical_url_hash("https://example.com/two")

        self.assertNotEqual(first_hash, second_hash)

    def test_create_hash_rejects_empty_url(self):
        with self.assertRaisesRegex(ValueError, "非空白"):
            create_canonical_url_hash("")

        with self.assertRaisesRegex(ValueError, "非空白"):
            create_canonical_url_hash("   ")


if __name__ == "__main__":
    unittest.main()
