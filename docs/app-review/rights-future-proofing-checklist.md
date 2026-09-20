# Rights Future-Proofing Checklist

Goal: make future App Store, Play Store, and platform reviews easy to answer with records instead of memory.

## Before Publishing Any Creator Content

- Confirm the creator/rights holder has a signed authorization, accepted creator terms, or written approval on file.
- Save the evidence path in the rights register.
- Confirm the authorization covers the actual content type: audio, video, podcast, artwork, metadata, or AHOY TV scheduling.
- Confirm samples, covers, collaborators, producers, labels, publishers, artwork, stock footage, and archive footage are cleared when applicable.
- Mark content unpublished or hidden until rights are confirmed.

## Database Fields To Add Later

Add a rights table or fields so the app can prove its content state directly:

- `rights_status`: `pending`, `authorized`, `owned`, `licensed`, `rejected`, `expired`, `revoked`.
- `rights_holder_name`.
- `rights_holder_email`.
- `rights_agreement_id`.
- `rights_evidence_url` or internal file reference.
- `rights_scope`: audio, video, podcast, artwork, metadata, live_tv, promo, mobile_app.
- `rights_effective_date`.
- `rights_expiration_date`.
- `rights_last_reviewed_at`.
- `rights_reviewed_by`.
- `rights_notes`.

## App Behavior To Add Later

- Hide content from public APIs unless `rights_status` is `authorized`, `owned`, or `licensed`.
- Exclude pending/expired/revoked content from `/api/music`, `/api/shows`, `/api/podcasts`, `/api/artists`, `/api/radio/manifest`, and `/api/live-tv/channels`.
- Add an admin-only rights dashboard outside the consumer app.
- Add an export command that regenerates the Apple/Google rights packet from the live database.
- Add upload storage for signed agreements and release forms.

## App Review Wording

Use this positioning consistently:

Ahoy is a direct-to-artist media platform. It does not aggregate unauthorized third-party streaming services. Content is either produced by Ahoy / Little Market LLC, submitted by creators and rights holders who authorized Ahoy distribution, or otherwise licensed/cleared for app distribution.

AHOY TV is a scheduled marketing and discovery surface for Ahoy-controlled video catalog items. It is not a third-party TV, cable, IPTV, or broadcast retransmission service.

## Ongoing Review Cadence

- Review the rights register before every iOS release.
- Review the rights register before every major content import.
- Keep an annual rights audit folder by year.
- Save App Review correspondence next to the supporting rights packet.
- If a creator asks for removal, document the request and remove or hide the content before the next public content refresh.
