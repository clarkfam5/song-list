import re

CREDIT_PATTERN = re.compile(
    r'[\"“]([^\"”]{2,100})[\"”]\s+by\s+([^.\n]{2,80})',
    re.IGNORECASE,
)

# Trailing clauses that sometimes follow the artist name with no comma or
# period before them (e.g. "by Mountain LIVE from Dollywood's Harvest
# Festival", "by Tom Petty and the Heartbreakers (our favorite forever)"),
# so they aren't naturally excluded by CREDIT_PATTERN's stop characters.
ARTIST_TRAILING_CUTOFF = re.compile(
    r'\s+(?:LIVE\b|for our\b|for the\b|from our\b|from the\b)|\s*\(',
)

# The opposite problem: a "one of our favorites" / "our favorite EVER"
# style aside sometimes comes BEFORE the real artist name (e.g. "by one
# of our favorites, Chris Stapleton", "by one of our favorite bands THE
# WHO!"), usually but not always followed by a comma. CREDIT_PATTERN no
# longer stops at commas (see above), so this must be stripped from the
# front of the captured group, leaving whatever name follows it.
FAVORITE_FILLER_PREFIX = re.compile(
    r'^(?:one of )?our favorite[s]?(?:\s+bands?)?(?:\s+ever)?,?\s+',
    re.IGNORECASE,
)


def extract_song_artist(description):
    """Return (song_title, artist) parsed from a video description's
    credit line, or None if no clear credit is found. When a
    description mentions more than one song in quotes (e.g. a passing
    reference to an earlier cover), the credit nearest the end of the
    description is the actual one for this video, so the last match
    wins rather than the first."""
    if not description:
        return None
    matches = list(CREDIT_PATTERN.finditer(description))
    if not matches:
        return None
    match = matches[-1]
    song = match.group(1).strip()
    artist = match.group(2).strip().rstrip('.!').strip()
    artist = FAVORITE_FILLER_PREFIX.sub('', artist, count=1)
    cutoff = ARTIST_TRAILING_CUTOFF.search(artist)
    if cutoff:
        artist = artist[:cutoff.start()].strip()
    if not song or not artist:
        return None
    return song, artist
