import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

FAKE_SMTP_ENV = {'SMTP_USER': 'bot@example.com', 'SMTP_PASS': 'app-password'}

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
    'new1': {'title': 'New Cover', 'description': '"A Song" by An Artist.',
             'upload_date': '20260101', 'view_count': 10},
    'new2': {'title': 'New Vlog', 'description': 'Just us hanging out today!',
             'upload_date': '20260102', 'view_count': 5},
}


class RunTest(unittest.TestCase):
    @patch('update.send_review_email')
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_classifies_new_videos_and_refreshes_views(self, mock_list, mock_details, mock_notify):
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

            with patch.dict(os.environ, FAKE_SMTP_ENV):
                run(data_dir=tmp, notify=True)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            pending = json.load(open(os.path.join(tmp, 'pending.json')))
            state = json.load(open(os.path.join(tmp, 'state.json')))

            self.assertEqual(covers[0]['views'], 999)  # refreshed
            self.assertEqual([c['id'] for c in covers if c['id'] != 'seen1'], ['new1'])
            self.assertEqual([p['id'] for p in pending], ['new2'])
            self.assertEqual(sorted(state['processedIds']), ['new1', 'new2', 'seen1'])
            mock_notify.assert_called_once()

    @patch('update.send_review_email')
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_already_processed_ids_are_skipped(self, mock_list, mock_details, mock_notify):
        mock_list.return_value = FLAT_VIDEOS

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1', 'new1', 'new2']}, f)

            run(data_dir=tmp, notify=True)

            mock_details.assert_not_called()
            mock_notify.assert_not_called()

    @patch('update.send_review_email')
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_unavailable_video_is_skipped_not_fatal(self, mock_list, mock_details, mock_notify):
        mock_list.return_value = FLAT_VIDEOS

        def side_effect(vid):
            if vid == 'new1':
                raise subprocess.CalledProcessError(1, ['yt-dlp'])
            return DETAILS_BY_ID[vid]

        mock_details.side_effect = side_effect

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            with patch.dict(os.environ, FAKE_SMTP_ENV):
                run(data_dir=tmp, notify=True)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            pending = json.load(open(os.path.join(tmp, 'pending.json')))
            state = json.load(open(os.path.join(tmp, 'state.json')))

            self.assertEqual(covers, [])  # new1 failed, never classified
            self.assertEqual([p['id'] for p in pending], ['new2'])
            self.assertEqual(sorted(state['processedIds']), ['new1', 'new2', 'seen1'])


if __name__ == '__main__':
    unittest.main()
