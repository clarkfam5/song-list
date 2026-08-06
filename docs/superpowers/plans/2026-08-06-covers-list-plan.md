# Clark Family Creative Covers List — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public, searchable, sortable webpage of Clark Family Creative's YouTube covers that updates itself daily, with an email-notified review step for anything the parser can't confidently classify.

**Architecture:** A static site (GitHub Pages) reads plain JSON data files committed to the repo. A daily GitHub Actions job runs a small Python pipeline (`yt-dlp` + stdlib only) that lists the channel's videos, parses new ones for song/artist from the description, and either appends them to the published data or holds them for review. A tiny Cloudflare Worker is the only piece with write credentials, so the public review page can publish edits without the family ever touching GitHub.

**Tech Stack:** Plain HTML/CSS/JS (no framework, no build step) for the site; Python stdlib + `yt-dlp` CLI for the pipeline; GitHub Actions for scheduling; Cloudflare Workers (free tier) for the review-publish endpoint; Gmail SMTP for notification email.

## Global Constraints

- Channel source: `https://www.youtube.com/@TheClarkFamilyCreative` — Videos tab only, Shorts excluded (spec §Source).
- No YouTube Data API / API key — use `yt-dlp` (validated working during design).
- No database — data lives in `data/covers.json`, `data/pending.json`, `data/state.json` in the repo.
- Zero expected dollar cost — GitHub Pages, GitHub Actions, and Cloudflare Workers free tiers only.
- Default sort is Newest→Oldest; other sorts: Oldest→Newest, Most Popular, Artist A-Z, Song Title A-Z.
- Styling: plain white background, black text — no visual polish yet (spec §Public page).
- Review email recipients: `clarkfamilyband@gmail.com` and `cashclarkemail@gmail.com`.
- No GitHub account/knowledge required for the family to review and publish held-back items.
- Write the least amount of code needed — no speculative abstraction, no unused options, no framework/build tooling.

---

## Task 1: Description parsing logic

**Files:**
- Create: `scripts/parse.py`
- Test: `scripts/parse_test.py`

**Interfaces:**
- Produces: `extract_song_artist(description: str) -> tuple[str, str] | None`

- [ ] **Step 1: Write the failing test**

```python
# scripts/parse_test.py
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


class ExtractSongArtistTest(unittest.TestCase):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m unittest parse_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'parse'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/parse.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m unittest parse_test -v`
Expected: `OK` (4 tests pass)

- [ ] **Step 5: Commit**

```bash
git add scripts/parse.py scripts/parse_test.py
git commit -m "Add description credit-line parsing"
```

---

## Task 2: yt-dlp wrapper functions

**Files:**
- Create: `scripts/ytdlp.py`
- Test: `scripts/ytdlp_test.py`

**Interfaces:**
- Consumes: none (calls `yt-dlp` binary via subprocess)
- Produces:
  - `list_channel_videos(channel_url: str) -> list[dict]` — each dict has `id`, `title`, `view_count`, `duration`, `url`
  - `get_video_details(video_id: str) -> dict` — dict has `title`, `description`, `upload_date`, `view_count`

- [ ] **Step 1: Write the failing test**

```python
# scripts/ytdlp_test.py
import json
import unittest
from unittest.mock import patch, MagicMock

from ytdlp import list_channel_videos, get_video_details

FLAT_LISTING_JSON = json.dumps({
    "entries": [
        {"id": "abc123", "title": "A Cover", "view_count": 500, "duration": 180},
        None,  # yt-dlp can emit null entries for unavailable videos
    ]
})

VIDEO_DETAILS_JSON = json.dumps({
    "title": "A Cover",
    "description": '"A Song" by An Artist.',
    "upload_date": "20240828",
    "view_count": 500,
})


class ListChannelVideosTest(unittest.TestCase):
    @patch('ytdlp.subprocess.run')
    def test_parses_flat_listing_and_skips_nulls(self, mock_run):
        mock_run.return_value = MagicMock(stdout=FLAT_LISTING_JSON)
        videos = list_channel_videos("https://www.youtube.com/@Example")
        self.assertEqual(videos, [{
            'id': 'abc123', 'title': 'A Cover', 'view_count': 500,
            'duration': 180, 'url': 'https://www.youtube.com/watch?v=abc123',
        }])
        args = mock_run.call_args.args[0]
        self.assertIn('--flat-playlist', args)
        self.assertTrue(args[-1].endswith('/videos'))


class GetVideoDetailsTest(unittest.TestCase):
    @patch('ytdlp.subprocess.run')
    def test_parses_video_details(self, mock_run):
        mock_run.return_value = MagicMock(stdout=VIDEO_DETAILS_JSON)
        details = get_video_details("abc123")
        self.assertEqual(details, {
            'title': 'A Cover', 'description': '"A Song" by An Artist.',
            'upload_date': '20240828', 'view_count': 500,
        })


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m unittest ytdlp_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ytdlp'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/ytdlp.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m unittest ytdlp_test -v`
Expected: `OK` (2 tests pass)

- [ ] **Step 5: Commit**

```bash
git add scripts/ytdlp.py scripts/ytdlp_test.py
git commit -m "Add yt-dlp wrapper for channel listing and video details"
```

---

## Task 3: Classification and data store

**Files:**
- Create: `scripts/store.py`
- Test: `scripts/store_test.py`

**Interfaces:**
- Consumes: flat-entry dicts and details dicts shaped like Task 2's outputs; `song_artist` shaped like Task 1's output
- Produces:
  - `load_json(path, default) -> Any`
  - `save_json(path, data) -> None`
  - `upload_date_to_iso(upload_date: str) -> str`
  - `thumbnail_url(video_id: str) -> str`
  - `classify_new_video(flat_entry: dict, details: dict, song_artist: tuple | None) -> tuple[str, dict | None]` — bucket is `"short"`, `"cover"`, or `"pending"`

- [ ] **Step 1: Write the failing test**

```python
# scripts/store_test.py
import os
import tempfile
import unittest

from store import (
    load_json, save_json, upload_date_to_iso, thumbnail_url,
    classify_new_video,
)

FLAT_ENTRY = {
    'id': 'abc123', 'title': 'A Cover', 'view_count': 500,
    'duration': 180, 'url': 'https://www.youtube.com/watch?v=abc123',
}
DETAILS = {
    'title': 'A Cover', 'description': '"A Song" by An Artist.',
    'upload_date': '20240828', 'view_count': 500,
}
SHORT_ENTRY = dict(FLAT_ENTRY, duration=45)


class HelpersTest(unittest.TestCase):
    def test_upload_date_to_iso(self):
        self.assertEqual(upload_date_to_iso('20240828'), '2024-08-28')

    def test_thumbnail_url(self):
        self.assertEqual(
            thumbnail_url('abc123'),
            'https://img.youtube.com/vi/abc123/mqdefault.jpg',
        )

    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.json')
            self.assertEqual(load_json(path, []), [])
            save_json(path, [{'a': 1}])
            self.assertEqual(load_json(path, []), [{'a': 1}])


class ClassifyNewVideoTest(unittest.TestCase):
    def test_short_is_excluded(self):
        bucket, entry = classify_new_video(SHORT_ENTRY, DETAILS, ('A Song', 'An Artist'))
        self.assertEqual(bucket, 'short')
        self.assertIsNone(entry)

    def test_matched_credit_is_a_cover(self):
        bucket, entry = classify_new_video(FLAT_ENTRY, DETAILS, ('A Song', 'An Artist'))
        self.assertEqual(bucket, 'cover')
        self.assertEqual(entry, {
            'id': 'abc123', 'date': '2024-08-28', 'views': 500,
            'thumbnail': 'https://img.youtube.com/vi/abc123/mqdefault.jpg',
            'url': 'https://www.youtube.com/watch?v=abc123',
            'song': 'A Song', 'artist': 'An Artist',
        })

    def test_no_credit_is_pending(self):
        bucket, entry = classify_new_video(FLAT_ENTRY, DETAILS, None)
        self.assertEqual(bucket, 'pending')
        self.assertEqual(entry, {
            'id': 'abc123', 'date': '2024-08-28', 'views': 500,
            'thumbnail': 'https://img.youtube.com/vi/abc123/mqdefault.jpg',
            'url': 'https://www.youtube.com/watch?v=abc123',
            'title': 'A Cover',
        })


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m unittest store_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'store'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/store.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m unittest store_test -v`
Expected: `OK` (6 tests pass)

- [ ] **Step 5: Commit**

```bash
git add scripts/store.py scripts/store_test.py
git commit -m "Add classification logic and JSON data store helpers"
```

---

## Task 4: Email notifier

**Files:**
- Create: `scripts/notify.py`
- Test: `scripts/notify_test.py`

**Interfaces:**
- Consumes: a list of pending entries shaped like Task 3's `"pending"` bucket entries
- Produces:
  - `build_review_email(pending_items: list[dict], review_page_url: str) -> str`
  - `send_review_email(pending_items: list[dict], recipients: list[str], smtp_user: str, smtp_pass: str, review_page_url: str) -> None`

- [ ] **Step 1: Write the failing test**

```python
# scripts/notify_test.py
import unittest
from unittest.mock import patch, MagicMock

from notify import build_review_email, send_review_email

PENDING = [
    {'id': 'abc123', 'title': 'Some Vlog', 'date': '2026-08-01'},
    {'id': 'def456', 'title': 'Unclear Cover', 'date': '2026-08-02'},
]


class BuildReviewEmailTest(unittest.TestCase):
    def test_body_lists_each_item_and_link(self):
        body = build_review_email(PENDING, 'https://example.com/review.html')
        self.assertIn('2 video(s)', body)
        self.assertIn('Some Vlog (2026-08-01)', body)
        self.assertIn('Unclear Cover (2026-08-02)', body)
        self.assertIn('https://example.com/review.html', body)


class SendReviewEmailTest(unittest.TestCase):
    @patch('notify.smtplib.SMTP_SSL')
    def test_sends_to_all_recipients(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        send_review_email(
            PENDING, ['a@example.com', 'b@example.com'],
            'bot@example.com', 'app-password',
            'https://example.com/review.html',
        )

        mock_server.login.assert_called_once_with('bot@example.com', 'app-password')
        sendmail_args = mock_server.sendmail.call_args.args
        self.assertEqual(sendmail_args[0], 'bot@example.com')
        self.assertEqual(sendmail_args[1], ['a@example.com', 'b@example.com'])
        self.assertIn('Some Vlog', sendmail_args[2])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m unittest notify_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'notify'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/notify.py
import smtplib
from email.mime.text import MIMEText


def build_review_email(pending_items, review_page_url):
    lines = [f"{len(pending_items)} video(s) need review before they go live:\n"]
    for item in pending_items:
        lines.append(f"- {item['title']} ({item['date']})")
    lines.append(f"\nReview them here: {review_page_url}")
    return "\n".join(lines)


def send_review_email(pending_items, recipients, smtp_user, smtp_pass, review_page_url):
    body = build_review_email(pending_items, review_page_url)
    msg = MIMEText(body)
    msg['Subject'] = f"Clark Family Creative: {len(pending_items)} cover(s) need review"
    msg['From'] = smtp_user
    msg['To'] = ", ".join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipients, msg.as_string())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m unittest notify_test -v`
Expected: `OK` (2 tests pass)

- [ ] **Step 5: Commit**

```bash
git add scripts/notify.py scripts/notify_test.py
git commit -m "Add review-needed email notification"
```

---

## Task 5: Main pipeline script (with backfill mode)

**Files:**
- Create: `scripts/update.py`
- Test: `scripts/update_test.py`

**Interfaces:**
- Consumes: `list_channel_videos`, `get_video_details` (Task 2), `extract_song_artist` (Task 1), `load_json`, `save_json`, `classify_new_video` (Task 3), `send_review_email` (Task 4)
- Produces: `run(data_dir: str, force_all: bool = False, notify: bool = True) -> None`

- [ ] **Step 1: Write the failing test**

```python
# scripts/update_test.py
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from update import run

FAKE_SMTP_ENV = {'SMTP_USER': 'bot@example.com', 'SMTP_PASS': 'app-password'}

FLAT_VIDEOS = [
    {'id': 'seen1', 'title': 'Old Cover', 'view_count': 999, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=seen1'},
    {'id': 'new1', 'title': 'New Cover', 'view_count': 10, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=new1'},
    {'id': 'new2', 'title': 'New Vlog', 'view_count': 5, 'duration': 200,
     'url': 'https://www.youtube.com/watch?v=new2'},
]

DETAILS_BY_ID = {
    'new1': {'title': 'New Cover', 'description': '"A Song" by An Artist.',
             'upload_date': '20260101', 'view_count': 10},
    'new2': {'title': 'New Vlog', 'description': 'Just us hanging out today!',
             'upload_date': '20260102', 'view_count': 5},
}


class RunTest(unittest.TestCase):
    @patch('update.send_review_email')
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_classifies_new_videos_and_refreshes_views(self, mock_list, mock_details, mock_notify):
        mock_list.return_value = FLAT_VIDEOS
        mock_details.side_effect = lambda vid: DETAILS_BY_ID[vid]

        with tempfile.TemporaryDirectory() as tmp:
            covers_path = os.path.join(tmp, 'covers.json')
            with open(covers_path, 'w') as f:
                json.dump([{'id': 'seen1', 'song': 'Old', 'artist': 'X',
                            'date': '2020-01-01', 'views': 1, 'thumbnail': '',
                            'url': ''}], f)
            # seen1 must be marked processed already, or the pipeline treats
            # it as new too and tries to fetch details for it.
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1']}, f)

            # send_review_email is mocked, but run() still builds its
            # arguments — including os.environ lookups — before the mock
            # intercepts the call, so the env vars must exist.
            with patch.dict(os.environ, FAKE_SMTP_ENV):
                run(data_dir=tmp, notify=True)

            covers = json.load(open(os.path.join(tmp, 'covers.json')))
            pending = json.load(open(os.path.join(tmp, 'pending.json')))
            state = json.load(open(os.path.join(tmp, 'state.json')))

            self.assertEqual(covers[0]['views'], 999)  # refreshed
            self.assertEqual([c['id'] for c in covers if c['id'] != 'seen1'], ['new1'])
            self.assertEqual([p['id'] for p in pending], ['new2'])
            self.assertEqual(sorted(state['processedIds']), ['new1', 'new2', 'seen1'])
            mock_notify.assert_called_once()

    @patch('update.send_review_email')
    @patch('update.get_video_details')
    @patch('update.list_channel_videos')
    def test_already_processed_ids_are_skipped(self, mock_list, mock_details, mock_notify):
        mock_list.return_value = FLAT_VIDEOS

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, 'state.json'), 'w') as f:
                json.dump({'processedIds': ['seen1', 'new1', 'new2']}, f)

            run(data_dir=tmp, notify=True)

            mock_details.assert_not_called()
            mock_notify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts && python -m unittest update_test -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'update'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/update.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts && python -m unittest update_test -v`
Expected: `OK` (2 tests pass)

- [ ] **Step 5: Commit**

```bash
git add scripts/update.py scripts/update_test.py
git commit -m "Add main pipeline orchestration with backfill mode"
```

---

## Task 6: Daily GitHub Actions workflow

**Files:**
- Create: `.github/workflows/update.yml`
- Create: `data/covers.json` (seed: `[]`)
- Create: `data/pending.json` (seed: `[]`)
- Create: `data/state.json` (seed: `{"processedIds": []}`)

**Interfaces:**
- Consumes: `scripts/update.py` (Task 5), repo secrets `SMTP_USER`/`SMTP_PASS`
- Produces: a scheduled job that commits data changes back to `main`

- [ ] **Step 1: Seed the data files**

```bash
mkdir -p data
echo '[]' > data/covers.json
echo '[]' > data/pending.json
echo '{"processedIds": []}' > data/state.json
```

- [ ] **Step 2: Write the workflow**

```yaml
# .github/workflows/update.yml
name: Update covers list

on:
  schedule:
    - cron: '30 21 * * *'  # 21:30 UTC ~= 5:30 PM US Eastern (drifts 1hr across DST)
  workflow_dispatch: {}

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install yt-dlp
      - run: python scripts/update.py
        env:
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
      - run: |
          git config user.name "covers-bot"
          git config user.email "actions@github.com"
          git add data/
          git diff --cached --quiet || git commit -m "Update covers list"
          git push
```

- [ ] **Step 3: Verify YAML is well-formed**

Run: `python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/update.yml'))" 2>&1 || python3 -m json.tool --help >/dev/null`

Expected: no error (if `pyyaml` isn't installed locally, skip this and rely on GitHub's own validation when the workflow file is pushed — GitHub rejects malformed workflow YAML immediately in the Actions tab).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/update.yml data/covers.json data/pending.json data/state.json
git commit -m "Add daily update workflow and seed data files"
```

*(This task has no automated test — it's verified end-to-end in Task 12 by triggering it manually via `workflow_dispatch` after deployment.)*

---

## Task 7: Public page search/sort logic

**Files:**
- Create: `assets/lib.js`
- Test: `assets/lib.test.js`

**Interfaces:**
- Consumes: array of cover objects `{id, song, artist, date, views, thumbnail, url}`
- Produces:
  - `searchCovers(covers, query) -> array`
  - `sortCovers(covers, mode) -> array` where `mode` is `'newest' | 'oldest' | 'popular' | 'artist' | 'title'`

- [ ] **Step 1: Write the failing test**

```javascript
// assets/lib.test.js
const test = require('node:test');
const assert = require('node:assert');
const { searchCovers, sortCovers } = require('./lib.js');

const COVERS = [
  { id: '1', song: 'Two of Us', artist: 'The Beatles', date: '2023-05-01', views: 100 },
  { id: '2', song: 'The Swimming Song', artist: 'Loudon Wainwright III', date: '2024-08-28', views: 300 },
  { id: '3', song: "You've Got a Friend in Me", artist: 'Randy Newman', date: '2026-07-31', views: 200 },
];

test('searchCovers matches song title, case-insensitive', () => {
  const result = searchCovers(COVERS, 'swim');
  assert.deepStrictEqual(result.map(c => c.id), ['2']);
});

test('searchCovers matches artist name', () => {
  const result = searchCovers(COVERS, 'beatles');
  assert.deepStrictEqual(result.map(c => c.id), ['1']);
});

test('searchCovers with empty query returns everything', () => {
  assert.strictEqual(searchCovers(COVERS, '').length, 3);
});

test('sortCovers newest puts latest date first', () => {
  const result = sortCovers(COVERS, 'newest');
  assert.deepStrictEqual(result.map(c => c.id), ['3', '2', '1']);
});

test('sortCovers oldest puts earliest date first', () => {
  const result = sortCovers(COVERS, 'oldest');
  assert.deepStrictEqual(result.map(c => c.id), ['1', '2', '3']);
});

test('sortCovers popular sorts by views descending', () => {
  const result = sortCovers(COVERS, 'popular');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '3', '1']);
});

test('sortCovers artist sorts alphabetically by artist', () => {
  // Loudon Wainwright III < Randy Newman < The Beatles
  const result = sortCovers(COVERS, 'artist');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '3', '1']);
});

test('sortCovers title sorts alphabetically by song', () => {
  // The Swimming Song < Two of Us < You've Got a Friend in Me
  const result = sortCovers(COVERS, 'title');
  assert.deepStrictEqual(result.map(c => c.id), ['2', '1', '3']);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test assets/lib.test.js`
Expected: FAIL — `Cannot find module './lib.js'`

- [ ] **Step 3: Write minimal implementation**

```javascript
// assets/lib.js
(function (exports) {
  function searchCovers(covers, query) {
    const q = query.trim().toLowerCase();
    if (!q) return covers;
    return covers.filter(c =>
      c.song.toLowerCase().includes(q) || c.artist.toLowerCase().includes(q)
    );
  }

  const SORTERS = {
    newest: (a, b) => b.date.localeCompare(a.date),
    oldest: (a, b) => a.date.localeCompare(b.date),
    popular: (a, b) => b.views - a.views,
    artist: (a, b) => a.artist.localeCompare(b.artist),
    title: (a, b) => a.song.localeCompare(b.song),
  };

  function sortCovers(covers, mode) {
    const sorter = SORTERS[mode] || SORTERS.newest;
    return [...covers].sort(sorter);
  }

  exports.searchCovers = searchCovers;
  exports.sortCovers = sortCovers;
})(typeof module !== 'undefined' ? module.exports : (window.CoversLib = {}));
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test assets/lib.test.js`
Expected: all 8 tests pass

- [ ] **Step 5: Commit**

```bash
git add assets/lib.js assets/lib.test.js
git commit -m "Add search and sort logic for the covers list"
```

---

## Task 8: Public page markup and wiring

**Files:**
- Create: `index.html`
- Create: `assets/app.js`
- Create: `assets/style.css`

**Interfaces:**
- Consumes: `CoversLib.searchCovers`/`CoversLib.sortCovers` (Task 7, loaded as a browser global via `<script>` tag), `data/covers.json` (Task 6's seed, populated by Task 11's backfill)

- [ ] **Step 1: Write the page**

```html
<!-- index.html -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clark Family Creative — Covers</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<h1>Clark Family Creative — Covers</h1>
<input id="search" type="text" placeholder="Search song or artist...">
<select id="sort">
  <option value="newest">Newest first</option>
  <option value="oldest">Oldest first</option>
  <option value="popular">Most popular</option>
  <option value="artist">Artist A-Z</option>
  <option value="title">Song title A-Z</option>
</select>
<div id="list"></div>
<script src="assets/lib.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
```

```css
/* assets/style.css */
body {
  background: #fff;
  color: #000;
  font-family: sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.cover {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ddd;
}
#search, #sort {
  margin: 0.5rem 0.5rem 1rem 0;
  padding: 0.4rem;
}
```

```javascript
// assets/app.js
let covers = [];

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function render() {
  const query = document.getElementById('search').value;
  const mode = document.getElementById('sort').value;
  const filtered = CoversLib.sortCovers(CoversLib.searchCovers(covers, query), mode);
  document.getElementById('list').innerHTML = filtered.map(c => `
    <div class="cover">
      <img src="${escapeHtml(c.thumbnail)}" alt="${escapeHtml(c.song)}" width="120">
      <div>
        <strong>${escapeHtml(c.song)}</strong> by ${escapeHtml(c.artist)}<br>
        <span>${escapeHtml(c.date)}</span> &middot;
        <a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">Watch</a>
      </div>
    </div>
  `).join('');
}

fetch('data/covers.json')
  .then(r => r.json())
  .then(data => { covers = data; render(); });

document.getElementById('search').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);
```

- [ ] **Step 2: Verify manually**

Run: `python3 -m http.server 8000` from the repo root, then open `http://localhost:8000/` in a browser.

Before this works you need sample data — temporarily replace `data/covers.json`'s contents with:
```json
[
  {"id": "1", "song": "Two of Us", "artist": "The Beatles", "date": "2023-05-01", "views": 100, "thumbnail": "https://img.youtube.com/vi/1/mqdefault.jpg", "url": "https://www.youtube.com/watch?v=1"},
  {"id": "2", "song": "The Swimming Song", "artist": "Loudon Wainwright III", "date": "2024-08-28", "views": 32947, "thumbnail": "https://img.youtube.com/vi/YnD6FgPIilA/mqdefault.jpg", "url": "https://www.youtube.com/watch?v=YnD6FgPIilA"}
]
```
Expected: both entries render with thumbnail, title, artist, date, and a working "Watch" link; typing "beatles" in search leaves only the first entry; switching sort to "Most popular" puts the Swimming Song first. Revert `data/covers.json` back to `[]` afterward — Task 11 populates it for real.

- [ ] **Step 3: Commit**

```bash
git add index.html assets/app.js assets/style.css
git commit -m "Add public covers page with search and sort"
```

---

## Task 9: Review-publish logic and Cloudflare Worker

**Files:**
- Create: `worker/review-logic.js`
- Test: `worker/review-logic.test.js`
- Create: `worker/publish.js`

**Interfaces:**
- Produces: `applyReviewAction(covers: array, pending: array, action: {type: 'publish'|'discard', id: string, song?: string, artist?: string}) -> {covers: array, pending: array}`

- [ ] **Step 1: Write the failing test**

```javascript
// worker/review-logic.test.js
const test = require('node:test');
const assert = require('node:assert');
const { applyReviewAction } = require('./review-logic.js');

const COVERS = [{ id: '1', song: 'Old', artist: 'X', date: '2020-01-01', views: 1, thumbnail: 't', url: 'u' }];
const PENDING = [{ id: '2', title: 'New Vlog', date: '2026-08-01', views: 5, thumbnail: 't2', url: 'u2' }];

test('publish moves item from pending to covers with the edited fields', () => {
  const result = applyReviewAction(COVERS, PENDING, { type: 'publish', id: '2', song: 'Fixed Song', artist: 'Fixed Artist' });
  assert.strictEqual(result.pending.length, 0);
  assert.strictEqual(result.covers.length, 2);
  assert.deepStrictEqual(result.covers[1], {
    id: '2', date: '2026-08-01', views: 5, thumbnail: 't2', url: 'u2',
    song: 'Fixed Song', artist: 'Fixed Artist',
  });
});

test('discard removes the item from pending without touching covers', () => {
  const result = applyReviewAction(COVERS, PENDING, { type: 'discard', id: '2' });
  assert.strictEqual(result.pending.length, 0);
  assert.deepStrictEqual(result.covers, COVERS);
});

test('unknown id throws', () => {
  assert.throws(() => applyReviewAction(COVERS, PENDING, { type: 'discard', id: 'missing' }));
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test worker/review-logic.test.js`
Expected: FAIL — `Cannot find module './review-logic.js'`

- [ ] **Step 3: Write minimal implementation**

```javascript
// worker/review-logic.js
function applyReviewAction(covers, pending, action) {
  const idx = pending.findIndex(p => p.id === action.id);
  if (idx === -1) throw new Error('pending item not found: ' + action.id);
  const item = pending[idx];
  const newPending = pending.slice(0, idx).concat(pending.slice(idx + 1));

  if (action.type === 'discard') {
    return { covers, pending: newPending };
  }

  const published = {
    id: item.id, date: item.date, views: item.views,
    thumbnail: item.thumbnail, url: item.url,
    song: action.song, artist: action.artist,
  };
  return { covers: covers.concat([published]), pending: newPending };
}

module.exports = { applyReviewAction };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test worker/review-logic.test.js`
Expected: all 3 tests pass

- [ ] **Step 5: Write the Worker entry point** *(deployed and manually verified in Task 12 — Workers run on Cloudflare's edge runtime, not Node, so this isn't covered by `node --test`)*

```javascript
// worker/publish.js
import { applyReviewAction } from './review-logic.js';

const REPO = 'REPLACE_WITH_GITHUB_USERNAME/song-list';
const BRANCH = 'main';

async function getFile(path, token) {
  const res = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}`, {
    headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'covers-worker' },
  });
  const json = await res.json();
  return { content: JSON.parse(atob(json.content)), sha: json.sha };
}

async function putFile(path, content, sha, token, message) {
  await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'covers-worker' },
    body: JSON.stringify({
      message,
      content: btoa(JSON.stringify(content, null, 2) + '\n'),
      sha,
      branch: BRANCH,
    }),
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return new Response('Not found', { status: 404 });
    if (request.headers.get('x-review-secret') !== env.REVIEW_SECRET) {
      return new Response('Unauthorized', { status: 401 });
    }
    const action = await request.json();

    const [coversFile, pendingFile] = await Promise.all([
      getFile('data/covers.json', env.GITHUB_TOKEN),
      getFile('data/pending.json', env.GITHUB_TOKEN),
    ]);

    const { covers, pending } = applyReviewAction(coversFile.content, pendingFile.content, action);

    await Promise.all([
      putFile('data/covers.json', covers, coversFile.sha, env.GITHUB_TOKEN, `Publish review: ${action.id}`),
      putFile('data/pending.json', pending, pendingFile.sha, env.GITHUB_TOKEN, `Remove from pending: ${action.id}`),
    ]);

    return new Response('OK');
  },
};
```

- [ ] **Step 6: Commit**

```bash
git add worker/review-logic.js worker/review-logic.test.js worker/publish.js
git commit -m "Add review-publish logic and Cloudflare Worker endpoint"
```

---

## Task 10: Review page markup and wiring

**Files:**
- Create: `review.html`
- Create: `assets/review.js`

**Interfaces:**
- Consumes: `data/pending.json`, the deployed Worker URL from Task 9 (placeholder filled in during Task 12)

- [ ] **Step 1: Write the page**

```html
<!-- review.html -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Review — Clark Family Creative</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<h1>Pending Review</h1>
<div id="list"></div>
<script src="assets/review.js"></script>
</body>
</html>
```

```javascript
// assets/review.js
const WORKER_URL = 'REPLACE_WITH_DEPLOYED_WORKER_URL';
const SECRET_STORAGE_KEY = 'covers_review_secret';

function getSecret() {
  let secret = localStorage.getItem(SECRET_STORAGE_KEY);
  if (!secret) {
    secret = prompt('Enter the review secret:');
    localStorage.setItem(SECRET_STORAGE_KEY, secret);
  }
  return secret;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

async function submitAction(action) {
  await fetch(WORKER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-review-secret': getSecret() },
    body: JSON.stringify(action),
  });
  location.reload();
}

function render(items) {
  document.getElementById('list').innerHTML = items.map(item => `
    <div class="cover" data-id="${escapeHtml(item.id)}">
      <img src="${escapeHtml(item.thumbnail)}" width="120">
      <div>
        <div>${escapeHtml(item.title || '(no title)')} &middot; ${escapeHtml(item.date)}</div>
        <label>Song <input class="song" value="${escapeHtml(item.song || '')}"></label>
        <label>Artist <input class="artist" value="${escapeHtml(item.artist || '')}"></label>
        <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Watch</a>
        <button class="publish">Publish</button>
        <button class="discard">Discard</button>
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.publish').forEach(btn => btn.addEventListener('click', e => {
    const card = e.target.closest('.cover');
    submitAction({
      type: 'publish',
      id: card.dataset.id,
      song: card.querySelector('.song').value,
      artist: card.querySelector('.artist').value,
    });
  }));
  document.querySelectorAll('.discard').forEach(btn => btn.addEventListener('click', e => {
    submitAction({ type: 'discard', id: e.target.closest('.cover').dataset.id });
  }));
}

fetch('data/pending.json').then(r => r.json()).then(render);
```

- [ ] **Step 2: Verify manually**

Run: `python3 -m http.server 8000` from the repo root, temporarily set `data/pending.json` to:
```json
[{"id": "x1", "title": "Maybe a cover?", "date": "2026-08-01", "views": 5, "thumbnail": "https://img.youtube.com/vi/x1/mqdefault.jpg", "url": "https://www.youtube.com/watch?v=x1"}]
```
Open `http://localhost:8000/review.html`. Expected: the item renders with editable Song/Artist fields and Publish/Discard buttons. Clicking either will attempt a network call to the placeholder `WORKER_URL` and fail (expected — Worker isn't deployed yet, that's Task 12). Revert `data/pending.json` back to `[]` afterward.

- [ ] **Step 3: Commit**

```bash
git add review.html assets/review.js
git commit -m "Add review page for approving or discarding pending covers"
```

---

## Task 11: Initial backfill run

**Files:**
- Modify: `data/covers.json`, `data/pending.json`, `data/state.json` (populated by running the pipeline, not hand-edited)

**Interfaces:**
- Consumes: `scripts/update.py`'s `run(data_dir, force_all=True, notify=False)` (Task 5)

- [ ] **Step 1: Run the backfill locally**

```bash
cd scripts && python update.py --all
```

This processes every video currently on the channel's Videos tab (Shorts excluded automatically), classifying each into `covers` or `pending`. It does not send email (`--all` implies `notify=False` per Task 5's `__main__` block) since a full-history run could otherwise queue dozens of review emails at once.

- [ ] **Step 2: Manually review the results**

Open `data/pending.json` and check how many videos landed there vs. `data/covers.json`. For any pending item, either fix it by hand in `data/pending.json` and re-run, or note it for review via `review.html` after deployment (Task 12) — both are valid; hand-fixing now avoids waiting on the Worker for the initial backfill specifically.

- [ ] **Step 3: Commit the seeded data**

```bash
git add data/covers.json data/pending.json data/state.json
git commit -m "Backfill full cover history from the channel"
```

---

## Task 12: Deploy and wire up

**Files:**
- Modify: `worker/publish.js` (`REPO` constant)
- Modify: `assets/review.js` (`WORKER_URL` constant)

This task is account/credential setup rather than code — each step is a manual action with exact values to enter.

- [ ] **Step 1: Push the repo to GitHub**

```bash
gh repo create song-list --public --source=. --remote=origin --push
```

(Or create the repo manually on github.com and `git remote add origin <url> && git push -u origin main` if `gh` isn't set up.)

- [ ] **Step 2: Enable GitHub Pages**

In the repo on github.com: Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder: `/ (root)`. Note the resulting URL (e.g. `https://<username>.github.io/song-list/`).

- [ ] **Step 3: Update the review page URL used by the email**

In `scripts/update.py`, set `REVIEW_PAGE_URL` to `https://<username>.github.io/song-list/review.html` using the actual Pages URL from Step 2.

- [ ] **Step 4: Create a Gmail App Password**

At myaccount.google.com/apppasswords (for the Gmail account that will send notifications), generate an app password. In the GitHub repo: Settings → Secrets and variables → Actions → New repository secret:
- `SMTP_USER` = the Gmail address
- `SMTP_PASS` = the generated app password

- [ ] **Step 5: Create a GitHub fine-grained Personal Access Token for the Worker**

At github.com/settings/personal-access-tokens/new: repository access limited to this one repo only, permission `Contents: Read and write`. This token is only ever pasted into the Cloudflare Worker's secret store (Step 7) — it is never exposed in any file or client-side code.

- [ ] **Step 6: Fill in the Worker's REPO constant**

In `worker/publish.js`, replace `REPLACE_WITH_GITHUB_USERNAME/song-list` with the real `<username>/song-list`.

- [ ] **Step 7: Deploy the Cloudflare Worker**

```bash
npm install -g wrangler
cd worker && wrangler init --from-dash=false --yes  # creates wrangler.toml if not present
wrangler deploy publish.js
wrangler secret put GITHUB_TOKEN   # paste the token from Step 5
wrangler secret put REVIEW_SECRET  # choose and paste any random passphrase
```

Note the deployed Worker URL printed by `wrangler deploy` (e.g. `https://covers-review.<subdomain>.workers.dev`).

- [ ] **Step 8: Fill in the review page's Worker URL**

In `assets/review.js`, replace `REPLACE_WITH_DEPLOYED_WORKER_URL` with the URL from Step 7.

- [ ] **Step 9: Commit the filled-in constants**

```bash
git add worker/publish.js assets/review.js scripts/update.py
git commit -m "Wire up deployed Worker URL and repo details"
git push
```

- [ ] **Step 10: End-to-end smoke test**

In the GitHub repo: Actions tab → "Update covers list" workflow → "Run workflow" (this is the `workflow_dispatch` trigger, for testing without waiting for the 5:30 PM schedule). Confirm: the run succeeds, and if it found nothing new, `data/` shows no diff (expected, since Task 11 already processed everything as of the backfill). Confirm the public page at the Pages URL from Step 2 loads and shows the backfilled covers with working search and sort.

When ready, use `review.html` on the live site (enter the `REVIEW_SECRET` passphrase from Step 7 when prompted) to confirm Publish/Discard actually commit back to `data/covers.json` / `data/pending.json` on GitHub.
