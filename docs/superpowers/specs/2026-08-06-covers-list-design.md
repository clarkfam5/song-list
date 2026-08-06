# Clark Family Creative — Covers List Design

## Purpose

A public, searchable, sortable webpage listing every cover Clark Family
Creative has posted on YouTube, kept up to date automatically as new
covers are posted.

## Source

Channel: `https://www.youtube.com/@TheClarkFamilyCreative`
(same channel, historically also branded "Colt Clark and the Quarantine
Kids" in older video titles/descriptions).

Only the channel's **Videos** tab is used. **YouTube Shorts are excluded**
— the channel posts Shorts more often than full covers, and mixing them
in would flood the list. Detection: pull from the Videos listing only
(not the Shorts feed), and as a safety net, drop anything that resolves
to a `/shorts/` URL or has a very short duration.

## Data fields per entry

- Song title
- Original artist/band (not the performing family — see Attribution below)
- Date recorded (video upload date)
- View count (captured when the video is first added — see Update
  pipeline for why this isn't refreshed afterward)
- Thumbnail image
- Link to the YouTube video

## Attribution logic

Titles alone are often insufficient — e.g. `"Colt Clark and the
Quarantine Kids play 'Two of Us'"` names the song but not the original
artist. The description reliably contains a credit line (validated
against two real videos during design, e.g. *"...singing 'You've Got a
Friend in Me' by Randy Newman"*). Parsing order per video:

1. Look for an explicit artist credit in the description.
2. If found, extract song + artist from that line.
3. If not found (or the video doesn't read as a cover — e.g. vlog,
   original song), do **not** guess. Hold for review (see below).

## Update pipeline (automatic)

Runs once daily at 5:30 PM (assumed US Eastern — confirm/adjust when
scheduling).

1. Fetch the channel's video list via `yt-dlp` (no YouTube API key
   needed; validated working during design).
2. Diff against previously seen video IDs; process only new ones.
3. For each new video: apply attribution logic above.
   - Confident match → append to the published data file.
   - Ambiguous/unclear → append to a separate pending file, not shown
     on the public page.
4. View counts are captured once, at add-time, from the per-video
   fetch in step 3 — the cheap channel-wide listing used in step 1
   doesn't include view counts at all (confirmed during
   implementation), so there's no cheap way to refresh all published
   entries daily; doing it per-video for the whole list would mean
   hundreds of extra network calls every day for a channel this size,
   which isn't worth the time or rate-limit risk. "Most Popular"
   sorting therefore reflects views as of when each cover was added,
   not live counts.
5. If any items are pending, send one email to `clarkfamilyband@gmail.com`
   and `cashclarkemail@gmail.com` with what was found and a link to the
   review page.
6. Commit updated data file(s) back to the repo; GitHub Pages redeploys
   automatically.

`yt-dlp` is a community-maintained scraping tool, not YouTube's official
API — chosen because it requires no Google Cloud/API-key setup and
worked reliably in testing. Trade-off: it occasionally needs updating
when YouTube changes its site; the workflow keeps it current
automatically. If the pipeline ever silently stops finding new videos,
this is the first thing to check.

## Review workflow

A separate, unlisted page lists any pending (held-back) videos with
whatever info was found, editable fields for song/artist/date, and two
actions: **Publish** or **Discard (not a cover)**. No GitHub knowledge
required to use it.

Publishing a review-page edit needs to write back to the data file
securely; this requires one small always-free helper (a serverless
function) holding write credentials — a one-time setup, not something
that needs ongoing attention.

## Public page

- Search bar: live filter, matches song title or artist, case-insensitive.
- Sort: Newest→Oldest (default), Oldest→Newest, Most Popular (views),
  Artist A-Z, Song Title A-Z.
- Each entry: thumbnail, song title, artist, date, link to video.
- Styling: plain (white background, black text) for now; intentionally
  minimal since it will be restyled once folded into a full website
  later. Must still be usable/embeddable as-is in the meantime.

## Initial build

Before daily automation takes over, one larger backfill pass processes
the channel's entire history (including older "Colt Clark and the
Quarantine Kids" videos) so the list starts complete.

## Hosting & cost

- GitHub Pages (free) for the public page.
- GitHub Actions (free tier) for the daily pipeline.
- Data stored as file(s) in the repo — no database.
- No YouTube API key/quota to manage.
- No expected dollar cost at this channel's scale.

## Out of scope (for this spec)

- Restyled/branded design (deferred until embedded in a real site).
- Embedding into an existing website (deferred; page is built to make
  this easy later, but not implemented now).
- Any content beyond covers (vlogs, originals, Shorts).
