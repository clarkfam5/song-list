import re

CREDIT_PATTERN = re.compile(
    r'[\"“]([^\"”]{2,100})[\"”]\s+by\s+([^.\n,]{2,80})',
    re.IGNORECASE,
)


def extract_song_artist(description):
    """Return (song_title, artist) parsed from a video description's
    credit line, or None if no clear credit is found."""
    if not description:
        return None
    match = CREDIT_PATTERN.search(description)
    if not match:
        return None
    song = match.group(1).strip()
    artist = match.group(2).strip().rstrip('.').strip()
    if not song or not artist:
        return None
    return song, artist
