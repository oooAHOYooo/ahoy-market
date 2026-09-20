# convert_one_audio.py

Converts a single audio file to a smaller AAC `.m4a` for uploading to Ahoy Indie Media.

## Requirements

Install ffmpeg once:

```bash
brew install ffmpeg
```

## Basic usage

```bash
python3 convert_one_audio.py ~/Downloads/song.wav
```

Output lands in `~/Downloads/ahoy_converted/song.m4a` at 256k by default.
The original file is never touched.

## Overwrite an existing output

```bash
python3 convert_one_audio.py ~/Downloads/song.wav --overwrite
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--output-dir` | `~/Downloads/ahoy_converted` | Where to put the converted file |
| `--bitrate` | `256k` | AAC bitrate (e.g. `128k`, `192k`, `320k`) |
| `--overwrite` | off | Replace output if it already exists |

## Examples

```bash
# Custom output folder
python3 convert_one_audio.py ~/Downloads/song.wav --output-dir ~/Desktop/ready

# Lower bitrate for smaller file (good for speech/podcasts)
python3 convert_one_audio.py ~/Downloads/episode.mp3 --bitrate 128k

# High quality + force overwrite
python3 convert_one_audio.py ~/Downloads/track.flac --bitrate 320k --overwrite
```

## Upload to Google Cloud Storage

After converting, copy the file to your Ahoy bucket:

```bash
gsutil cp ~/Downloads/ahoy_converted/song.m4a gs://MY_BUCKET_NAME/music/
```

Replace `MY_BUCKET_NAME` with your actual GCS bucket name.
