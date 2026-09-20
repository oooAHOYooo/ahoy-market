# Owl Game — Game Design Document

**Last updated:** 2026-04-23
**Status:** Historical prototype — the shipped v1.0.8 `/radio` implementation moved to a tiny skipper variant, but this doc still captures the owl-game design direction
**Source:** `spa/src/features/radio-game/`

---

## The One-Sentence Vision

An owl follows a bird through the world that bird's music made — and sometimes the bird looks back.

---

## Design Pillars

### 1. It's a toy, not a game
Skate 4 doesn't explain why you skate. This game doesn't explain why you fly. There is no mission, no story, no antagonist. The owl is a vessel for the feeling of motion. Like a skateboard: you can just cruise, or you can hunt beautiful lines. Both are correct.

### 2. Flow state over challenge
Flow requires matched challenge and skill. This game solves that differently than most: it makes difficulty *opt-in*. A passive player drifts center-lane and has a nice time. An active player chases rings, chains feathers across lanes, tricks off obstacles, and composes a line through space. The game never ramps on you — your own ambition is the difficulty dial.

### 3. Radio-first
The owl is in the air because music is playing. The game must never compete with the music for attention. Rules that follow:
- No fail state that interrupts playback or demands recovery attention.
- Obstacles are gentle taps, not punishments.
- If you ignore the game for 30 seconds it keeps flying, the world keeps breathing.
- Score shown as ambient poetry, not pressure.

### 4. The world is made of sound
The artist-bird flies ahead, just beyond the fog. The seeds it drops — feathers, orbs, rings — are what it's leaving behind as it goes. You're not flying through abstract light. You're following someone making something, collecting what they leave, and occasionally they look back and see you there.

---

## The Two Characters

### The Owl (you)
Nobody on a mission. You're flying because music is playing. Identity through motion — the banking, the bob, the wing-tuck on tricks, the slipstream trail. You don't need to know who you are. You know where you're going: forward, toward the bird.

### The Artist-Bird
The artist currently playing is a bird flying just ahead — always at the edge of the fog, never fully visible, never quite reachable. It lays seeds as it goes: the feathers, orbs, and rings you collect. These aren't randomly spawned pickups. They're breadcrumbs. It's leaving them for you.

**The glance back** — occasionally, on a quiet interval, the artist-bird turns its head. A small animation. It sees you're still there. Then it faces forward again and keeps flying.

This is the emotional core of the whole game. You've been following. It noticed. That's what listening to music feels like when it matters.

**Design rules for the glance:**
- Rare enough to feel like a gift, not a loop. Every 45–90 seconds, randomized.
- No sound, no UI, no reward. Just the gesture.
- If the player is very close (chaining pickups, high combo) — weight toward glancing sooner. The artist responds to being followed closely.
- If radio is paused or player is idle — no glance. The bird only looks back when someone is there.

**No radio = no artist-bird.** The corridor is empty, quieter. Just the owl and the fog. This is intentional — it's the sound of listening to silence.

**Different artists, different birds.** Subtle silhouette and color variation — not a character select screen, just something you start to notice after listening to the same artist a lot. The bird that plays with [artist] looks a little different than the one that plays with [artist]. You don't need to be told. You notice.

---

## What Flow Feels Like (the design target)

Picking up three feathers in sequence on the same altitude → banking through a ring → barrel rolling off the back of it → riding the slipstream boost into a new color world as the segment theme shifts.

The feeling is **compositional**. You're not reacting to danger — you're choosing a path because it looks beautiful. Like finding a clean skate line through a plaza, not because it scores highest but because it feels right.

---

## Core Loop (Implemented)

- Endless 3D corridor. Owl flies forward automatically.
- Player controls: **5 lanes** (left/right) + **3 altitudes** (low/mid/high).
- **Feathers** — drift in the air, collect by flying through. Worth 2 points each.
- **Rings** — bonus gates, reward clean line-flying. Worth 5 points.
- **Boost orbs** — speed burst + points.
- **Obstacles** — crystal spires. Light speed penalty + combo break on hit. Not punishing — more like a tap on the shoulder.
- **Tricks** — tap or Space. Barrel roll. Adds boost + looks great.
- Score accrues passively (+1 feather per 10s of radio play) whether the player steers or not.

---

## Feathers — Returning the Seeds

The artist-bird laid the seeds. You collected them. At the end of a session — or whenever you feel like it — you can return some to the artist.

Not money. Not a rating. Just seeds, sent back. The artist sees them in their dashboard as a count of presence: *someone was in your world, following you, collecting what you left*.

The gesture closes the loop: bird lays seeds → listener follows and collects → listener sends some back → bird knows someone was there.

**Design rules:**
- Never show a raw count in a way that creates anxiety. Show it like a distance hiked — not a score, a memory.
- Sending is optional and has no mechanical consequence. It's pure expression.
- Artists see total seeds received, not per-listener. No surveillance. No ranking of who listens most.
- The send UI should feel like leaving a note, not filing a form.

---

## Difficulty — Self-Imposed

The game never ramps on the player. Obstacles don't get denser over time. Speed increases with combo, but gradually and with a ceiling.

What the player *can* do:
- **Cruise** — stay center-lane, ignore obstacles, collect what drifts in front of you.
- **Hunt the line** — plan a path across lanes to chain all pickups in a segment.
- **Trick through obstacles** — a barrel roll through an obstacle lane instead of avoiding it.
- **Ring chains** — rings appear in sequences; committing to a line to hit three consecutive rings is the skill ceiling.

The skate analogy: a beginner rolls through the park. An expert links the manual through the gap into the boardslide. Same park. The expert made their own difficulty.

---

## Music Reactivity — Soft Correlation

Not beat-synced. Mood-mapped.

The goal: the world should feel like it's made of the same stuff as the music, without the player ever consciously noticing a sync.

**Implemented:** particles lerp to active theme color (each segment has its own palette).

**Planned:**
- If BPM metadata is available: obstacle spawn density and pickup arc spacing breathe with tempo.
- Segment theme color palette biased toward cooler/warmer by energy level (loud/fast → warmer accent, slow/quiet → cooler).
- Bloom intensity pulses gently — not on every beat, on musical phrases (every 4–8 bars).

**Hard rule:** if the reactivity ever draws attention to itself ("whoa it just synced"), it's too literal. Dial it back until it's subliminal.

---

## Controls (as of commit 66ce3a9)

| Input | Action |
|---|---|
| Touch swipe left/right | Step one lane (36px threshold) |
| Touch swipe up/down | Step one altitude |
| Touch tap | Barrel roll |
| Mouse hover | Direct position (lane + altitude from cursor X/Y) |
| Mouse click-hold | Activates isActive pressure |
| Arrow keys | Lane/altitude step |
| Space / Enter | Barrel roll |

**Touch feel:** swipe-to-step is intentional. One gesture = one lane. Predictable, low-anxiety, like flicking a skate trick.

**Mouse feel:** hover-follow gives a painterly quality — the owl traces your cursor like a brush. Good for desktop as a ambient companion while working.

---

## Tricks

Currently one trick: **barrel roll**.
- Looks great, adds boost, spikes slipstream particles.
- Triggered by tap or Space.

**Planned:**
- **Wing-tuck dive** — swipe down + trick simultaneously. Fast altitude drop with a speed spike. Looks like a falcon stoop.
- **Soar** — hold up while in high altitude. Owl rises briefly above the corridor with a bloom flash. Pure expression, no mechanical benefit.
- **Trick chaining** — within 0.8s of a trick landing, next trick gets a visual flourish (different particle color, bigger bloom burst). Not a score multiplier — just satisfying to do.

**Design rule:** tricks are always optional. Never require a trick to pass an obstacle. They're expression, not keys.

---

## Visual Direction

Reference: *Alto's Odyssey*, *Monument Valley*, *Sky: Children of the Light*.

**The rules:**
1. Color does the emotional work. Geometry is the skeleton.
2. One saturated accent per scene. Everything else muted.
3. Fog is depth. FogExp2 matched to segment theme — distant objects dissolve rather than pop.
4. Silhouette first — the owl should read in half a second at any size.
5. Emissive materials only for things that matter: feathers, rings, orbs, particle trails, owl eyes.

**Themes (4 implemented, cycling per segment):**
- Blue-teal — cool, nocturnal, the default
- Purple-lavender — dreamy, late-night
- Green-mint — forest, gentle
- Amber-gold — warm, dusk

**Planned biomes** (visual overhaul of segment geometry, not just palette):
- Pine — current default corridor with crystals
- Willow — trailing shapes, lower obstacles, more horizontal spread
- Sakura — petal pickups instead of feathers, softer palette, petals drift downward

Biomes unlock at lifetime feather thresholds. They're cosmetic — same mechanics, different world.

---

## Progression Arc

| Milestone | Unlock |
|---|---|
| 500 feathers lifetime | Willow biome |
| 2,000 feathers lifetime | Sakura biome |
| 10,000 feathers lifetime | Owl skin: Lunar (white + silver) |
| 30,000 feathers lifetime | Owl skin: Ember (dark + amber) |
| 100 consecutive rings | Trail color: Gold |

Milestones are shown as a quiet reveal — no score screen, no fanfare. The world just shifts the next time you land on `/radio`. Like returning to a park and noticing someone added a new feature.

---

## Mechanics Reference

```
LANE_POSITIONS     = [-5.4, -2.7, 0, 2.7, 5.4]   // world X
ALTITUDE_POSITIONS = [1.15, 2.05, 3.1]             // world Y

PLAYER_RADIUS      = 0.7
PICKUP_RADIUS      = 0.42
OBSTACLE_RADIUS    = 0.9
RING_RADIUS        = 1.15
OWL_SCALE          = 0.58

SEGMENT_LENGTH     = 18 units
SEGMENT_COUNT      = 14 (recycled)

Base speed         = 10.9 units/s (playing) / 1.25 (idle)
Max combo boost    = +3.6 units/s
Boost orb          = +3.5 units/s (decays 0.95/s)
Hit penalty        = speed × 0.72, combo reset

Trick (barrel roll):
  trickTimer = 1.0, decays 1.1/s
  boost += 0.3 (cap 2.0)
  slipstream velocity × 3.2 for trick duration

Passive score: +1 feather per 10s of radio play
Active score:  feather=2, arc feather=2, ring=5, boost orb=4

CONTROL_FEEL (lerp alphas by source):
  touch    → move 0.062, bank 0.13
  mouse    → move 0.12,  bank 0.18
  keyboard → move 0.17,  bank 0.24
  idle     → move 0.05,  bank 0.08

Particles:
  Slipstream: 24 particles, cluster near owl, size/opacity scale with speed
  Ambient:    32 particles, wide spread, background texture
  Both pools: color lerps to activeTheme.glow / skyTop per segment
```

---

## Backlog (Prioritized)

| Feature | Why |
|---|---|
| **Artist-bird** — flies ahead, lays seeds as pickups | The soul of the game. Replaces abstract pickups with a relationship |
| **Artist-bird glance-back** — rare head-turn, no reward | The emotional core moment |
| **Artist-bird variation** — subtle color/silhouette per artist | Makes each artist a distinct world you learn to recognize |
| **Seed return gesture** — send collected seeds back to artist | Closes the loop. The game's version of artist support |
| Server-side feather persistence | Seeds mean nothing if they reset on close |
| Biome unlocks (willow, sakura) | Retention, sense of world growing |
| Drop UnrealBloomPass → CSS glow | Mobile performance (biggest single win) |
| Beat-correlation (segment density by tempo) | Music-world connection |
| Wing-tuck dive trick | Expressiveness, speed sensation |
| Soar trick | Pure expression, no mechanical benefit — just beautiful |
| Owl skin: Lunar | First real progression milestone |
| Quiet milestone reveals | Show progression without fanfare |
| Bloom pulse on musical phrases | Subliminal music connection |

---

## File Map

```
spa/src/features/radio-game/
  OwlStage.vue          — Three.js scene, full game loop, all rendering
  useOwlControls.js     — touch/pointer/keyboard input, swipe-to-step

spa/src/views/
  RadioView.vue         — mounts OwlStage, HUD (home button, audio orb,
                          trick button), hint overlay, router

docs/features/
  owl-game-gdd.md       — this document
  radio-owl-game-plan.md — original ambient plan (pre-runner pivot)
  radio-station-manifest.md — radio station architecture
```
