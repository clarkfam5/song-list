import unittest
from unittest.mock import patch, MagicMock

from notify import build_review_email, send_review_email

PENDING = [
    {'id': 'abc123', 'title': 'Some Vlog', 'date': '2026-08-01'},
    {'id': 'def456', 'title': 'Unclear Cover', 'date': '2026-08-02'},
]


class BuildReviewEmailTest(unittest.TestCase):
    def test_body_lists_each_item_and_link(self):
        body = build_review_email(PENDING, 'https://example.com/review.html')
        self.assertIn('2 video(s)', body)
        self.assertIn('Some Vlog (2026-08-01)', body)
        self.assertIn('Unclear Cover (2026-08-02)', body)
        self.assertIn('https://example.com/review.html', body)


class SendReviewEmailTest(unittest.TestCase):
    @patch('notify.smtplib.SMTP_SSL')
    def test_sends_to_all_recipients(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_review_email(
            PENDING, ['a@example.com', 'b@example.com'],
            'bot@example.com', 'app-password',
            'https://example.com/review.html',
        )

        mock_server.login.assert_called_once_with('bot@example.com', 'app-password')
        sendmail_args = mock_server.sendmail.call_args.args
        self.assertEqual(sendmail_args[0], 'bot@example.com')
        self.assertEqual(sendmail_args[1], ['a@example.com', 'b@example.com'])
        self.assertIn('Some Vlog', sendmail_args[2])


if __name__ == '__main__':
    unittest.main()
