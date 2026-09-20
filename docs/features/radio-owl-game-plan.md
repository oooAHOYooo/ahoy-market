# Radio Owl Game — Plan

**Status:** Partially implemented ambient v1 on `/radio`; not yet a full save/share/world-building feature.
**Location it will live:** `spa/src/features/radio-game/`
**Drafted:** 2026-04-15

An ambient, lo-poly 3D mini-game that runs as the background of the `/radio` page. It is a *companion*, not a focus game — the user listens to the radio, and an owl glides through a stylized forest behind the controls. Players can ignore it entirely, or tap to collect motes for points.

The bottom now-playing deck and existing radio widget chrome are not affected. The game renders *behind* the glassmorphic controls.

Radio timeline/source-of-truth note:
- Station architecture now lives in `docs/features/radio-station-manifest.md`
- The radio page should consume `GET /api/radio/live` instead of inventing its own local shuffle
- Live position is still computed on the client from the manifest epoch and server time
- The radio page now stays inside the normal app shell and keeps the bottom dock visible
- `Back To Live Radio` lives on the radio page, not in the mini-player

## Current v1 reality

What exists now:

- ambient owl backdrop inside the `/radio` hero
- feather count and passive accumulation while tuned into radio
- steering/trick affordances on the radio page
- manifest-driven live station info shared with the rest of the app

What does not exist yet:

- creation saving
- social sharing
- collaborative world building
- a finished collectible/progression loop beyond feathers and ambient interaction

This means the current implementation should be framed as:

- a live radio page with atmospheric owl-world polish
- early game scaffolding, not the finished game vision in this document

---

## Concept

- Night-forest flyer. An owl auto-glides between branches on its own (idle AI).
- Glowing motes spawn occasionally — tap to send the owl to catch them for points.
- Rare events every 30–60s (shooting star, rival owl, glowing branch) for bigger rewards.
- **No fail state.** No stamina. Score accrues passively while the radio plays.
- Pausing radio pauses the game. Stops rendering when tab hidden or widget out of view.

## Why ambient (not a real game)

Radio use is background listening. A game with fail states fights that. Tying score growth to listening time rewards actual radio use and gives the game retention legs without demanding attention.

---

## Scoring

- `+1/sec` passive while radio plays (owl "sings along").
- `+10–50 per mote` tapped.
- Bonus multiplier if radio has been playing uninterrupted for >5 min.
- Closing app saves state.

## Progression (the real retention hook)

- **Unlock biomes** at score thresholds: pine → oak → willow → sakura. Swap branch GLTFs + fog color. Cheap.
- **Owl skins** unlocked by lifetime listen-time milestones. Texture/vertex-color swap, no new model.

## High scores — soft take

Skip competitive leaderboards for v1. Ambient design contradicts competitive pressure.

Track instead:
- Personal lifetime score (localStorage → synced to user account).
- "Longest flight" = longest single listening session (shown as a stat, not a ranking).
- Friends-only board is a v2 idea if social features ever ship.

---

## Art direction: lo-poly + atmospheric

Reference mood: *Monument Valley*, *Alto's Odyssey*, *Sky: Children of the Light*. Geometry is deliberately crude; lighting and color do the work.

### The five rules

1. **Flat shading, no textures.** `MeshStandardMaterial` with `flatShading: true`. Crisp facet edges, zero texture memory.
2. **Vertex colors, not materials.** Paint colors onto mesh vertices in Blender. One material per asset. Gradients across faces come free. This is the single biggest "looks expensive" trick.
3. **Two lights only.** Warm key (moonlight-blue or sunset-orange, low angle) + cool fill (deep indigo, opposite side). Ambient near black. Warm/cool contrast on flat facets is what makes lo-poly glow.
4. **Fog is a feature.** `FogExp2` matched to the radio widget's background color. Distant branches fade to background → infinite depth on a 300px stage. Also hides draw distance.
5. **Silhouette over detail.** Owl recognizable from outline alone. Rounded wedge body + triangle wings + two circle eyes. 200–400 tris total.

### Palette (pulled from existing radio widget)

- Background: deep teal-navy (existing widget color).
- Branches: desaturated plum → dusty rose via vertex colors.
- Leaves/needles: muted sage + one warm gold accent cluster per tree.
- Owl: cream body, charcoal wingtips, amber eyes (only saturated color in the scene).
- Motes: soft gold with bloom.

**Rule:** one saturated accent color in the whole scene. Everything else muted.

### Geometry budget

| Asset | Tris | Notes |
|---|---|---|
| Owl | 300 | One mesh, vertex-colored |
| Branch (×3 variants) | 150 each | Instanced, 8–12 on screen |
| Leaf cluster | 80 | Instanced |
| Mote | 12 (icosahedron) | Emissive, instanced |
| Ground/hills | 200 | Background silhouette only |

Total: **<3000 tris on screen.** Art payload budget: **<200kb** for all geometry.

### Post-processing

- **Bloom** on motes + owl eyes only (selective via emissive materials). ~2ms/frame.
- **Vignette** via a radial gradient overlay div (free, no shader).
- Skip SSAO, DOF, film grain.

### Motion

Static lo-poly looks like a screenshot. Movement sells it:

- Branches sway on a slow sine (vertex shader, or rotate the instance).
- Fog density pulses slightly with BPM.
- Motes bob + emit particles when collected.
- Owl wings flap on a 2-frame cycle (2fps looks charmingly handmade, not cheap).

### The one thing that would kill the look

Mixing shading styles. If the owl is flat-shaded and a branch has smooth normals, it looks amateur. Lock `flatShading: true` on every material, or export with hard edges on every face in Blender.

---

## Visual blending (the key move)

Don't build a "game box." Build a background that happens to have a game in it.

- Canvas is the radio widget's background layer — branches, fog, owl render *behind* track info, buttons, artwork.
- Radio controls sit on top with their existing glassmorphism — the forest shows through the blur.
- Canvas fades to transparent at top/bottom edges via CSS `mask-image` gradient. No hard rectangle.
- Palette pulled from current radio widget so it reads as "the radio page has depth now," not "a game was bolted on."
- Owl + motes are the only bright elements.

## Interaction without hijacking

- Canvas has `pointer-events: none` by default.
- Only motes/owl are tappable — single tap listener at canvas root, raycast to find hits.
- Tapping empty forest passes through. Tapping buttons = buttons work normally, never blocked.
- This is what keeps the radio widget feeling like a radio widget.

---

## Tech / integration

- **Three.js**, lazy-loaded. Three is ~150kb gz — dynamic import inside `OwlStage.vue` so it never touches the main bundle. Only loads when user lands on `/radio`.
- Mount inside existing radio widget as a sibling to the current background, `z-index: 0`. Controls stay at `z-index: 2+`.
- ~300px tall canvas on mobile. Target 60fps (cheap at this size).
- Single directional light + fog. No shadows.
- Pause render loop when: radio paused, tab hidden, widget scrolled out of view (IntersectionObserver).
- Render at 30fps if battery becomes an issue — ambient doesn't need smooth.

### File structure

```
spa/src/features/radio-game/
  OwlStage.vue              # mounts canvas, lifecycle, visibility observer
  useOwlScene.ts            # Three.js scene setup, returns { tick, dispose }
  useOwlAI.ts               # idle glide behavior, target picking
  useMotes.ts               # spawn/despawn, tap-to-collect
  useOwlScore.ts            # score state, localStorage + server sync
  assets/
    owl.glb                 # low-poly, <50kb
    branch.glb              # instanced
    mote-sprite.png
  OwlStage.css              # mask gradients, z-index layering
```

### Asset pipeline

- Model in Blender → vertex paint → export GLB.
- One GLB per asset, <30kb each.
- Starter assets: **Kenney.nl** CC0 lo-poly nature packs, recolor vertex palette to match widget.

---

## Build order (MVP, ~1 day of work)

1. `OwlStage.vue` with transparent canvas, fog, 5 static branches, 1 auto-gliding owl. No interaction yet.
2. **Go/no-go check:** does the glassmorphic now-playing bar look *better* with forest behind it? If blending looks janky the whole concept falls apart — stop and fix the palette before going further.
3. Add motes + tap-to-collect.
4. Score + localStorage.
5. Server sync + listen-time bonus.
6. Biome unlocks (swap GLBs + fog color on threshold).
7. Owl skins.

## Open decisions

- **Scope of presence:** Ship radio-only first. Global companion (owl follows across app while radio plays) is a v2 idea if people love it.
- **Music reactivity:** Start with timing/BPM from track metadata. Web Audio analyser on the stream is cooler but adds CORS headaches with HLS — defer.
- **Boost button tie-in:** Could offer "boost the owl" for a score multiplier, tied to existing boost flow. Could feel gross. Defer until core game is in.

## Backend (if/when needed)

New table for persistence:

```sql
radio_game_state (
  user_id uuid primary key,
  lifetime_score bigint default 0,
  longest_flight_seconds int default 0,
  unlocked_biomes text[] default '{pine}',
  unlocked_skins text[] default '{default}',
  updated_at timestamptz
)
```

Endpoints: `GET /api/radio-game/state`, `POST /api/radio-game/state` (debounced save every ~30s of play). No realtime, no leaderboard, no anti-cheat for v1.
