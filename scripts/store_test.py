import os
import tempfile
import unittest

from store import (
    load_json, save_json, upload_date_to_iso, thumbnail_url,
    classify_new_video,
)

FLAT_ENTRY = {
    'id': 'abc123', 'title': 'A Cover', 'view_count': 500,
    'duration': 180, 'url': 'https://www.youtube.com/watch?v=abc123',
}
DETAILS = {
    'title': 'A Cover', 'description': '"A Song" by An Artist.',
    'upload_date': '20240828', 'view_count': 500,
}
SHORT_ENTRY = dict(FLAT_ENTRY, duration=45)


class HelpersTest(unittest.TestCase):
    def test_upload_date_to_iso(self):
        self.assertEqual(upload_date_to_iso('20240828'), '2024-08-28')

    def test_thumbnail_url(self):
        self.assertEqual(
            thumbnail_url('abc123'),
            'https://img.youtube.com/vi/abc123/mqdefault.jpg',
        )

    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.json')
            self.assertEqual(load_json(path, []), [])
            save_json(path, [{'a': 1}])
            self.assertEqual(load_json(path, []), [{'a': 1}])


class ClassifyNewVideoTest(unittest.TestCase):
    def test_short_is_excluded(self):
        bucket, entry = classify_new_video(SHORT_ENTRY, DETAILS, ('A Song', 'An Artist'))
        self.assertEqual(bucket, 'short')
        self.assertIsNone(entry)

    def test_matched_credit_is_a_cover(self):
        bucket, entry = classify_new_video(FLAT_ENTRY, DETAILS, ('A Song', 'An Artist'))
        self.assertEqual(bucket, 'cover')
        self.assertEqual(entry, {
            'id': 'abc123', 'date': '2024-08-28', 'views': 500,
            'thumbnail': 'https://img.youtube.com/vi/abc123/mqdefault.jpg',
            'url': 'https://www.youtube.com/watch?v=abc123',
            'song': 'A Song', 'artist': 'An Artist',
        })

    def test_no_credit_is_pending(self):
        bucket, entry = classify_new_video(FLAT_ENTRY, DETAILS, None)
        self.assertEqual(bucket, 'pending')
        self.assertEqual(entry, {
            'id': 'abc123', 'date': '2024-08-28', 'views': 500,
            'thumbnail': 'https://img.youtube.com/vi/abc123/mqdefault.jpg',
            'url': 'https://www.youtube.com/watch?v=abc123',
            'title': 'A Cover',
        })


if __name__ == '__main__':
    unittest.main()
