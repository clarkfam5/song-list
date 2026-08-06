import json
import os

SHORT_MAX_SECONDS = 60
EXCLUDED_TITLE_PREFIXES = ('inside the videos',)
EXCLUDED_TITLE_SUBSTRINGS = ('original song',)
# Individually reviewed one-offs that don't fit the one-video-one-song
# model (e.g. a compilation covering multiple songs in a single video),
# where there's no reliable general pattern to detect the case
# automatically without also misfiring on legitimate single-song videos.
EXCLUDED_VIDEO_IDS = {
    '05KH9X4eiUw',  # "DUETS" video covering 3 separate songs
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def upload_date_to_iso(upload_date):
    return f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"


def thumbnail_url(video_id):
    return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"


def classify_new_video(flat_entry, details, song_artist):
    """Build the entry for a never-before-seen video. Returns
    (bucket, entry): bucket is "short" or "excluded" (entry=None,
    dropped), "cover" (confident match), or "pending" (needs human
    review)."""
    if flat_entry['duration'] and flat_entry['duration'] <= SHORT_MAX_SECONDS:
        return 'short', None
    if flat_entry['id'] in EXCLUDED_VIDEO_IDS:
        return 'excluded', None

    title_lower = details['title'].strip().lower()
    if title_lower.startswith(EXCLUDED_TITLE_PREFIXES):
        # These reference an older cover's own "X by Y" credit in their
        # description, which would otherwise false-positive as this
        # video's own credit, so they're excluded before that check runs.
        return 'excluded', None
    if any(s in title_lower for s in EXCLUDED_TITLE_SUBSTRINGS):
        # Original compositions credit the family itself as "artist" in
        # the description, which reads exactly like a real cover credit.
        return 'excluded', None

    base = {
        'id': flat_entry['id'],
        'date': upload_date_to_iso(details['upload_date']),
        'views': details['view_count'],
        'thumbnail': thumbnail_url(flat_entry['id']),
        'url': flat_entry['url'],
    }

    if song_artist is None:
        base['title'] = details['title']
        return 'pending', base

    song, artist = song_artist
    base['song'] = song
    base['artist'] = artist
    return 'cover', base
