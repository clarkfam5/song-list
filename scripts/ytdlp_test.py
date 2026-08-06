import json
import unittest
from unittest.mock import patch, MagicMock

from ytdlp import list_channel_videos, get_video_details

FLAT_LISTING_JSON = json.dumps({
    "entries": [
        {"id": "abc123", "title": "A Cover", "view_count": 500, "duration": 180},
        None,  # yt-dlp can emit null entries for unavailable videos
    ]
})

VIDEO_DETAILS_JSON = json.dumps({
    "title": "A Cover",
    "description": '"A Song" by An Artist.',
    "upload_date": "20240828",
    "view_count": 500,
})


class ListChannelVideosTest(unittest.TestCase):
    @patch('ytdlp.subprocess.run')
    def test_parses_flat_listing_and_skips_nulls(self, mock_run):
        mock_run.return_value = MagicMock(stdout=FLAT_LISTING_JSON)
        videos = list_channel_videos("https://www.youtube.com/@Example")
        self.assertEqual(videos, [{
            'id': 'abc123', 'title': 'A Cover', 'view_count': 500,
            'duration': 180, 'url': 'https://www.youtube.com/watch?v=abc123',
        }])
        args = mock_run.call_args.args[0]
        self.assertIn('--flat-playlist', args)
        self.assertTrue(args[-1].endswith('/videos'))


class GetVideoDetailsTest(unittest.TestCase):
    @patch('ytdlp.subprocess.run')
    def test_parses_video_details(self, mock_run):
        mock_run.return_value = MagicMock(stdout=VIDEO_DETAILS_JSON)
        details = get_video_details("abc123")
        self.assertEqual(details, {
            'title': 'A Cover', 'description': '"A Song" by An Artist.',
            'upload_date': '20240828', 'view_count': 500,
        })


if __name__ == '__main__':
    unittest.main()
