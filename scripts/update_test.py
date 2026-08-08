import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from update import run

FLAT_VIDEOS = [
    {'id': 'seen1', 'title': 'Old Cover', 'view_count': 999, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=seen1'},
    {'id': 'new1', 'title': 'New Cover', 'view_count': 10, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=new1'},
    {'id': 'new2', 'title': 'New Vlog', 'view_count': 5, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=new2'},
]

DETAILS_BY_ID = {
    'seen1': {'title': 'Old Cover', 'description': '', 'upload_date': '20200101', 'view_count': 1234},
    'new1': {'title': 'New Cover', 'description': '"A Song" by An Artist.',
             'upload_date': '20260101', 'view_count': 10},
    'new2': {'title': 'New Vlog', 'description': 'Just us hanging out today!',
             'upload_date': '20260102', 'view_count': 5},
}


class RunTest(unittest.TestCase):
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_classifies_new_videos_and_leaves_existing_covers_untouched(self, mock_list, mock_details):
        mock_list.return_value = FLAT_VIDEOS
        mock_details.side_effect = lambda vid: DETAILS_BY_ID[vid]

        with tempfile.TemporaryDirectory() as tmp:
            covers_path = os.path.join(tmp, 'covers.json')
            with open(covers_path, 'w') as f:
                json.dump([{'id': 'seen1', 'song': 'Old', 'artist': 'X',
                            'date': '2020-01-01', 'views': 1, 'thumbnail': '',
                            'url': ''}], f)
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            run(data_dir=tmp)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            pending = json.load(open(os.path.join(tmp, 'pending.json')))
            state = json.load(open(os.path.join(tmp, 'state.json')))

            # Existing covers get their view count refreshed too, not left stale.
            self.assertEqual(covers[0]['views'], 1234)
            self.assertEqual([c['id'] for c in covers if c['id'] != 'seen1'], ['new1'])
            self.assertEqual(covers[1]['views'], 10)  # from get_video_details
            self.assertEqual([p['id'] for p in pending], ['new2'])
            self.assertEqual(sorted(state['processedIds']), ['new1', 'new2', 'seen1'])

    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_refreshes_view_counts_for_existing_covers(self, mock_list, mock_details):
        mock_list.return_value = []
        mock_details.return_value = {'title': 'Old Cover', 'description': '',
                                      'upload_date': '20200101', 'view_count': 4242}

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'covers.json'), 'w') as f:
                json.dump([{'id': 'seen1', 'song': 'Old', 'artist': 'X',
                            'date': '2020-01-01', 'views': 1, 'thumbnail': '',
                            'url': ''}], f)
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            run(data_dir=tmp)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            self.assertEqual(covers[0]['views'], 4242)
            mock_details.assert_called_once_with('seen1')

    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_refresh_keeps_existing_views_if_video_now_unavailable(self, mock_list, mock_details):
        mock_list.return_value = []
        mock_details.side_effect = subprocess.CalledProcessError(1, ['yt-dlp'])

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'covers.json'), 'w') as f:
                json.dump([{'id': 'seen1', 'song': 'Old', 'artist': 'X',
                            'date': '2020-01-01', 'views': 1, 'thumbnail': '',
                            'url': ''}], f)
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            run(data_dir=tmp)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            self.assertEqual(covers[0]['views'], 1)

    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_already_processed_ids_are_skipped(self, mock_list, mock_details):
        mock_list.return_value = FLAT_VIDEOS

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1', 'new1', 'new2']}, f)

            run(data_dir=tmp)

            mock_details.assert_not_called()

    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_unavailable_video_is_skipped_not_fatal(self, mock_list, mock_details):
        mock_list.return_value = FLAT_VIDEOS

        def side_effect(vid):
            if vid == 'new1':
                raise subprocess.CalledProcessError(1, ['yt-dlp'])
            return DETAILS_BY_ID[vid]

        mock_details.side_effect = side_effect

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            run(data_dir=tmp)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            pending = json.load(open(os.path.join(tmp, 'pending.json')))
            state = json.load(open(os.path.join(tmp, 'state.json')))

            self.assertEqual(covers, [])  # new1 failed, never classified
            self.assertEqual([p['id'] for p in pending], ['new2'])
            self.assertEqual(sorted(state['processedIds']), ['new1', 'new2', 'seen1'])


if __name__ == '__main__':
    unittest.main()
