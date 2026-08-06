import os
import sys

from parse import extract_song_artist
from ytdlp import list_channel_videos, get_video_details
from store import load_json, save_json, classify_new_video
from notify import send_review_email

CHANNEL_URL = "https://www.youtube.com/@TheClarkFamilyCreative"
RECIPIENTS = ['clarkfamilyband@gmail.com', 'cashclarkemail@gmail.com']
REVIEW_PAGE_URL = "https://theclarkfamilycreative.github.io/song-list/review.html"


def run(data_dir, force_all=False, notify=True):
    covers_path = os.path.join(data_dir, 'covers.json')
    pending_path = os.path.join(data_dir, 'pending.json')
    state_path = os.path.join(data_dir, 'state.json')

    covers = load_json(covers_path, [])
    pending = load_json(pending_path, [])
    state = load_json(state_path, {'processedIds': []})
    processed = set(state['processedIds'])

    flat_videos = list_channel_videos(CHANNEL_URL)
    view_counts = {v['id']: v['view_count'] for v in flat_videos}
    for cover in covers:
        if cover['id'] in view_counts:
            cover['views'] = view_counts[cover['id']]

    new_pending = []
    for video in flat_videos:
        if video['id'] in processed and not force_all:
            continue
        details = get_video_details(video['id'])
        song_artist = extract_song_artist(details['description'])
        bucket, entry = classify_new_video(video, details, song_artist)
        processed.add(video['id'])
        if bucket == 'cover':
            covers.append(entry)
        elif bucket == 'pending':
            pending.append(entry)
            new_pending.append(entry)

    save_json(covers_path, covers)
    save_json(pending_path, pending)
    save_json(state_path, {'processedIds': sorted(processed)})

    if notify and new_pending:
        send_review_email(
            new_pending, RECIPIENTS,
            os.environ['SMTP_USER'], os.environ['SMTP_PASS'],
            REVIEW_PAGE_URL,
        )


if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    force_all = '--all' in sys.argv
    run(data_dir=data_dir, force_all=force_all, notify=not force_all)
