import re

# Stops at a comma by default: most trailing asides after the artist name
# ("by Bob Seger, written by Rodney Crowell") are correctly excluded this
# way. The exception is a "favorite" filler phrase before the real name
# (see FAVORITE_FILLER / CREDIT_PATTERN_FULL below), where stopping at the
# comma would cut off the name itself.
CREDIT_PATTERN = re.compile(
    r'[\"“]([^\"”]{2,100})[\"”]\s+by\s+([^.\n,]{2,80})',
    re.IGNORECASE,
)
# Same, but doesn't stop at commas — used only to recover the real name
# when CREDIT_PATTERN's capture turned out to be just filler.
CREDIT_PATTERN_FULL = re.compile(
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

# A "one of our favorites" / "our favorite EVER" style aside sometimes
# comes BEFORE the real artist name (e.g. "by one of our favorites, Chris
# Stapleton", "by one of our favorite bands THE WHO!"). FAVORITE_FILLER
# matches when CREDIT_PATTERN's comma-stopped capture is *entirely* such
# a phrase (meaning the comma cut off the real name right after it);
# FAVORITE_FILLER_PREFIX then strips just the filler, leaving the name.
FAVORITE_FILLER = re.compile(
    r'^(?:one of )?our favorite[s]?(?:\s+bands?)?(?:\s+ever)?$',
    re.IGNORECASE,
)
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

    if FAVORITE_FILLER.match(artist):
        full_matches = list(CREDIT_PATTERN_FULL.finditer(description))
        if full_matches:
            artist = full_matches[-1].group(2).strip().rstrip('.!').strip()

    artist = FAVORITE_FILLER_PREFIX.sub('', artist, count=1)
    cutoff = ARTIST_TRAILING_CUTOFF.search(artist)
    if cutoff:
        artist = artist[:cutoff.start()].strip()
    if not song or not artist:
        return None
    return song, artist
