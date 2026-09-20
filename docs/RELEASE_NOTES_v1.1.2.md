# Release Notes — v1.1.2

**Target platforms:** iOS, Android, Web, Desktop
**Status:** Draft prep

> v1.1.2 delivers major new experiential components, including the CMYK interactive radio mini-games and the Support Hub monetization system, while standardizing mobile-first "glassmorphism" visual layouts across the entire platform.

---

## What's new in v1.1.2

- **🎮 Radio Games**: Complete replacement of the radio skipper with fully interactive Three.js CMYK games.
    - **Ninja Jump / Trampoline Flip**: Charge jumps and execute airborne rotation combos to score points while the radio plays.
    - Features vector aesthetics, falling shurikens, music-synced moon pulses, and landing confetti.
- **💰 Support Hub**: Added platform and artist boost hubs to the architecture, including a marketplace-style support page that leads with artist boosts and keeps Ahoy as an optional second line item below the directory.
- The artist spotlight now uses an artist-page-style circular thumbnail instead of the 3D renderer so the browse motion feels faster while keeping the visual language consistent.
- The support marketplace now includes artist sorting, compact stats, and clearer listing-style boost CTAs.
- The support page now includes a logged-in portfolio view that tracks boost holdings, badge progress, and recent support activity.
- The boost page spacing was tightened so the marketplace, portfolio, and Ahoy add-on read more compactly on desktop and mobile.
- The latest boost-page pass collapses the artist CTA into the card footer and reduces the portfolio into a shorter summary-first layout.
- **🛠️ Glassmorphism Hero Consolidation**: Uniform "glass card" headers applied to all primary views:
    - **Merch**: Gold accent glass card, store eyebrow, count badge.
    - **Videos**: Music-matching glass header with bold titles and play actions.
    - Also applied to **Artists, Events, Studio, and Saved** pages.
- **📚 Video Library Organization**: The Videos page now groups items by type first, with dedicated sections for music videos, live shows, films/shorts, and an everything-else fallback. Video detail pages also show a matching type rail alongside the artist rail when related items exist.
- The Videos page now sorts those type sections by the newest item inside each bucket, and each section header shows a small recency label so the updated shelf order is visible at a glance.
- The Podcasts page now shows a small recency label on each show section and keeps the show sections ordered by the newest episode in that show.
- **🚀 Mobile Performance Hooks**: Integrated hardware-accelerated GPU hints and CSS containment for ultra-smooth inertial scrolling on iOS and Android.
- **🔔 Mobile Navigation Polish**: 
    - Updated the Mobile Deck to include a dedicated Playlists action.
    - Standardized the mobile notification drawer to a slide-in top sheet.
- **🎚️ Music Browse Controls**: Added an artist dropdown filter to the Music page, alongside the existing search and sort controls.
- **⏱️ Global Footer Timeline**: Added seekable playback timelines to the shared footer, desktop now-playing transport, and mobile deck player so current track progress stays visible and scrubbable from the bottom shell.
- **🖼️ Dynamic Subheaders**: Implemented automatic context-aware item counts across Artists and Video galleries.
- **📐 Video Section Labels**: Gave the Videos page section headers a slightly more distinct shelf-label treatment so the grouped sections read more clearly without changing the layout.
- **🖼️ Video Share Thumbnails**: Video detail URLs now emit server-side Open Graph and Twitter metadata from the video thumbnail, title, and description so shared links preview the actual video art.
- **🎬 Video Watermark Fix**: Individual video pages now use the transparent `u_ahoy23.png` logo watermark instead of the square placeholder box.
- **🎼 Artist Album Grouping**: Individual artist pages now organize music by album when that metadata exists, then keep any remaining tracks visible in an "Other Tracks" section.
- **🎬 Artist Video Routing**: Artist-page video cards now open the internal video detail route with a stable slug, and the video page resolves those slugs back to the matching video.
- **🎯 Video Thumbnail Routing Cleanup**: Explore widgets and the video-detail rails now keep thumbnail clicks inside the app instead of opening raw media URLs.
- **👥 Artist Catalog Update**: Added new Tallboyz clip artists to the catalog so the latest clip profiles can resolve in browse and search flows.
- **🧾 Account Security Collapse**: The Account page now hides password, sign-out, and deletion controls behind a collapsed security disclosure.
- **📈 PostHog Analytics Migration**: Replaced the Google Analytics shell snippet with PostHog wiring in the SPA, added route pageviews plus auth identity stitching, and updated the privacy copy to reflect the new analytics stack.
- **🎬 Video Watch Metrics**: Native video players now emit start, progress, stop, and complete events with watched-seconds data so watch counts and watch time can be measured in PostHog and the admin analytics table.
- **📊 Owner Watch Funnel**: Added watch starts, completions, completion rate, average watch time, and top watched videos to `/ops/stats` and `ahoy-cli`.
- **👤 Guest Listening Tracking**: Anonymous playback now maps to a dedicated internal guest account so incognito listens can contribute to listening totals without changing the listening schema.
- **📊 Daily Ops Trends**: The private `/ops/stats` page now includes a compact day-by-day trend strip, and `ahoy-cli posthog-import <file>` gives you a path for future PostHog exports.
- **🔧 Content Management**: Enabled authoritative "What's New" database edits preserving data across environment deployments.
- **🧭 Desktop Sidebar Discovery**: Added a dedicated `What's New` entry to the desktop left sidebar so the update archive is directly reachable from the main nav.
- **📱 Mobile Deck Discovery**: Swapped `What's New` into Deck 1 next to Artists with a visible bullhorn icon and moved Events into the Deck 3 utility slot.
- **🔴 Mobile Update Dot**: Added a small unread-update dot to the Deck 1 `What's New` icon for content and platform notifications.
- **🧑‍🎤 Mobile Artist Cards**: Tightened the Artists grid on phones so cards are image-filled with overlaid names and no large empty grey body.
- **✨ Sidebar Hover Sweep**: Added a softer hover cascade in the desktop sidebar so adjacent items pick up a subtle light-pass effect when you move across the nav.
- **🎯 Sidebar Hover Accent**: Tightened the hover treatment with a slim accent bar and inner highlight so the active row still feels anchored while the cursor moves around it.
- **💡 Sidebar Light Sweep**: Reworked the hover motion to feel more like a drifting light beam by reducing scale and animating the glow across the row.
- **🌫️ Sidebar Overlay Softening**: Lowered the hover overlay opacity so the adjacent-row shimmer reads as a lighter, cooler illusion.
- **🌊 Sidebar Water Fill**: Swapped the hover sheen toward a bottom-up fill so quick passes feel fluid and longer hovers build more naturally across the hovered row and its neighbors.
- **🌘 Sidebar Ripple Falloff**: Separated the ripple into stronger hovered, softer adjacent, and faint second-neighbor layers so it reads more like a pebble in water and less like synchronized glow.
- **🫧 Sidebar Glass Hover**: Shifted the hovered item toward a brighter glass panel and pushed the text/icon emphasis onto the active row while softening neighbor echoes.
- **✨ Sidebar Shimmer Layer**: Added a very faint moving shimmer on the hovered row only for a subtle living-glass feel.
- **⏳ Sidebar Hover Dwell**: Made the hover tint and shimmer deepen the longer the pointer rests on a row.
- **🔐 Account Password MVP**: Added logged-in password changes on the Account and Settings pages, temporary-password hints, and a print-ready promo-account CSV generator for in-person username/password handouts.

---

## Fixes

- Resolved a regression that caused blank white screens on desktop web loads.
- Corrected Android Auto radio queue handoff, ensuring playable items populate correctly.
- Cleaned up redundant skip-to-content overlays.
- Standardized hero card top margins to lock identically between Music, Artists, and Podcast grids.
- Clamped mobile deck toggle behavior to prevent double-advancement.
- Fixed the artist-page back button so it stays fully visible on narrow mobile screens and uses an icon-first control.

---

## Version bumps

- `package.json`: `1.1.2`
- `android/app/build.gradle`: `versionName "1.1.2"`, `versionCode 1772056511`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.1.2`, `CURRENT_PROJECT_VERSION = 11`
