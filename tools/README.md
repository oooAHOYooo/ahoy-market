# Ahoy Custom Tools

Custom tools and utilities for managing Ahoy content, administration, and integration workflows.

## Tools

### youtube_to_bucket.py

Download videos from YouTube and upload to Google Cloud Storage.

**Requirements:**
- `yt-dlp` (install with `pip install yt-dlp`)
- `google-cloud-storage` (for GCS uploads)

**Usage:**

Download a single video and save metadata:
```bash
python tools/youtube_to_bucket.py \
  --url https://www.youtube.com/watch?v=... \
  --output-file video.json
```

Download and upload to GCS:
```bash
python tools/youtube_to_bucket.py \
  --url https://www.youtube.com/watch?v=... \
  --upload --bucket my-videos-bucket
```

Download an entire playlist:
```bash
python tools/youtube_to_bucket.py \
  --playlist https://www.youtube.com/playlist?list=... \
  --upload --output-file playlist.json
```

Or via the main CLI:
```bash
python scripts/ahoy_cli.py youtube-download --url https://www.youtube.com/watch?v=...
```

**Environment Variables:**
- `AHOY_VIDEOS_GCS_BUCKET` - Default GCS bucket for uploads (optional if `--bucket` specified)

**Output:**
Generates a JSON metadata file with:
- Title, description, duration
- YouTube ID, uploader info
- View count, likes
- GCS URLs (if uploaded)
- Download timestamp

### cli.py

Basic admin CLI for user management.

```bash
python tools/cli.py set-admin --email user@example.com --on
python tools/cli.py set-admin --email user@example.com --off
```

## Integrating New Tools

1. Create a new Python file in `tools/`
2. Implement a `main(argv)` function that returns an exit code
3. Add an import and command handler to `scripts/ahoy_cli.py`
4. Document in this README

## Running Tools

Tools can be run directly:
```bash
python tools/youtube_to_bucket.py --help
```

Or through the main CLI:
```bash
python scripts/ahoy_cli.py youtube-download --help
```
