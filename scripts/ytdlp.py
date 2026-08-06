import json
import subprocess


def list_channel_videos(channel_url):
    """Return [{id, title, view_count, duration, url}] for every video
    on the channel's Videos tab (excludes Shorts, which live in a
    separate feed). One network call regardless of channel size."""
    videos_url = channel_url.rstrip('/') + '/videos'
    result = subprocess.run(
        ['yt-dlp', '--flat-playlist', '-J', videos_url],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    videos = []
    for entry in data.get('entries', []):
        if not entry:
            continue
        videos.append({
            'id': entry['id'],
            'title': entry.get('title', ''),
            'view_count': entry.get('view_count') or 0,
            'duration': entry.get('duration') or 0,
            'url': f"https://www.youtube.com/watch?v={entry['id']}",
        })
    return videos


def get_video_details(video_id):
    """Return {title, description, upload_date, view_count} for one
    video, fetched fresh (flat listing above doesn't include description)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    result = subprocess.run(
        ['yt-dlp', '--skip-download', '-J', url],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    return {
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'upload_date': data.get('upload_date', ''),
        'view_count': data.get('view_count') or 0,
    }
