import unittest
from parse import extract_song_artist

FIXTURE_COUSINS = (
    'This is Colt Clark and the Quarantine Kids + COUSINS singing, '
    '“You’ve Got a Friend in Me” by Randy Newman.'
)
FIXTURE_SWIMMING = (
    'This is Colt Clark and The Quarantine Kids playing '
    '"The Swimming Song" by Loudon Wainwright III.'
)
FIXTURE_VLOG = (
    'Hey guys! We had so much fun filming this vlog with the whole '
    'family at the beach today.'
)
FIXTURE_MULTIPLE_MENTIONS = (
    'Last month we covered "Landslide" by Fleetwood Mac and loved it. '
    'This week, Colt Clark and the Quarantine Kids are playing '
    '"Ripple" by Grateful Dead.'
)


class ExtractSongArtistTest(unittest.TestCase):
    def test_uses_the_last_credit_when_multiple_are_mentioned(self):
        # The actual credit for the video is always the one nearest the
        # end of the description; earlier passing mentions of other
        # songs must not win.
        self.assertEqual(
            extract_song_artist(FIXTURE_MULTIPLE_MENTIONS),
            ("Ripple", "Grateful Dead"),
        )

    def test_curly_quotes(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_COUSINS),
            ("You’ve Got a Friend in Me", "Randy Newman"),
        )

    def test_straight_quotes(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_SWIMMING),
            ("The Swimming Song", "Loudon Wainwright III"),
        )

    def test_no_credit_returns_none(self):
        self.assertIsNone(extract_song_artist(FIXTURE_VLOG))

    def test_empty_description_returns_none(self):
        self.assertIsNone(extract_song_artist(""))


if __name__ == '__main__':
    unittest.main()
