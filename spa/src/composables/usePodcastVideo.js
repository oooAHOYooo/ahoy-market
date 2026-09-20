const PODCAST_VIDEO_PAGE_MAP = {
  'poets-and-friends': {
    3: 'poets-and-friends-3',
    4: 'poets-and-friends-4',
    8: 'poets-and-friends-8',
    9: 'poets-and-friends-9',
    10: 'poets-and-friends-10',
  },
  'tyler-needs-a-break': {
    4: 'tyler-needs-a-break-ep4-full',
  },
}

function parseEpisodeNumber(value) {
  const match = String(value || '').match(/#\s*(\d+)/)
  return match ? Number(match[1]) : null
}

function getEpisodeNumber(episode) {
  if (!episode) return null
  const directNumber = Number(episode.episode_number)
  if (Number.isFinite(directNumber) && directNumber > 0) return directNumber

  const parsed = parseEpisodeNumber(episode.title)
  if (Number.isFinite(parsed) && parsed > 0) return parsed

  return null
}

export function getPodcastVideoRoute(showSlug, episode) {
  const slug = String(showSlug || '')
  const map = PODCAST_VIDEO_PAGE_MAP[slug] || {}
  const episodeNumber = getEpisodeNumber(episode)
  const videoPageId = episodeNumber ? map[episodeNumber] : null

  if (videoPageId) {
    return `/videos/${videoPageId}`
  }

  const directVideoUrl = String(episode?.video_url || episode?.url || '').trim()
  return directVideoUrl
}

export function hasPodcastVideo(showSlug, episode) {
  return Boolean(getPodcastVideoRoute(showSlug, episode))
}
