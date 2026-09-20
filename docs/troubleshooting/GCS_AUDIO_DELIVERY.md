# GCS Audio Delivery Troubleshooting

Use this when GCS-hosted audio fails but S3-hosted audio still plays.

## Current finding

As of 2026-04-26, sampled GCS audio objects are publicly reachable and support byte-range playback. The buckets initially did not return `Access-Control-Allow-Origin` for `https://app.ahoy.ooo`, `capacitor://localhost`, or `http://localhost`; that has been fixed for `gs://ahoy-song-collection` and `gs://ahoy-podcast-collection`.

That means a normal `<audio src="...">` can play the file, but an audio element configured with `crossOrigin = 'anonymous'` can fail because the browser requires CORS headers. The Vue player in `spa/src/stores/player.js` now matches the legacy player behavior and does not force anonymous CORS mode.

## Google CLI status

The relevant bucket owner is `alex@ahoy.ooo`, not `alex@littlemarket.org`.

Observed before login on 2026-04-26:

```bash
gcloud auth list --format='table(account,status)'
```

Returned only:

```text
alex@littlemarket.org  *
```

Explicit bucket checks with `--account=alex@ahoy.ooo` initially failed because that account had no valid local credentials:

```text
Your current active account [alex@ahoy.ooo] does not have any valid credentials
```

After `gcloud auth login alex@ahoy.ooo --no-launch-browser`, `alex@ahoy.ooo` became the active account and both bucket policies were updated from `docs/deployment/gcs-audio-cors.json`.

## Commands

```bash
gcloud auth login alex@ahoy.ooo
gcloud config set account alex@ahoy.ooo
gcloud storage buckets describe gs://ahoy-song-collection --format=json
gcloud storage buckets describe gs://ahoy-podcast-collection --format=json
gcloud storage objects describe 'gs://ahoy-song-collection/Jake Custer - Better Halves.mp3' --format=json
gcloud storage objects describe 'gs://ahoy-song-collection/mintea - 7eleven.mp3' --format=json
gcloud storage buckets update gs://ahoy-song-collection --cors-file=docs/deployment/gcs-audio-cors.json
gcloud storage buckets update gs://ahoy-podcast-collection --cors-file=docs/deployment/gcs-audio-cors.json
```

Check these fields:

- bucket `cors`
- bucket public access prevention / uniform bucket-level access
- object `contentType`
- object `acl` or IAM-derived public readability
- object `metadata`

## Header checks

Use `curl` to compare public delivery and CORS behavior:

```bash
curl -I -L 'https://storage.googleapis.com/ahoy-song-collection/Jake%20Custer%20-%20Better%20Halves.mp3'
curl -I -L -H 'Origin: https://app.ahoy.ooo' 'https://storage.googleapis.com/ahoy-song-collection/Jake%20Custer%20-%20Better%20Halves.mp3'
curl -I -L -H 'Origin: capacitor://localhost' -H 'Range: bytes=0-1' 'https://storage.googleapis.com/ahoy-song-collection/Jake%20Custer%20-%20Better%20Halves.mp3'
```

Healthy public media delivery should return `200` or `206`, `Content-Type`, `Content-Length` or `Content-Range`, and `Accept-Ranges: bytes`.

If a future player feature needs Web Audio analysis, canvas extraction, or any other CORS-gated read access, configure bucket CORS instead of re-adding `crossOrigin` without storage headers.

## Current CORS policy

The deployed policy is tracked at `docs/deployment/gcs-audio-cors.json`.

```json
[
  {
    "origin": [
      "https://ahoy-indie-media.onrender.com",
      "https://ahoy.ooo",
      "https://app.ahoy.ooo",
      "capacitor://localhost",
      "http://localhost",
      "http://localhost:5001",
      "http://localhost:3000"
    ],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
```
