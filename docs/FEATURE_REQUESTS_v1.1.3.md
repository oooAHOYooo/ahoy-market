# Feature Requests — v1.1.3

_Captured 2026-05-19. Reference doc for pickup on next machine._

---

## 1. Boost — Cart-Style Flow
- Boosts should accumulate in a cart before final checkout (not immediate single-purchase)
- Add a "Suggest Boost" default of $0.50
- *Completed: Created `spa/src/stores/cart.js` (Pinia store with localStorage persistence). Boost buttons in `ArtistDetailView.vue` and `MiniPlayer.vue` now add $0.50 to the cart and show a toast instead of routing to checkout immediately. Added a "Cart" nav item to `AppSidebar.vue` with a live red badge. Updated `CheckoutView.vue` to handle `type=cart`: shows full cart list with per-item +/- controls, proportional fee breakdown, and Stripe/wallet payment. Backend `routes/boost_stripe.py` updated to accept an `items[]` array in `create-intent` (single Stripe fee for the whole cart) and to write one `Tip` row per artist on `confirm`. Also fixed `TipArtistView.vue` (previously a dead redirect) to add the artist to the cart first, then forward to the cart checkout. "Suggested: $0.50/artist" hint shown in checkout UI.*

## 2. Android Auto (Web Auto)
- Make Android Auto / Web Auto skippable (user can bypass without completing setup)
- *Completed: Updated `OnboardingView.vue` to update the user profile with `onboarding_complete: true` when skipping, permanently bypassing the onboarding flow.*

## 3. Ahoy TV
- Disable live scroll on the Ahoy TV view (no more scroll interaction while live content plays)
- *Completed: Modified `LiveTVView.vue` guide scroller to apply a `.no-scroll` style class that hides horizontal overflow and sets the cursor to default, and updated the `onMouseDown`, `onMouseMove`, and `onMouseUp` drag handlers to return early while live content is playing.*

## 4. Podcast — Audio vs. Video Choice
- If a podcast episode has a video version (e.g. Tyler's), present a picker: **Audio** or **Video** before playback begins
- *Completed: Modified `PodcastEpisodeView.vue` to present a glassmorphic format choice picker when an episode has a `video_url`. Choosing video renders a premium HTML5 video player inline over the hero art, and includes strict playback syncing to pause the background audio player (and vice versa).*

## 5. Music — Shuffle All Button
- Shuffle All should reorder the visible list, not just play randomly
- Must stay randomized across refreshes (currently resets on second tap / page reload)
- *Completed: Modified `MusicView.vue` to introduce a `'shuffle'` sort mode (and explicit "Shuffled" option in the sort drawer), persisting the random order and selected sort method to `localStorage` so it survives page refreshes and toggles smoothly.*

## 6. Settings Page — Dynamic Build Number
- `https://app.ahoy.ooo/settings` should display the actual current build number dynamically (not hardcoded)
- *Completed: Updated `ahoy/version.py`, and made backend API dynamic using `package.json` and git commits.*

## 7. Settings Page — Surface in Main Dashboard
- `https://app.ahoy.ooo/settings` should be accessible directly from the main dashboard nav
- *Completed: Added settings link in `AppSidebar.vue`.*

## 8. Settings Page — Remove Temporary Password Screen
- Remove the "temporary password" prompt/screen from the settings flow
- *Completed: Removed password section card, form, and handlers from settings flow.*

## 9. Settings Page — Downloads in Experimental Section
- Add a **Downloads** entry under the Experimental section on the settings page
- *Completed: Added Experimental card containing a link to `/mp3-player`.*

## 10. Settings / Profile — Profile Photo Upload
- Allow users to upload a JPEG as their profile photo from both settings and profile pages
- *Completed: Added file upload endpoint `/api/user/avatar` on the backend, styled premium hover/overlay photo upload controls on both `SettingsView.vue` and `AccountView.vue`.*

## 11. What's New — TB Content Refresh + Clips
- Refresh "What's New" with TB (Tylers / Jerry / similar) clips — same treatment as the Tyler and Jerry clip cards already done
- `tnab5` clips in What's New should link to their individual episode/clip pages (not play inline or go nowhere)
- *Completed: Modified `content_db.py` fallback to pass `is_clip` and `video_url` columns. Refreshed `whats_new.json` with related video cards for Jerry Ornelas, Tom Berry, and Tyler Needs a Break. Modified `PodcastEpisodeView.vue` to support loading and rendering of individual clip pages via ID so the cards link seamlessly to their individual clip play surfaces.*
