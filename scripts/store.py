import json
import os

SHORT_MAX_SECONDS = 60


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
    (bucket, entry): bucket is "short" (entry=None, dropped),
    "cover" (confident match), or "pending" (needs human review)."""
    if flat_entry['duration'] and flat_entry['duration'] <= SHORT_MAX_SECONDS:
        return 'short', None

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
