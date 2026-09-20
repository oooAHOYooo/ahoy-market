import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { apiFetch, apiFetchCached } from './useApi'

const DEFAULT_COVER = ''
const FALLBACK_PLACEHOLDER_TITLES = ['Broadcast', 'Live Segment', 'Commercial Break', 'Station ID']

function getAnchorTime() {
  const now = new Date()
  const ms = 1000 * 60 * 30
  return new Date(Math.floor(now.getTime() / ms) * ms)
}

function diffMinutes(a, b) {
  return Math.round((b.getTime() - a.getTime()) / 60000)
}

function getVideoUrl(item) {
  return item?.video_url || item?.mp4_link || item?.trailer_url || ''
}

function normalizeItem(item, index, channelName) {
  const durationSec = Math.max(300, Number(item?.duration_seconds) || 300)
  const src = getVideoUrl(item)

  return {
    ...item,
    id: item?.id ?? `${channelName}-${index}`,
    title: item?.title || 'Untitled',
    category: item?.category || channelName || 'Show',
    description: item?.description || '',
    thumbnail: item?.thumbnail || '',
    duration_seconds: durationSec,
    video_url: src,
    playbackSrc: src,
  }
}

function buildPlaceholderItems(channelName) {
  return Array.from({ length: 24 }, (_, index) =>
    normalizeItem(
      {
        title: `${FALLBACK_PLACEHOLDER_TITLES[index % FALLBACK_PLACEHOLDER_TITLES.length]} #${index + 1}`,
        duration_seconds: 3600,
        category: channelName,
      },
      index,
      channelName,
    ),
  )
}

function normalizeChannel(channel, index) {
  const name = channel?.name ?? 'Channel'
  const items = Array.isArray(channel?.items) && channel.items.length
    ? channel.items.map((item, itemIndex) => normalizeItem(item, itemIndex, name))
    : buildPlaceholderItems(name)

  return {
    ...channel,
    id: channel?.id ?? `channel-${index + 1}`,
    name,
    items,
  }
}

export function useLiveTvSchedule({
  liveTvStore,
  horizonMinutes = 180,
  pxPerMinute = 6,
  pillColors = ['#00a2ff', '#00ffff', '#0066ff', '#5b21b6'],
} = {}) {
  const channels = ref([])
  const selectedRow = ref(Number(liveTvStore?.selectedChannelIdx) || 0)
  const loadError = ref(false)
  const gridStart = ref(getAnchorTime())
  const nowMs = ref(Date.now())
  const generatedThumbs = ref({})

  const thumbQueue = []
  let thumbsInFlight = 0
  let uiTimer = null
  let boundaryTimer = null

  const rowLabels = computed(() =>
    channels.value.map((channel, index) => `Channel ${String(index + 1).padStart(2, '0')} — ${channel.name}`),
  )

  function fmtTime(date) {
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  }

  function cleanTitle(title) {
    if (!title) return 'Untitled'
    return title.replace(/\[[^\]]*\]/g, '').replace(/\([^)]*\)/g, '').trim() || 'Untitled'
  }

  function getThumbnail(item, videoUrl) {
    if (item?.thumbnail) return item.thumbnail
    const url = videoUrl || getVideoUrl(item)
    if (url && generatedThumbs.value[url]) return generatedThumbs.value[url]
    return DEFAULT_COVER
  }

  function captureVideoFrame(videoUrl) {
    return new Promise((resolve, reject) => {
      if (!videoUrl || typeof videoUrl !== 'string') {
        reject(new Error('Invalid video URL'))
        return
      }

      const video = document.createElement('video')
      video.muted = true
      video.playsInline = true
      video.crossOrigin = 'anonymous'
      video.preload = 'metadata'

      const timeout = setTimeout(() => {
        video.src = ''
        video.load()
        reject(new Error('Timeout'))
      }, 15000)

      video.onerror = () => {
        clearTimeout(timeout)
        reject(new Error('Video load failed'))
      }

      video.onloadeddata = () => {
        const t = Math.min(1, Math.max(0, video.duration ? video.duration * 0.05 : 1))
        video.currentTime = t
      }

      video.onseeked = () => {
        clearTimeout(timeout)
        try {
          const canvas = document.createElement('canvas')
          const width = 320
          const height = Math.round((video.videoHeight / video.videoWidth) * width) || 180
          canvas.width = width
          canvas.height = height
          const context = canvas.getContext('2d')
          if (!context) {
            resolve(null)
            return
          }
          context.drawImage(video, 0, 0, width, height)
          const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
          video.src = ''
          video.load()
          resolve(dataUrl)
        } catch (error) {
          reject(error)
        }
      }

      try {
        video.src = videoUrl
        video.load()
      } catch {
        reject(new Error('Load failed'))
      }
    })
  }

  function processThumbQueue() {
    if (thumbsInFlight >= 2 || thumbQueue.length === 0) return
    const videoUrl = thumbQueue.shift()
    if (!videoUrl || generatedThumbs.value[videoUrl]) {
      processThumbQueue()
      return
    }

    thumbsInFlight++
    captureVideoFrame(videoUrl)
      .then((dataUrl) => {
        if (dataUrl) {
          generatedThumbs.value = { ...generatedThumbs.value, [videoUrl]: dataUrl }
        }
      })
      .catch(() => {})
      .finally(() => {
        thumbsInFlight--
        processThumbQueue()
      })
  }

  function ensureVideoThumb(videoUrl) {
    if (!videoUrl || generatedThumbs.value[videoUrl] || thumbQueue.includes(videoUrl)) return
    thumbQueue.push(videoUrl)
    processThumbQueue()
  }

  function buildRowSchedule(channel, rowIndex, startMs) {
    const items = channel?.items || []
    if (!items.length) return []

    const rowSchedule = []
    let cursor = new Date(startMs)
    let column = 0

    while (diffMinutes(new Date(startMs), cursor) < horizonMinutes) {
      const item = items[column % items.length]
      const durationSec = Math.max(300, Number(item?.duration_seconds) || 300)
      const end = new Date(cursor.getTime() + durationSec * 1000)

      rowSchedule.push({
        startUTC: cursor.getTime(),
        endUTC: end.getTime(),
        row: rowIndex,
        col: column,
        title: item?.title || 'Program',
        category: item?.category || channel?.name || 'Show',
        src: item?.playbackSrc || getVideoUrl(item),
        thumb: item?.thumbnail || '',
        durationSec,
        timeLabel: `${fmtTime(cursor)} – ${fmtTime(end)}`,
        item,
      })

      cursor = end
      column++
    }

    return rowSchedule
  }

  const schedulesByRow = computed(() =>
    channels.value.map((channel, rowIndex) => buildRowSchedule(channel, rowIndex, gridStart.value.getTime())),
  )

  const flattenedSchedule = computed(() => schedulesByRow.value.flat())

  function getCurrentSlot(rowFilter = null, atMs = nowMs.value) {
    const schedule = rowFilter == null ? flattenedSchedule.value : schedulesByRow.value[rowFilter] || []
    for (const slot of schedule) {
      if (atMs >= slot.startUTC && atMs < slot.endUTC) return slot
    }
    return null
  }

  function getNextSlot(rowFilter = null, atMs = nowMs.value) {
    const schedule = rowFilter == null ? flattenedSchedule.value : schedulesByRow.value[rowFilter] || []
    return schedule.find((slot) => slot.startUTC > atMs) || null
  }

  function getSeekTime(slot, atMs = Date.now()) {
    if (!slot) return 0
    const elapsed = Math.max(0, atMs - slot.startUTC)
    return Math.max(0, Math.min(Math.floor(elapsed / 1000), slot.durationSec - 1))
  }

  function getFirstPlayableChannelIndex() {
    return channels.value.findIndex((_, index) => !!getCurrentSlot(index)?.src)
  }

  const selectedCurrentSlot = computed(() => getCurrentSlot(selectedRow.value))
  const selectedNextSlot = computed(() => getNextSlot(selectedRow.value))

  const currentProgramDescription = computed(() => selectedCurrentSlot.value?.item?.description || '')

  const channelLabel = computed(() => {
    const index = selectedRow.value
    const channel = channels.value[index]
    const num = String(index + 1).padStart(2, '0')
    return `Channel ${num} — ${channel?.name || 'AHOY TV'}`
  })

  function channelNowTitle(index) {
    const slot = getCurrentSlot(index)
    if (slot) return cleanTitle(slot.title)
    const channel = channels.value[index]
    if (channel?.items?.length) return cleanTitle(channel.items[0].title)
    return 'Off Air'
  }

  function getChannelThumb(index) {
    const slot = getCurrentSlot(index)
    const channel = channels.value[index]
    if (slot) return slot.thumb || generatedThumbs.value[slot.src] || null
    if (channel?.items?.length) return getThumbnail(channel.items[0], channel.items[0].playbackSrc)
    return null
  }

  function getChannelBg(index) {
    const thumb = getChannelThumb(index)
    if (thumb && thumb !== DEFAULT_COVER) {
      return { backgroundImage: `url(${thumb})` }
    }

    const color = pillColors[index % pillColors.length]
    return {
      background: `linear-gradient(135deg, ${color}22 0%, #111 60%)`,
      opacity: 0.8,
    }
  }

  const currentChannelProgress = computed(() => {
    const slot = selectedCurrentSlot.value
    if (!slot) return 0
    return Math.max(0, Math.min(100, ((nowMs.value - slot.startUTC) / (slot.endUTC - slot.startUTC)) * 100))
  })

  const timeMarkers = computed(() => {
    const markers = []
    for (let minutes = 0; minutes <= horizonMinutes; minutes += 30) {
      const markerTime = new Date(gridStart.value.getTime() + minutes * 60000)
      markers.push(fmtTime(markerTime))
    }
    return markers
  })

  const nowLineStyle = computed(() => {
    const minutesElapsed = (nowMs.value - gridStart.value.getTime()) / 60000
    return { left: `${158 + minutesElapsed * pxPerMinute}px` }
  })

  const guidePrograms = computed(() => {
    void generatedThumbs.value
    const result = {}
    const start = gridStart.value

    channels.value.forEach((channel, rowIndex) => {
      const programs = []
      const items = channel.items || []
      if (!items.length) {
        result[rowIndex] = programs
        return
      }

      let cursor = new Date(start)
      let column = 0

      while (diffMinutes(start, cursor) < horizonMinutes) {
        const item = items[column % items.length]
        const durationSec = Math.max(300, Number(item?.duration_seconds) || 300)
        const durationMin = Math.max(5, Math.round(durationSec / 60))
        const itemEnd = new Date(cursor.getTime() + durationSec * 1000)

        programs.push({
          title: item?.title || 'Untitled',
          thumbnail: getThumbnail(item, item?.playbackSrc),
          category: item?.category || channel.name || 'Show',
          durMin: durationMin,
          widthPx: durationMin * pxPerMinute,
          timeLabel: `${fmtTime(cursor)} – ${fmtTime(itemEnd)}`,
          startUTC: cursor.getTime(),
          endUTC: itemEnd.getTime(),
          src: item?.playbackSrc,
          item,
        })

        cursor = itemEnd
        column++
      }

      result[rowIndex] = programs
    })

    return result
  })

  function clampSelectedRow() {
    if (!channels.value.length) {
      selectedRow.value = 0
      return
    }
    selectedRow.value = Math.max(0, Math.min(selectedRow.value, channels.value.length - 1))
  }

  function selectChannel(index) {
    if (!channels.value.length) return
    const nextIndex = Math.max(0, Math.min(index, channels.value.length - 1))
    selectedRow.value = nextIndex
    liveTvStore?.selectChannel(nextIndex)
  }

  function channelUp() {
    if (!channels.value.length) return
    selectChannel((selectedRow.value + 1) % channels.value.length)
  }

  function channelDown() {
    if (!channels.value.length) return
    selectChannel((selectedRow.value - 1 + channels.value.length) % channels.value.length)
  }

  async function loadChannels() {
    loadError.value = false
    let data = null

    try {
      data = await apiFetch(`/api/live-tv/channels?_=${Date.now()}`)
    } catch {
      try {
        data = await apiFetchCached('/api/live-tv/channels')
      } catch {
        loadError.value = true
        channels.value = []
        return false
      }
    }

    const rawChannels = data?.channels ?? data?.data?.channels ?? []
    channels.value = Array.isArray(rawChannels)
      ? rawChannels.map((channel, index) => normalizeChannel(channel, index))
      : []

    clampSelectedRow()
    liveTvStore?.setChannels(channels.value)
    liveTvStore?.selectChannel(selectedRow.value)

    nextTick(() => {
      channels.value.forEach((channel) => {
        channel.items.forEach((item) => {
          if (item.playbackSrc && !item.thumbnail) ensureVideoThumb(item.playbackSrc)
        })
      })
    })

    return true
  }

  function scheduleBoundaryRefresh() {
    if (boundaryTimer) clearTimeout(boundaryTimer)

    const upcomingTimes = [
      selectedCurrentSlot.value?.endUTC,
      selectedNextSlot.value?.startUTC,
    ].filter(Boolean)

    const nextBoundary = upcomingTimes.length ? Math.min(...upcomingTimes) : Date.now() + 60000
    const delay = Math.max(1000, Math.min(nextBoundary - Date.now() + 250, 30 * 60 * 1000))

    boundaryTimer = setTimeout(() => {
      nowMs.value = Date.now()
      scheduleBoundaryRefresh()
    }, delay)
  }

  watch(
    () => liveTvStore?.selectedChannelIdx,
    (index) => {
      if (typeof index === 'number' && index !== selectedRow.value) {
        selectedRow.value = index
      }
    },
  )

  watch([channels, selectedRow], () => {
    clampSelectedRow()
    nowMs.value = Date.now()
    scheduleBoundaryRefresh()
  }, { immediate: true })

  if (uiTimer) clearInterval(uiTimer)
  uiTimer = setInterval(() => {
    nowMs.value = Date.now()
  }, 15000)

  onUnmounted(() => {
    if (uiTimer) clearInterval(uiTimer)
    if (boundaryTimer) clearTimeout(boundaryTimer)
  })

  return {
    channels,
    selectedRow,
    loadError,
    rowLabels,
    gridStart,
    timeMarkers,
    nowLineStyle,
    guidePrograms,
    currentProgramDescription,
    channelLabel,
    currentChannelProgress,
    generatedThumbs,
    selectedCurrentSlot,
    selectedNextSlot,
    cleanTitle,
    getVideoUrl,
    getThumbnail,
    getCurrentSlot,
    getNextSlot,
    getSeekTime,
    getChannelBg,
    channelNowTitle,
    loadChannels,
    selectChannel,
    channelUp,
    channelDown,
    getFirstPlayableChannelIndex,
    syncNow: () => {
      nowMs.value = Date.now()
      scheduleBoundaryRefresh()
    },
  }
}
