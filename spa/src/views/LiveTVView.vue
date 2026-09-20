<template>
  <div class="tv-container">
    <!-- Subpage hero removed to make video flush at top -->

    <!-- Video Player -->
    <section class="ltv-player-section">
      <div ref="heroPlaceholder" class="ltv-player-wrap" :class="{ 'is-idle': !hasVideoTrack }">

        <!-- 16:9 video area — stage clips height so guide stays visible -->
        <div class="ltv-video-stage" :class="{ 'is-standby': !hasVideoTrack }">
        <div class="ltv-video-frame" :class="{ 'is-standby': !hasVideoTrack }" @click="onHeroClick">
          <video
            ref="heroVideoRef"
            class="ltv-video"
            :class="{ 'is-hidden': !hasVideoTrack }"
            :poster="selectedCurrentSlot?.thumb || '/static/img/u_ahoy23.png'"
            preload="metadata"
            playsinline
            muted
            @loadstart="onHeroVideoLoadStart"
            @canplay="onHeroVideoCanPlay"
            @play="playerStore.isPlaying = true"
            @pause="playerStore.isPlaying = false"
            @loadedmetadata="onHeroVideoMetadata"
            @error="onHeroVideoError"
          ></video>

          <!-- Watermark -->
          <div class="video-watermark" aria-hidden="true">
            <img src="/static/img/u_ahoy23.png" alt="" />
          </div>

          <!-- Empty state -->
          <div v-if="!hasVideoTrack" class="placeholder-content">
            <LiveTvStandbyState
              :kicker="emptyStateKicker"
              :title="emptyStateTitle"
              :body="emptyStateBody"
              :retry-label="loadError ? 'Retry guide' : 'Refresh channel'"
              :show-retry="loadError || !channels.length"
              @retry="handleRetry"
            />
          </div>

          <div v-else-if="loading" class="ltv-status-overlay">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading live channel…</span>
          </div>

          <div v-else-if="heroVideoError" class="ltv-status-overlay is-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>AHOY TV failed to load.</span>
            <button type="button" class="ltv-status-retry" @click.stop="retryCurrentChannel">Retry</button>
          </div>

          <!-- Click-to-watch overlay -->
          <div v-if="hasVideoTrack && !isWatching" class="watch-overlay" @click.stop="watchNow">
            <div class="watch-overlay-inner">
              <div class="watch-play-btn"><i class="fas fa-play"></i></div>
              <span class="watch-overlay-label">Watch with Sound</span>
            </div>
          </div>

          <!-- NOW PLAYING badge -->
          <div v-if="hasVideoTrack" class="ltv-header">
            <span class="ltv-now-playing">Now Playing</span>
            <span class="ltv-channel-name" aria-live="polite">{{ channelLabel }}</span>
          </div>

          <!-- Fullscreen button — lives inside the frame so it always anchors to the video corner -->
          <button
            v-if="hasVideoTrack"
            type="button"
            class="ltv-video-fullscreen"
            title="Fullscreen"
            aria-label="Fullscreen"
            @click.stop="toggleFullscreen"
          >
            <i class="fas fa-expand"></i>
          </button>

          <div class="ltv-glass"></div>
        </div><!-- ltv-video-frame -->
        </div><!-- ltv-video-stage -->

        <!-- Program progress bar (mobile only) -->
        <div v-if="hasVideoTrack" class="ltv-progress-bar mobile-only" aria-hidden="true">
          <div class="ltv-progress-fill" :style="{ width: currentChannelProgress + '%' }"></div>
        </div>

        <!-- Info + controls bar -->
        <div class="ltv-info-bar">
          <LiveTvControlPanel
            :channels="channels"
            :selected-row="selectedRow"
            :channel-label="channelLabel"
            :pinned-channel-title="selectedCurrentSlot?.title || channelLabel"
            :mobile-channel-menu-open="mobileChannelMenuOpen"
            :display-title="displayTitle"
            :display-description="displayDescription"
            :up-next-title="upNextTitle"
            :status-label="mobileStatusLabel"
            :get-channel-bg="getChannelBg"
            :channel-now-title="channelNowTitle"
            :has-video-track="hasVideoTrack"
            :is-watching="isWatching"
            :is-playing="playerStore.isPlaying"
            :is-muted="playerStore.isMuted"
            :is-cast-available="isCastAvailable"
            @select="handleChannelSelect"
            @prev="channelDown"
            @next="channelUp"
            @open-drawer="mobileDrawerOpen = true"
            @toggle-channel-menu="toggleMobileChannelMenu"
            @toggle-play="handlePrimaryAction"
            @toggle-mute="playerStore.toggleMute()"
            @cast="showCastModal = true"
          />
        </div>

        <section v-if="mobileTimelineChannels.length" class="ltv-mobile-timeline mobile-only">
          <div class="ltv-mobile-timeline-kicker">Channels</div>
          <div class="ltv-mobile-channel-list">
            <article
              v-for="channel in mobileTimelineChannels"
              :key="channel.id"
              class="ltv-mobile-channel-row"
              :class="{ active: channel.isActive }"
              role="button"
              tabindex="0"
              @click="handleChannelSelect(channel.index)"
              @keydown.enter="handleChannelSelect(channel.index)"
            >
              <div class="ltv-mobile-channel-row-thumb" :style="getChannelBg(channel.index)"></div>
              <div class="ltv-mobile-channel-row-left">
                <div class="ltv-mobile-channel-row-name">{{ channel.name }}</div>
                <div class="ltv-mobile-channel-row-title">{{ channel.title }}</div>
              </div>
              <div class="ltv-mobile-channel-row-right">
                <span class="ltv-mobile-channel-row-time">{{ channel.timeLabel }}</span>
                <i v-if="channel.isActive" class="fas fa-play ltv-mobile-channel-row-icon"></i>
              </div>
            </article>
          </div>
        </section>

      </div>
    </section>

    <!-- TV Guide section (Moved flush under controls) -->
    <div ref="guideRef" class="live-tv-container guide-flush" aria-label="TV Guide">
      <section class="live-tv-main">
        <div class="guide">
          <div class="guide-header">
            <div>Guide</div>
            <div class="kbd-hint" aria-hidden="true">
              <span>Navigate</span>
              <span class="kbd">&uarr;</span><span class="kbd">&darr;</span>
              <span class="kbd">&larr;</span><span class="kbd">&rarr;</span>
            </div>
          </div>
          <div class="guide-timebar">
            <div v-for="t in timeMarkers" :key="t" class="time-marker" :style="{ minWidth: (30 * pxPerMinute) + 'px' }">{{ t }}</div>
          </div>
          <div class="guide-scroller" :class="{ 'no-scroll': playerStore.isPlaying }" ref="scrollerRef" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp">
            <div class="guide-rows" role="grid" aria-label="Channel Guide">
              <div class="now-line" :style="nowLineStyle"></div>
              <div v-for="(ch, rowIdx) in channels" :key="ch.id" class="guide-row" role="row">
                <div class="guide-channel-label" @click="selectChannel(rowIdx)" @keydown.enter="selectChannel(rowIdx)" tabindex="0">
                  <div class="guide-channel-icon" :style="getChannelBg(rowIdx)" style="background-size: cover; background-position: center; border-radius: 4px;"></div>
                  <div class="guide-channel-name" style="font-weight: bold; font-size: 14px; opacity: 0.9;">{{ ch.name }}</div>
                </div>
                <div class="guide-track">
                  <div
                    v-for="(prog, colIdx) in guidePrograms[rowIdx] || []"
                    :key="rowIdx + '-' + colIdx"
                    class="program"
                    :class="{ selected: guideFocus.row === rowIdx && guideFocus.col === colIdx }"
                    @click="openProgramDetails(prog)"
                    @keydown.enter="openProgramDetails(prog)"
                    :data-row="rowIdx"
                    :data-col="colIdx"
                    tabindex="0"
                    role="gridcell"
                    :aria-label="prog.title + ' • ' + prog.durMin + ' min'"
                    :style="{
                       width: prog.widthPx + 'px',
                       background: 'linear-gradient(165deg, ' + pillColors[rowIdx % 4] + 'bb 0%, ' + pillColors[rowIdx % 4] + '22 100%)',
                       border: '1px solid ' + pillColors[rowIdx % 4] + 'cc', /* crisper borders */
                       backdropFilter: 'blur(16px)',
                       boxShadow: '0 8px 32px rgba(0,0,0,0.4), inset 0 0 15px ' + pillColors[rowIdx % 4] + '22'
                    }"
                  >
                    <!-- No Thumbnail -->
                    <div class="program-title" style="font-size:11px; opacity:0.9">{{ prog.title }}</div>
                    <div class="program-time">{{ prog.timeLabel }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <LiveTvChannelDrawer
        :open="mobileDrawerOpen"
        :channels="channels"
        :selected-row="selectedRow"
        :get-channel-bg="getChannelBg"
        :channel-now-title="channelNowTitle"
        @close="mobileDrawerOpen = false"
        @select="handleChannelSelect"
      />

      <!-- Program Details Modal -->
      <div v-if="selectedProgram" class="program-modal-overlay" @click.self="closeProgramDetails">
        <div class="program-modal">
          <button class="close-btn" @click="closeProgramDetails" aria-label="Close">
            <i class="fas fa-times"></i>
          </button>

          <div class="modal-content">
            <div class="modal-header">
              <h2 class="modal-title">{{ cleanTitle(selectedProgram.title) }}</h2>
              <div class="modal-meta">
                <span class="modal-badge">{{ selectedProgram.category }}</span>
                <span>{{ selectedProgram.durMin }} min</span>
                <span v-if="selectedProgram.timeLabel">{{ selectedProgram.timeLabel }}</span>
              </div>
            </div>

            <div class="modal-body">
              <p class="modal-desc">
                {{ selectedProgram.item?.description || "No description available for this program." }}
              </p>

              <div class="modal-actions">
                <button class="action-btn primary" @click="addToSaved(selectedProgram)">
                  <i class="fas fa-plus"></i> Add to Saved
                </button>
                <!-- Watch Now button if it's currently playing or capable of VOD (future enhancement) -->
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cast Modal -->
      <CastModal v-model="showCastModal" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCasting } from '../composables/useCasting'
import { useLiveTvPlayback } from '../composables/useLiveTvPlayback'
import { useLiveTvSchedule } from '../composables/useLiveTvSchedule'
import { useBookmarks } from '../composables/useBookmarks'
import { usePlayerStore } from '../stores/player'
import { useLiveTvStore } from '../stores/liveTv'
import CastModal from '../components/CastModal.vue'
import LiveTvControlPanel from '../components/live-tv/LiveTvControlPanel.vue'
import LiveTvChannelDrawer from '../components/live-tv/LiveTvChannelDrawer.vue'
import LiveTvStandbyState from '../components/live-tv/LiveTvStandbyState.vue'

const heroPlaceholder = ref(null)
const heroVideoRef = ref(null)
const guideRef = ref(null)
const scrollerRef = ref(null)
const playerStore = usePlayerStore()
const liveTvStore = useLiveTvStore()
const bookmarks = useBookmarks()
const casting = useCasting()
const mobileDrawerOpen = ref(false)
const mobileChannelMenuOpen = ref(false)
const showCastModal = ref(false)

const isCastAvailable = computed(() => casting.isCastingAvailable.value)

const pillColors = ['#00a2ff', '#00ffff', '#0066ff', '#5b21b6']
const pxPerMinute = 6

const {
  channels,
  selectedRow,
  loadError,
  timeMarkers,
  nowLineStyle,
  guidePrograms,
  currentProgramDescription,
  currentChannelProgress,
  channelLabel,
  getCurrentSlot,
  selectedCurrentSlot,
  selectedNextSlot,
  cleanTitle,
  getChannelBg,
  channelNowTitle,
  loadChannels,
  selectChannel,
  channelUp,
  channelDown,
  getFirstPlayableChannelIndex,
} = useLiveTvSchedule({
  liveTvStore,
  pillColors,
  pxPerMinute,
})

const {
  loading,
  heroVideoError,
  isWatching,
  hasVideoTrack,
  playbackState,
  retryCurrentChannel,
  watchNow,
  onHeroClick,
  onHeroVideoMetadata,
  onHeroVideoLoadStart,
  onHeroVideoCanPlay,
  onHeroVideoError,
} = useLiveTvPlayback({
  heroVideoRef,
  playerStore,
  channels,
  selectedRow,
  currentSlot: selectedCurrentSlot,
  getSeekTime: (slot) => {
    const elapsed = Math.max(0, Date.now() - slot.startUTC)
    return Math.max(0, Math.min(Math.floor(elapsed / 1000), slot.durationSec - 1))
  },
})

const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)

function onMouseDown(e) {
  if (playerStore.isPlaying) return
  isDragging.value = true
  startX.value = e.pageX - scrollerRef.value.offsetLeft
  scrollLeft.value = scrollerRef.value.scrollLeft
  scrollerRef.value.style.cursor = 'grabbing'
}

function onMouseMove(e) {
  if (playerStore.isPlaying) return
  if (!isDragging.value) return
  e.preventDefault()
  const x = e.pageX - scrollerRef.value.offsetLeft
  const walk = (x - startX.value) * 1.5
  scrollerRef.value.scrollLeft = scrollLeft.value - walk
}

function onMouseUp() {
  isDragging.value = false
  if (scrollerRef.value) {
    scrollerRef.value.style.cursor = playerStore.isPlaying ? 'default' : 'grab'
  }
}

const guideFocus = ref({ row: 0, col: 0 })

const selectedProgram = ref(null)

function openProgramDetails(prog) {
  selectedProgram.value = prog
}

function closeProgramDetails() {
  selectedProgram.value = null
}

function addToSaved(prog) {
  bookmarks.toggle({
    ...(prog.item || prog),
    id: prog.item?.id || prog.id || prog.title,
    slug: prog.item?.slug || prog.slug,
    title: prog.item?.title || prog.title,
    type: prog.item?.type || 'show',
    _type: 'show',
    cover_art: prog.item?.cover_art || prog.thumb || prog.item?.thumbnail || '',
  })
  closeProgramDetails()
}

const emptyStateKicker = computed(() => {
  if (loadError.value) return 'Signal Lost'
  if (!channels.value.length) return 'Stand By'
  return channelLabel.value
})

const emptyStateTitle = computed(() => {
  if (loadError.value) return 'AHOY TV is having trouble loading'
  if (!channels.value.length) return 'The channel lineup is warming up'
  return 'Choose a channel to start watching'
})

const emptyStateBody = computed(() => {
  if (loadError.value) return 'Try again in a moment or switch channels while the feed reconnects.'
  if (!channels.value.length) return 'We could not load the guide yet. Pull to retry or come back in a moment.'
  return 'Open channels below, pick a live stream, and the player will start here.'
})

const upNextTitle = computed(() => selectedNextSlot.value ? cleanTitle(selectedNextSlot.value.title) : '')

const mobileStatusLabel = computed(() => {
  if (loadError.value || playbackState.value === 'error') return 'Signal Lost'
  if (playbackState.value === 'loading') return 'Loading'
  if (playbackState.value === 'playing') return 'Live with Sound'
  if (playbackState.value === 'preview') return 'Live Preview'
  if (playbackState.value === 'ready') return 'Ready'
  return 'Stand By'
})

const displayTitle = computed(() => (
  hasVideoTrack.value ? channelNowTitle(selectedRow.value) : 'Choose a channel to start watching'
))

const displayDescription = computed(() => {
  if (hasVideoTrack.value) return currentProgramDescription.value
  return 'Pick a live channel below. Browsing and playback stay in separate controls so the page stays calm.'
})

const mobileTimelineChannels = computed(() =>
  channels.value.map((channel, index) => {
    const slot = getCurrentSlot(index)
    return {
      id: channel.id,
      index,
      name: channel.name,
      title: cleanTitle(slot?.title || channelNowTitle(index)),
      timeLabel: slot?.timeLabel || 'Live now',
      isActive: index === selectedRow.value,
    }
  }),
)

function toggleFullscreen() {
  const target = heroVideoRef.value
  const isFullscreen = document.fullscreenElement
    || document.webkitFullscreenElement
    || document.mozFullScreenElement
    || document.msFullscreenElement

  if (!isFullscreen) {
    const requestFs = target?.requestFullscreen
      || target?.webkitRequestFullscreen
      || target?.mozRequestFullScreen
      || target?.msRequestFullscreen
    requestFs?.call(target)?.catch?.(() => {})
  } else {
    const exitFs = document.exitFullscreen
      || document.webkitExitFullscreen
      || document.mozCancelFullScreen
      || document.msExitFullscreen
    exitFs?.call(document)
  }
}

function handleChannelSelect(idx) {
  selectChannel(idx)
  mobileDrawerOpen.value = false
  mobileChannelMenuOpen.value = false
}

function toggleMobileChannelMenu() {
  mobileChannelMenuOpen.value = !mobileChannelMenuOpen.value
}

function handlePrimaryAction() {
  if (!hasVideoTrack.value) {
    mobileDrawerOpen.value = true
    return
  }

  if (isWatching.value) {
    playerStore.togglePlay()
    return
  }

  watchNow()
}

function selectFirstPlayableChannel() {
  if (isMobileLiveTvLayout() && !selectedCurrentSlot.value?.src) {
    const firstPlayableRow = getFirstPlayableChannelIndex()
    if (firstPlayableRow >= 0) {
      selectChannel(firstPlayableRow)
    }
  }
}

async function handleRetry() {
  const loaded = await loadChannels()
  if (loaded) selectFirstPlayableChannel()
  if (hasVideoTrack.value || heroVideoError.value || loadError.value) {
    retryCurrentChannel()
  }
}

function isMobileLiveTvLayout() {
  return typeof window !== 'undefined' && window.matchMedia('(max-width: 768px), (pointer: coarse)').matches
}

function setGuideFocus(row, col) {
  guideFocus.value = { row, col }
}

function onGlobalKeydown(e) {
  if (mobileChannelMenuOpen.value && e.key === 'Escape') {
    e.preventDefault()
    mobileChannelMenuOpen.value = false
    return
  }

  if (!guideRef.value) return
  const rect = guideRef.value.getBoundingClientRect()
  if (rect.bottom < 0 || rect.top > window.innerHeight) return

  const rows = channels.value.length
  if (!rows) return
  const { row, col } = guideFocus.value

  if (e.key === 'ArrowUp') {
    e.preventDefault()
    setGuideFocus(Math.max(0, row - 1), col)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    setGuideFocus(Math.min(rows - 1, row + 1), col)
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    const maxCol = (guidePrograms.value[row]?.length || 1) - 1
    setGuideFocus(row, Math.min(maxCol, col + 1))
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    setGuideFocus(row, Math.max(0, col - 1))
  } else if (e.key === 'Enter') {
    e.preventDefault()
    selectChannel(guideFocus.value.row)
  }
}

function updateBounds() {
  if (heroPlaceholder.value) {
    const rect = heroPlaceholder.value.getBoundingClientRect()
    playerStore.setHeroBounds({
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height
    })
  }
}

let rafTracker = null
function startBoundsTracking() {
  updateBounds()
  rafTracker = requestAnimationFrame(startBoundsTracking)
}

onMounted(async () => {
  document.addEventListener('keydown', onGlobalKeydown)
  await loadChannels()
  selectFirstPlayableChannel()

  startBoundsTracking()
})

onUnmounted(() => {
  if (rafTracker) cancelAnimationFrame(rafTracker)
  document.removeEventListener('keydown', onGlobalKeydown)
  window.removeEventListener('resize', updateBounds)
  playerStore.setHeroBounds(null)
})
</script>

<style scoped>
/* Override global .tv-container which has display:grid from index.css */
.tv-container {
  display: flex !important;
  flex-direction: column;
  background: #000;
  min-height: 0;
  height: 100%;
  color: #e5e7eb;
  width: 100%;
}

/* ===== Player: fully self-contained, no global class conflicts ===== */
.ltv-player-section {
  width: 100%;
  background: #000;
  display: block;
}

@media (max-width: 768px), (pointer: coarse) {
  .ltv-player-section {
    padding: 36px 12px 20px !important;
  }
}

.ltv-player-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.ltv-status-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.52);
  color: rgba(255, 255, 255, 0.92);
  font-weight: 600;
}

.ltv-status-overlay.is-error {
  background: rgba(15, 4, 4, 0.78);
}

.ltv-status-retry {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  padding: 8px 14px;
  font-weight: 700;
  cursor: pointer;
}

/* Stage: clips the video frame so it never taller than viewport - controls */
.ltv-video-stage {
  width: 100%;
  /* natural 16:9 height but never more than viewport minus navbar+infobar+guide */
  height: min(56.25vw, calc(100vh - 280px));
  min-height: 180px;
  overflow: hidden;
  background: #000;
  position: relative;
}

/* Frame: always 16:9 at full width; stage clips whatever overflows */
.ltv-video-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
  overflow: hidden;
  cursor: pointer;
}

/* Video fills the frame completely regardless of source aspect ratio */
.ltv-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  background: #000;
}

.ltv-video.is-hidden {
  opacity: 0;
  pointer-events: none;
}

/* Info bar below the video — now a shell for the dedicated control panel */
.ltv-info-bar {
  display: block;
  width: 100%;
  padding: 14px 0 0;
  background: transparent;
  border-top: 0;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

@media (max-width: 768px), (pointer: coarse) {
  .ltv-info-bar {
    padding-top: 0;
  }
}

@media (max-width: 768px), (pointer: coarse) {
  .ltv-player-wrap {
    width: min(100%, 720px);
    align-items: center;
    margin: 0 auto;
  }
  .ltv-video-stage {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    height: auto;
    min-height: 0;
    overflow: hidden;
  }
  .ltv-video-frame {
    width: 100%;
    margin: 0 auto;
    border-radius: 24px 24px 0 0;
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.45);
  }
  .ltv-video-frame.is-standby {
    aspect-ratio: 4 / 3;
    min-height: 352px;
  }
  .placeholder-content {
    padding: 28px 24px;
    background:
      radial-gradient(circle at top, rgba(79, 140, 255, 0.28), transparent 42%),
      linear-gradient(180deg, rgba(4, 10, 24, 0.92) 0%, rgba(3, 6, 14, 0.98) 100%);
  }
  .video-watermark {
    top: 10px;
    right: 10px;
    left: auto;
    bottom: auto;
    width: 36px;
    height: 36px;
    opacity: 0.74;
  }
  .video-watermark img {
    width: 100%;
  }
  .ltv-video-fullscreen {
    width: 38px;
    height: 38px;
  }
  .ltv-header {
    left: 56px;
  }
}

.placeholder-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #e5e7eb;
  z-index: 1;
}
.video-watermark {
  position: absolute;
  top: 16px;
  right: 16px;
  left: auto;
  bottom: auto;
  z-index: 6;
  pointer-events: none;
  width: 48px;
  height: 48px;
  opacity: 0.8;
}
.video-watermark img {
  display: block;
  width: 100%;
  height: auto;
  filter: drop-shadow(0 4px 14px rgba(0, 0, 0, 0.55));
}
.ltv-video-fullscreen {
  position: absolute;
  bottom: 14px;
  right: 14px;
  z-index: 10;
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
  cursor: pointer;
}
.ltv-video-fullscreen:hover {
  background: rgba(0, 0, 0, 0.58);
  border-color: rgba(255, 255, 255, 0.24);
}
.ltv-header {
  position: absolute;
  top: 12px;
  left: 64px;
  display: flex;
  gap: 10px;
  align-items: center;
  z-index: 6;
}
.ltv-now-playing {
  background: rgba(59, 130, 246, 0.22);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(59, 130, 246, 0.35);
  padding: 4px 10px 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.ltv-now-playing::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff3b5e;
  flex-shrink: 0;
  animation: ltv-live-pulse 1.6s ease-in-out infinite;
}
@keyframes ltv-live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.ltv-channel-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.75);
  text-shadow: 0 1px 6px rgba(0,0,0,0.8);
}
.ltv-glass {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(transparent, rgba(0,0,0,0.5));
  pointer-events: none;
  z-index: 2;
}

/* ===== Watch-with-Sound Overlay ===== */
.watch-overlay {
  position: absolute;
  inset: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.28);
  transition: background 0.2s;
}
.watch-overlay:hover {
  background: rgba(0, 0, 0, 0.45);
}
.watch-overlay-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  pointer-events: none;
}
.watch-play-btn {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 2px solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
  transition: transform 0.2s, background 0.2s;
}
.watch-overlay:hover .watch-play-btn {
  transform: scale(1.08);
  background: rgba(255, 255, 255, 0.22);
}
.watch-overlay-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7);
}

.guide-flush {
  margin-top: 0 !important;
  padding-top: 0 !important;
}

.ltv-mobile-timeline {
  display: none;
}



/* ===== Channel selector empty / retry (mobile-friendly) ===== */
.channel-selector-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 16px;
  text-align: center;
  min-height: 120px;
}
.channel-selector-empty-text {
  font-size: 16px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 0;
}
.channel-selector-empty-hint {
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
}
.channel-selector-retry {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 10px;
  background: #3b82f6;
  border: none;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  font-family: inherit;
  margin-top: 4px;
}
.channel-selector-retry:hover {
  background: #2563eb;
}
.channel-selector-retry:active {
  transform: scale(0.98);
}

/* ===== Hover Preview ===== */
.live-tv-channel-preview {
  position: fixed;
  z-index: 9999;
  width: 280px;
  max-width: 90vw;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s ease;
}
.live-tv-channel-preview.visible {
  opacity: 1;
}
.live-tv-channel-preview img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}
.live-tv-channel-preview-title {
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  line-height: 1.3;
}
.live-tv-channel-preview-meta {
  padding: 0 12px 10px;
}

.tv-container {
  padding-bottom: 2rem;
}

/* CAROUSEL & LIQUID GLASS STYLES */
.liquid-glass-wrap {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 20px;
  background: rgba(0,0,0,0.5);
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

/* Modern Glass Player Updates */
.modern-glass-player {
  position: relative;
  width: 100%;
  background: #000;
  display: flex;
  flex-direction: column;
}

.video-container-inner {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.liquid-glass-overlay.static-overlay {
  position: relative;
  inset: auto;
  opacity: 1; /* Always show when not overlaying */
  background: rgba(0,0,0,0.3);
  padding: 1.5rem 2rem;
  border-top: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(12px) saturate(120%);
  -webkit-backdrop-filter: blur(12px) saturate(120%);
  border-radius: 0 0 20px 20px;
  pointer-events: auto;
  transition: none;
}

.embedded-video-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0;
}

/* ========================================= */
.live-tv-container {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  background: #000;
}
.live-tv-sidebar {
  background: #0f0f0f;
  border-radius: 0;
  padding: 8px;
  border-right: 1px solid rgba(255,255,255,0.05);
}
.channel-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.channel-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
}
.channel-item[aria-selected="true"] {
  background: #222;
  outline: 2px solid #444;
}
.channel-pill {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.channel-name {
  font-weight: 600;
  letter-spacing: 0.25px;
}

.live-tv-main {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
}

.guide {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  background: var(--background-dark, #040810);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-color, rgba(0, 162, 255, 0.1));
  border-radius: 0; /* Flush */
  padding: 0;
  overflow: auto;
  margin-top: 0; /* Flush under player */
  width: 100%;
}
.guide-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.03);
  font-weight: 800;
  font-size: 1.1rem;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.kbd-hint {
  font-size: 12px;
  opacity: 0.75;
  margin-left: auto;
  display: flex;
  gap: 8px;
  align-items: center;
}
.kbd {
  border: 1px solid #333;
  background: #151515;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.guide-timebar {
  position: sticky;
  top: 0;
  background: rgba(8, 18, 36, 0.9);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  z-index: 10;
  padding: 12px 20px;
  display: flex;
  gap: 24px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: nowrap;
}
.time-marker {
  color: #bbb;
  font-size: 12px;
  text-align: left;
  flex: 0 0 auto;
}
.guide-scroller {
  overflow-x: auto;
  overflow-y: visible;
  flex: 1 1 auto;
  min-height: 0;
}
.guide-scroller.no-scroll {
  overflow-x: hidden !important;
  cursor: default !important;
}
.guide-rows {
  position: relative;
}
.guide-row {
  display: flex;
  gap: 8px;
  align-items: stretch;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}
.guide-channel-label {
  width: 160px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
  padding: 4px 6px;
  transition: background 0.15s;
}
.guide-channel-label:hover {
  background: rgba(255,255,255,0.07);
}
.guide-channel-label:focus {
  outline: 2px solid #00a2ff;
  outline-offset: 2px;
}
.guide-channel-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: inline-block;
  flex-shrink: 0;
  object-fit: cover;
  background-size: cover;
  background-position: center;
  border: 1px solid rgba(255,255,255,0.1);
}
.guide-track {
  position: relative;
  display: flex;
  gap: 8px;
  min-width: 1200px;
}
.program {
  /* Neuromorphic block style */
  border-radius: 12px;
  padding: 8px 12px;
  min-width: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}
.program::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
  pointer-events: none;
}
.program:hover {
  transform: translateY(-2px);
  filter: brightness(1.25);
  cursor: pointer; /* Now interactive */
  border-color: rgba(255, 255, 255, 0.6) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
}
/* Add a subtle play icon on hover to make it obvious it plays */
.program::before {
  content: '\f04b'; /* FontAwesome play icon */
  font-family: 'Font Awesome 5 Free', 'Font Awesome 6 Free';
  font-weight: 900;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0.5);
  color: rgba(255, 255, 255, 0.9);
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.6));
}
.program:hover::before {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1.2);
}
.program-title {
  font-weight: 600;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.9;
}
.program-time {
  font-size: 10px;
  line-height: 1.2;
  opacity: 0.72;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.program:focus {
  outline: 2px solid #4f46e5;
}
.program.selected {
  border-color: #00a2ff;
  box-shadow: 0 0 0 2px rgba(0,162,255,0.35) inset;
}
.now-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #00a2ff;
  box-shadow: 0 0 15px rgba(0, 162, 255, 0.8);
  z-index: 5;
  pointer-events: none;
}
.now-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  background: #00a2ff;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 162, 255, 1);
}

/* ===== Program Pop-up Modal ===== */
.program-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(5px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.program-modal {
  background: #1a1a1a;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
  position: relative;
  overflow: hidden;
  animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes modalPop {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@media (max-width: 768px), (pointer: coarse) {
  .program-modal-overlay {
    align-items: flex-end;
    padding: 0;
  }
  .program-modal {
    max-width: 100%;
    border-radius: 24px 24px 0 0;
    animation: modalSlideUp 0.28s cubic-bezier(0.32, 0.72, 0, 1);
    padding-bottom: env(safe-area-inset-bottom);
  }
}

@keyframes modalSlideUp {
  from { transform: translateY(100%); opacity: 0.8; }
  to { transform: translateY(0); opacity: 1; }
}
.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.1);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 2;
}
.close-btn:hover { background: rgba(255,255,255,0.2); }

.modal-content {
  padding: 24px;
}
.modal-header {
  margin-bottom: 16px;
}
.modal-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  line-height: 1.3;
}
.modal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 13px;
  color: #9ca3af;
  align-items: center;
}
.modal-badge {
  background: #0066ff;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
}
.modal-body {
  color: #d1d5db;
}
.modal-desc {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 24px;
  opacity: 0.9;
}
.modal-actions {
  display: flex;
  gap: 12px;
}
.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}
.action-btn.primary {
  background: #fff;
  color: #000;
}
.action-btn.primary:hover {
  background: #f3f4f6;
}
.action-btn.primary:active {
  transform: scale(0.97);
}

/* ===== Mobile ===== */
.mobile-only { display: none; }
.hidden-mobile {}
.channels-btn {
  background: #1d1d1f;
  border: 1px solid #2a2a2a;
  color: #e5e7eb;
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

/* Mobile Channels button: visible only on small screens */
.mobile-channels-btn {
  display: none;
}
.mobile-channels-label {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 600;
}

@media (max-width: 900px) {
  .spotlight-grid {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 0 8px;
  }
  .right-dashboard {
    position: relative;
    top: 0;
    max-height: none;
    margin-top: 12px;
  }
  .live-tv-container {
    grid-template-columns: 1fr;
  }
  .live-tv-main {
    grid-template-columns: 1fr;
  }
  #channel-selector {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

@media (max-width: 768px), (pointer: coarse) {
  .podcasts-hero {
    padding: 20px 0;
  }
  .podcasts-hero h1 {
    font-size: 24px;
  }
  .mobile-only {
    display: initial;
  }
  .hidden-mobile {
    display: none !important;
  }
  
  .spotlight-grid {
    flex-direction: column;
    gap: 0;
    padding: 0;
  }

  .ltv-header {
    top: 8px;
    left: 12px;
  }
  .ltv-now-playing {
    padding: 2px 6px;
    font-size: 10px;
  }
  .ltv-channel-name {
    font-size: 11px;
  }

  .ltv-progress-bar {
    width: 100%;
    height: 3px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
  }
  .ltv-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, rgba(109, 149, 255, 0.9), rgba(154, 193, 255, 0.7));
    transition: width 1s linear;
    border-radius: 0 2px 2px 0;
  }

  .remote-btn {
    width: 40px;
    height: 40px;
    font-size: 14px;
  }

  /* Show mobile Channels button; hide "Go to Guide" (guide is hidden on mobile) */
  .mobile-channels-btn {
    display: inline-flex;
    align-items: center;
    min-width: auto;
    padding: 0 12px;
  }
  .remote-btn[title="Go to Guide"] {
    display: none;
  }

  .playing-now {
    padding: 8px;
    gap: 8px;
  }
  .playing-now img {
    width: 40px;
    height: 28px;
  }
  .np-title { font-size: 13px; }
  .np-sub { font-size: 10px; }
  .np-next { font-size: 12px; }

  .ltv-mobile-timeline {
    display: block;
    width: 100%;
    margin-top: 20px;
    padding: 0 12px;
    box-sizing: border-box;
  }
  .ltv-mobile-timeline-kicker {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(154, 193, 255, 0.8);
    margin-bottom: 10px;
  }
  .ltv-mobile-channel-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ltv-mobile-channel-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.07);
    background: rgba(255, 255, 255, 0.04);
    cursor: pointer;
    overflow: hidden;
    transition: background 0.12s, border-color 0.12s;
  }
  .ltv-mobile-channel-row:active {
    background: rgba(255, 255, 255, 0.1);
  }
  .ltv-mobile-channel-row.active {
    border-color: rgba(109, 149, 255, 0.34);
    background: rgba(66, 100, 206, 0.18);
  }
  .ltv-mobile-channel-row-thumb {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    border-radius: 10px;
    background-size: cover;
    background-position: center;
    background-color: rgba(255,255,255,0.08);
  }
  .ltv-mobile-channel-row-left {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .ltv-mobile-channel-row-name {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(154, 193, 255, 0.82);
  }
  .ltv-mobile-channel-row.active .ltv-mobile-channel-row-name {
    color: rgba(180, 210, 255, 0.95);
  }
  .ltv-mobile-channel-row-title {
    font-size: 14px;
    font-weight: 700;
    color: #f0f4ff;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ltv-mobile-channel-row-right {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 8px;
  }
  .ltv-mobile-channel-row-time {
    font-size: 11px;
    color: rgba(229, 231, 235, 0.6);
    white-space: nowrap;
  }
  .ltv-mobile-channel-row-icon {
    font-size: 10px;
    color: rgba(154, 193, 255, 0.9);
  }

  /* Guide Responsive */
  .live-tv-container {
    display: none !important; /* Re-hide the guide on mobile as per user preference */
  }
}

@media (max-width: 480px) {
  .channel-button-name { font-size: 16px; }
  .channel-button-next { font-size: 12px; }
}

@media (max-width: 768px), (pointer: coarse) {
  .tv-container {
    min-height: auto;
    padding-bottom: var(--mobile-bottom-clear-sm, 80px); /* Space for bottom dock */
  }
  .spotlight-grid {
    flex-direction: column;
    gap: 0;
  }
  .video-spotlight {
    padding: 0; /* Full width player */
  }
  .ltv-player-box {
    border-radius: 0;
  }
  .placeholder-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #444;
    font-weight: 600;
  }
  .guide-scroller {
    cursor: grab;
    user-select: none;
  }
  .guide-scroller::-webkit-scrollbar {
    height: 6px;
  }
  .guide-scroller::-webkit-scrollbar-track {
    background: transparent;
  }
  .guide-scroller::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
  }
  .guide-scroller::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.1);
  }
  .tv-container, .live-tv-container, .live-tv-sidebar, .guide {
    background: #050505; /* Blacker harmonize */
  }
  .live-tv-sidebar {
    background: #080808;
    border-right-color: rgba(255,255,255,0.04);
  }
  .rd-suggested-title {
    font-size: 11px;
    text-transform: uppercase;
    color: #555;
    margin-top: 20px;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
  }
  .rd-suggested-item {
    display: flex;
    gap: 10px;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    cursor: pointer;
  }
  .rd-suggested-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }
  .rd-suggested-name {
    font-size: 12px;
    font-weight: 500;
  }
  .rd-suggested-meta {
    font-size: 10px;
    opacity: 0.4;
    margin-left: auto;
  }

  .channel-remote {
    padding: 0 12px;
    justify-content: space-between;
  }
  .remote-btn {
    width: 44px;
    height: 44px; /* Larger touch target */
    font-size: 16px;
  }
  #channel-selector {
    padding: 12px;
    grid-template-columns: 1fr; /* Stack channels */
  }
}
</style>
