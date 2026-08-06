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
# Real descriptions from the channel (found during a full-catalog audit)
# where trailing text after the artist name has no comma/period before
# it, so the artist capture must be cut off explicitly rather than
# relying on punctuation.
FIXTURE_ANNIVERSARY = (
    'This is Colt Clark and the Quarantine Kids playing, '
    '“Handle With Care” by the Traveling Wilburys for our 6-year anniversary. 😊'
)
FIXTURE_LIVE_SHOW = (
    'This is Colt Clark and the Quarantine Kids playing, '
    '“Mississippi Queen” by Mountain LIVE from Dollywood’s Harvest Festival.'
)
FIXTURE_PARENTHETICAL = (
    'This is Colt Clark and the Quarantine Kids playing, '
    '“American Girl” by Tom Petty and the Heartbreakers (our favorite forever).'
)
# Real descriptions where a "one of our favorites" / "our favorite EVER"
# style aside comes BEFORE the actual artist name, separated by a comma
# (or, in the THE_WHO case, no punctuation at all) — the opposite problem
# from the trailing-clause cases above: the real name is what's left
# over, not what's captured first.
FIXTURE_FAVORITE_COMMA = (
    'This is Colt Clark and the Quarantine Kids playing, '
    '“Hard Livin’” by one of our favorites, Chris Stapleton.'
)
FIXTURE_FAVORITE_EVER = (
    'This is Colt Clark and the Quarantine Kids playing, '
    '“Free Fallin’” by our favorite EVER, Tom Petty.'
)
FIXTURE_FAVORITE_BAND_NO_COMMA = (
    'This is Colt Clark and the Quarantine Kids playing '
    '“Pinball Wizard” by one of our favorite bands THE WHO!'
)


class ExtractSongArtistTest(unittest.TestCase):
    def test_strips_leading_favorite_filler_before_a_comma(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_FAVORITE_COMMA),
            ("Hard Livin’", "Chris Stapleton"),
        )

    def test_strips_leading_favorite_ever_filler(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_FAVORITE_EVER),
            ("Free Fallin’", "Tom Petty"),
        )

    def test_strips_leading_favorite_bands_filler_with_no_comma(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_FAVORITE_BAND_NO_COMMA),
            ("Pinball Wizard", "THE WHO"),
        )

    def test_trims_trailing_clause_with_no_punctuation_before_it(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_ANNIVERSARY),
            ("Handle With Care", "the Traveling Wilburys"),
        )

    def test_trims_trailing_live_show_clause(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_LIVE_SHOW),
            ("Mississippi Queen", "Mountain"),
        )

    def test_trims_trailing_parenthetical(self):
        self.assertEqual(
            extract_song_artist(FIXTURE_PARENTHETICAL),
            ("American Girl", "Tom Petty and the Heartbreakers"),
        )

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
