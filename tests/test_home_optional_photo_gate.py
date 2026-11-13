"""Fail-closed photo gate: unreviewed optional JPEG angles must not hit the live site."""
import unittest
from pathlib import Path
from scripts.build_home_auction_media import download_one

class OptionalPhotoGate(unittest.TestCase):
    def test_optional_angles_do_not_attempt_remote_download(self):
        path = Path("assets/auction/home/test-private-remote-angle-photo-2.jpg")
        rel, image = download_one((path, "https://example.invalid/never-requested.jpg", False))
        self.assertEqual(rel, path)
        self.assertIsNone(image, "Unreviewed optional images must not be published")

if __name__ == "__main__":
    unittest.main()
