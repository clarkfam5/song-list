import os
import subprocess
import sys
import time

from parse import extract_song_artist
from ytdlp import list_channel_videos, get_video_details
from store import load_json, save_json, classify_new_video
from notify import send_review_email

CHANNEL_URL = "https://www.youtube.com/@TheClarkFamilyCreative"
RECIPIENTS = ['clarkfamilyband@gmail.com', 'cashclarkemail@gmail.com']
REVIEW_PAGE_URL = "https://theclarkfamilycreative.github.io/song-list/review.html"
CHECKPOINT_EVERY = 25


def run(data_dir, backfill=False, notify=True):
    """backfill enables pacing/checkpointing/suppressed-notification for
    processing a large batch of videos in one run. It does not change
    which videos count as "new" — already-processed IDs are always
    skipped, so re-running after an interruption resumes rather than
    reprocessing everything."""
    covers_path = os.path.join(data_dir, 'covers.json')
    pending_path = os.path.join(data_dir, 'pending.json')
    state_path = os.path.join(data_dir, 'state.json')

    covers = load_json(covers_path, [])
    pending = load_json(pending_path, [])
    state = load_json(state_path, {'processedIds': []})
    processed = set(state['processedIds'])

    def checkpoint():
        save_json(covers_path, covers)
        save_json(pending_path, pending)
        save_json(state_path, {'processedIds': sorted(processed)})

    flat_videos = list_channel_videos(CHANNEL_URL)
    view_counts = {v['id']: v['view_count'] for v in flat_videos}
    for cover in covers:
        if cover['id'] in view_counts:
            cover['views'] = view_counts[cover['id']]

    new_pending = []
    for i, video in enumerate(flat_videos):
        if video['id'] in processed:
            continue
        try:
            details = get_video_details(video['id'])
        except subprocess.CalledProcessError:
            processed.add(video['id'])
            print(f"Skipping unavailable video: {video['id']}")
            if backfill:
                if i % CHECKPOINT_EVERY == 0:
                    checkpoint()
                time.sleep(1)
            continue
        song_artist = extract_song_artist(details['description'])
        bucket, entry = classify_new_video(video, details, song_artist)
        processed.add(video['id'])
        if bucket == 'cover':
            covers.append(entry)
        elif bucket == 'pending':
            pending.append(entry)
            new_pending.append(entry)
        if backfill:
            if i % CHECKPOINT_EVERY == 0:
                checkpoint()
            time.sleep(1)

    checkpoint()

    if notify and new_pending:
        send_review_email(
            new_pending, RECIPIENTS,
            os.environ['SMTP_USER'], os.environ['SMTP_PASS'],
            REVIEW_PAGE_URL,
        )


if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    backfill = '--all' in sys.argv
    run(data_dir=data_dir, backfill=backfill, notify=not backfill)
