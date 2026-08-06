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

    def test_inside_the_videos_is_excluded_even_with_a_credit_match(self):
        # "Inside the Videos" episodes discuss an older cover, so their
        # description often contains that old cover's "X by Y" credit
        # line, which would otherwise false-positive as this video's own
        # credit. They must be excluded regardless of what parse.py found.
        details = dict(DETAILS, title='Inside the Videos: "Downtown Train"')
        bucket, entry = classify_new_video(FLAT_ENTRY, details, ('Downtown Train', 'Tom Waits'))
        self.assertEqual(bucket, 'excluded')
        self.assertIsNone(entry)

    def test_inside_the_videos_match_is_case_insensitive(self):
        details = dict(DETAILS, title='inside the videos: a look back')
        bucket, entry = classify_new_video(FLAT_ENTRY, details, None)
        self.assertEqual(bucket, 'excluded')
        self.assertIsNone(entry)

    def test_original_song_is_excluded_even_with_a_credit_match(self):
        # The channel occasionally posts original compositions, and
        # credits themselves as the "artist" in the description (e.g.
        # "playing 'Bad Man in a Good Suit' by Colt Clark and The
        # Quarantine Kids"), which reads exactly like a real cover
        # credit. The "ORIGINAL SONG" title marker is what distinguishes
        # these from an actual cover.
        details = dict(DETAILS, title='Colt Clark and the Quarantine Kids play an ORIGINAL SONG, "Bad Man in a Good Suit"')
        bucket, entry = classify_new_video(FLAT_ENTRY, details, ('Bad Man in a Good Suit', 'Colt Clark and The Quarantine Kids'))
        self.assertEqual(bucket, 'excluded')
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
