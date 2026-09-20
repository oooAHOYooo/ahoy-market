<template>
  <div class="radio-home">

    <!-- Page header (responsive: compact on mobile, big on desktop) -->
    <div class="radio-page-head">
      <span class="radio-head-kicker">Ahoy Indie Media</span>
      <h1 class="radio-head-title">Radio</h1>
    </div>

    <!-- Main on-air card -->
    <div class="radio-card" :class="{ 'is-audible': isRadioAudible, 'is-loading': isLoading }">

      <!-- Art + overlay info -->
      <div class="radio-art-frame">
        <Transition name="art-xfade">
          <img v-if="stationArt" :key="stationArt" :src="stationArt" alt="" class="radio-art" />
          <div v-else key="placeholder" class="radio-art-empty">
            <i class="fas fa-radio" aria-hidden="true"></i>
          </div>
        </Transition>
        <div class="radio-veil"></div>
        <div class="radio-overlay">
          <span class="radio-live-tag" :class="{ 'is-on': isRadioAudible }">
            <span class="radio-live-dot"></span>
            Live
          </span>
          <p class="radio-now-title">{{ stationTitle }}</p>
          <p v-if="stationArtist" class="radio-now-artist">{{ stationArtist }}</p>
        </div>
      </div>

      <!-- Progress bar + timestamps -->
      <div class="radio-scrubber">
        <div class="radio-progress">
          <div class="radio-progress-fill" :style="{ width: progressPct + '%' }" />
        </div>
        <div class="radio-times">
          <span>{{ formatTime(elapsed) }}</span>
          <span>-{{ formatTime(remaining) }}</span>
        </div>
      </div>

      <!-- Error / retry state -->
      <div v-if="loadFailed && !isLoading" class="radio-error">
        <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
        <span>Couldn't reach the station</span>
        <button type="button" class="radio-retry" @click="emit('retry')">Retry</button>
      </div>

      <!-- Tune In / Mute button -->
      <button
        v-else
        type="button"
        class="radio-tune"
        :class="{ 'is-active': isRadioAudible }"
        :disabled="!stationCurrent || isLoading"
        :aria-label="radioToggleLabel"
        @click="emit('toggle-radio')"
      >
        <span class="radio-tune-orb">
          <i class="fas" :class="radioButtonIcon" aria-hidden="true"></i>
        </span>
        <span class="radio-tune-label">{{ radioToggleLabel }}</span>
      </button>

    </div>

    <!-- Just Played — retroactive info only, no interaction -->
    <section v-if="justPlayed && justPlayed.length" class="radio-queue-section">
      <p class="queue-eyebrow">Just Played</p>
      <div class="radio-queue">
        <div
          v-for="(track, i) in justPlayed"
          :key="track.id || i"
          class="queue-item"
        >
          <div class="queue-thumb">
            <img v-if="track.cover_art" :src="track.cover_art" alt="" class="queue-img" />
            <i v-else class="fas fa-music queue-icon" aria-hidden="true"></i>
          </div>
          <div class="queue-meta">
            <span class="queue-title">{{ track.title || track.name || 'Untitled' }}</span>
            <span class="queue-artist">{{ track.artist || track.artist_name || 'Ahoy Artist' }}</span>
          </div>
          <span class="queue-dur">{{ formatTime(track.duration_seconds || 180) }}</span>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isRadioAudible: { type: Boolean, required: true },
  radioButtonIcon: { type: String, required: true },
  radioToggleLabel: { type: String, required: true },
  stationArt: { type: String, default: '' },
  stationArtist: { type: String, default: '' },
  stationCurrent: { type: Object, default: null },
  stationTitle: { type: String, required: true },
  elapsed: { type: Number, default: 0 },
  justPlayed: { type: Array, default: () => [] },
  isLoading: { type: Boolean, default: false },
  loadFailed: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-radio', 'retry'])

const duration = computed(() => props.stationCurrent?.duration_seconds || 180)
const progressPct = computed(() => Math.min(100, (props.elapsed / duration.value) * 100))
const remaining = computed(() => Math.max(0, duration.value - props.elapsed))

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds))
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* ─── Container ─────────────────────────────────────────── */
.radio-home {
  width: 100%;
  max-width: 560px;
}

/* ─── Page header ────────────────────────────────────────── */
/* Hidden on mobile — LIVE badge + overlay text is enough context */
.radio-page-head {
  display: none;
}

.radio-head-kicker {
  display: block;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(0, 215, 255, 0.8);
  margin-bottom: 0.2rem;
}

.radio-head-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: #fff;
  line-height: 1;
}

/* ─── Main card ─────────────────────────────────────────── */
.radio-card {
  background: rgba(10, 10, 18, 0.78);
  border: 1.5px solid rgba(0, 215, 255, 0.22);
  border-radius: 20px;
  overflow: hidden;
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
  margin-bottom: 1rem;
}

.radio-card.is-audible {
  border-color: rgba(255, 47, 184, 0.42);
  box-shadow: 0 0 32px rgba(255, 47, 184, 0.13), 0 18px 44px rgba(0, 0, 0, 0.42);
}

/* ─── Art frame ─────────────────────────────────────────── */
.radio-art-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9; /* 16:9 on mobile — fits the whole page without scrolling */
  background: #08080f;
  overflow: hidden;
}

.radio-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.radio-art-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(0, 215, 255, 0.07) 0%, rgba(255, 47, 184, 0.06) 100%);
  color: rgba(0, 215, 255, 0.28);
  font-size: 5rem;
}

/* Pulsing glow on art frame border when live and audible */
.radio-card.is-audible .radio-art-frame {
  box-shadow: 0 0 0 0 rgba(255, 47, 184, 0);
  animation: art-glow-pulse 3s ease-in-out infinite;
}

@keyframes art-glow-pulse {
  0%, 100% { box-shadow: 0 0 18px 2px rgba(255, 47, 184, 0.18); }
  50%       { box-shadow: 0 0 38px 8px rgba(255, 47, 184, 0.36); }
}

/* Gradient veil for text legibility over art */
.radio-veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent 30%, rgba(5, 5, 15, 0.94) 100%);
  pointer-events: none;
}

/* Overlaid track info at bottom of art */
.radio-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.9rem 1rem;
}

.radio-live-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.38rem;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.38);
  margin-bottom: 0.38rem;
}

.radio-live-dot {
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.radio-live-tag.is-on {
  color: #ff2fb8;
}

.radio-live-tag.is-on .radio-live-dot {
  box-shadow: 0 0 7px rgba(255, 47, 184, 0.85);
  animation: blink-dot 1.5s ease-in-out infinite;
}

@keyframes blink-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}

.radio-now-title {
  margin: 0 0 0.15rem;
  font-size: 1.15rem;
  font-weight: 900;
  color: #fff;
  line-height: 1.15;
  letter-spacing: -0.01em;
}

.radio-now-artist {
  margin: 0;
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.65);
}

/* ─── Scrubber ───────────────────────────────────────────── */
.radio-scrubber {
  padding: 0.8rem 1rem 0.45rem;
}

.radio-progress {
  height: 3px;
  background: rgba(255, 255, 255, 0.09);
  border-radius: 999px;
  overflow: hidden;
}

.radio-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00d7ff 0%, #64baff 100%);
  border-radius: 999px;
  transition: width 1s linear;
}

.radio-card.is-audible .radio-progress-fill {
  background: linear-gradient(90deg, #ff2fb8 0%, #ff80cf 100%);
}

.radio-times {
  display: flex;
  justify-content: space-between;
  font-size: 0.67rem;
  color: rgba(255, 255, 255, 0.36);
  margin-top: 0.32rem;
  font-variant-numeric: tabular-nums;
}

/* ─── Tune In / Mute button ──────────────────────────────── */
.radio-tune {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  width: calc(100% - 2rem);
  margin: 0 1rem 1rem;
  padding: 1.05rem 1.5rem; /* taller on mobile — easier to tap while driving */
  min-height: 54px;
  border: 2px solid #00d7ff;
  border-radius: 12px;
  background: rgba(0, 215, 255, 0.05);
  color: #00d7ff;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease,
              transform 0.14s ease, box-shadow 0.2s ease;
}

.radio-tune:hover:not(:disabled) {
  background: rgba(0, 215, 255, 0.12);
  box-shadow: 0 4px 18px rgba(0, 215, 255, 0.18);
  transform: translateY(-1px);
}

.radio-tune.is-active {
  border-color: #ff2fb8;
  color: #ff2fb8;
  background: rgba(255, 47, 184, 0.05);
}

.radio-tune.is-active:hover:not(:disabled) {
  background: rgba(255, 47, 184, 0.12);
  box-shadow: 0 4px 18px rgba(255, 47, 184, 0.18);
}

.radio-tune:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  transform: none;
}

.radio-tune-orb {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.radio-tune-orb .fas {
  color: #0a0a12;
  font-size: 0.72rem;
}

/* ─── Up Next ─────────────────────────────────────────────── */
.radio-queue-section {
  background: rgba(10, 10, 18, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  margin-bottom: 1rem;
}

.queue-eyebrow {
  margin: 0;
  padding: 0.72rem 1rem 0.6rem;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(0, 215, 255, 0.65);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.62rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  opacity: 0.62; /* "past" — visually distinct from something you could act on */
}
.queue-item:last-child { border-bottom: none; }

.queue-thumb {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  display: grid;
  place-items: center;
}

.queue-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.queue-icon {
  color: rgba(255, 255, 255, 0.22);
  font-size: 0.9rem;
}

.queue-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.14rem;
}

.queue-title {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.88);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-artist {
  display: block;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.44);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-dur {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.28);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* ─── Error state ────────────────────────────────────────── */
.radio-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  width: calc(100% - 2rem);
  margin: 0 1rem 1rem;
  padding: 1.05rem 1.5rem;
  min-height: 54px;
  border-radius: 12px;
  background: rgba(255, 60, 60, 0.07);
  border: 1.5px solid rgba(255, 80, 80, 0.28);
  color: rgba(255, 120, 120, 0.9);
  font-size: 0.88rem;
  font-weight: 600;
}

.radio-retry {
  margin-left: auto;
  padding: 0.3rem 0.9rem;
  border-radius: 8px;
  border: 1.5px solid rgba(255, 120, 120, 0.5);
  background: transparent;
  color: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.18s ease;
}

.radio-retry:hover {
  background: rgba(255, 80, 80, 0.12);
}

/* ─── Art crossfade ──────────────────────────────────────── */
.art-xfade-enter-active,
.art-xfade-leave-active {
  transition: opacity 0.7s ease;
}
.art-xfade-enter-from,
.art-xfade-leave-to {
  opacity: 0;
}
.art-xfade-leave-active {
  position: absolute;
  inset: 0;
}

/* ─── Reduced motion ─────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .art-xfade-enter-active,
  .art-xfade-leave-active { transition: none; }
  .radio-card.is-audible .radio-art-frame { animation: none; }
  .radio-live-tag.is-on .radio-live-dot { animation: none; }
}

/* ─── Desktop ────────────────────────────────────────────── */
@media (min-width: 1025px) {
  .radio-home {
    width: min(100%, 1120px);
    max-width: 1120px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 320px;
    grid-template-areas:
      "head head"
      "main queue"
      "main queue";
    gap: 1rem 1.5rem;
    align-items: start;
  }

  .radio-page-head {
    display: block;
    grid-area: head;
    padding: 1rem 0 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 0;
  }

  .radio-head-kicker {
    font-size: 11px;
    color: #6ddcff;
    margin-bottom: 0.5rem;
  }

  .radio-head-title {
    font-size: clamp(2.2rem, 3.5vw, 2.8rem);
    margin-bottom: 0;
  }

  .radio-card {
    grid-area: main;
    margin-bottom: 0;
  }

  .radio-art-frame {
    aspect-ratio: unset;
    height: 320px;
  }

  .radio-scrubber {
    padding-top: 0.7rem;
  }

  .radio-tune {
    margin-bottom: 0.85rem;
  }

  .radio-now-title { font-size: 1.22rem; }

  .radio-queue-section {
    grid-area: queue;
    margin-bottom: 0;
    align-self: start;
    position: sticky;
    top: 1rem;
  }
}
</style>
