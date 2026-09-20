import { musicUrl, videoUrl } from '../utils/urls'
import { apiFetchCached } from './useApi'

let catalogCache = null
let catalogCachePromise = null

const TYPE_LABELS = {
  track: 'Track',
  album: 'Album',
  video: 'Video',
  show: 'Video',
  podcast: 'Podcast',
  podcastEpisode: 'Podcast Episode',
  artist: 'Artist',
  event: 'Event'
}

const TYPE_BADGE_LABELS = {
  podcastEpisode: 'Episode'
}

const TYPE_ORDER = {
  artist: 0,
  track: 1,
  album: 2,
  video: 3,
  show: 3,
  podcastEpisode: 4,
  podcast: 5,
  event: 6
}

export function toSearchList(collection) {
  if (Array.isArray(collection)) return collection
  if (!collection || typeof collection !== 'object') return []
  return Object.entries(collection).map(([key, value]) => ({
    ...value,
    id: value.id || key,
    slug: value.slug || key
  }))
}

function createAlbumSearchItems(tracks) {
  const albumMap = new Map()
  for (const track of tracks) {
    if (track.album && track.album !== 'Single' && !albumMap.has(track.album)) {
      albumMap.set(track.album, {
        id: track.album,
        title: track.album,
        name: track.album,
        artist: track.artist,
        cover_art: track.cover_art || track.artwork,
        type: 'album'
      })
    }
  }
  return Array.from(albumMap.values())
}

export function buildPodcastSearchItems(shows, episodes = []) {
  const items = []
  const podcastShows = toSearchList(shows)
  const showBySlug = new Map(podcastShows.map(show => [show.slug || show.id, show]))

  for (const show of podcastShows) {
    items.push({ ...show, type: 'podcast' })
    for (const episode of show.episodes || []) {
      items.push({
        ...episode,
        id: episode.id || `${show.slug || show.id}-${episode.title}`,
        showSlug: show.slug || show.id,
        showTitle: show.title,
        host: show.host,
        artwork: episode.artwork || episode.thumbnail || show.artwork || show.image,
        type: 'podcastEpisode'
      })
    }
  }

  for (const episode of toSearchList(episodes)) {
    const showSlug = episode.showSlug || episode.show_slug || episode.show_id
    const show = showBySlug.get(showSlug) || {}
    items.push({
      ...episode,
      showSlug,
      showTitle: episode.showTitle || episode.show_title || show.title,
      host: episode.host || show.host,
      artwork: episode.artwork || episode.thumbnail || show.artwork || show.image,
      type: 'podcastEpisode'
    })
  }

  return items
}

export function normalizeSearchCatalog({ music = {}, artists = {}, shows = {}, podcasts = {}, events = {} } = {}) {
  const tracks = toSearchList(music.tracks).map(item => ({ ...item, type: 'track' }))
  return {
    tracks,
    albums: createAlbumSearchItems(tracks),
    shows: toSearchList(shows.shows).map(item => ({ ...item, type: 'video' })),
    podcasts: buildPodcastSearchItems(podcasts.shows, podcasts.podcasts),
    artists: toSearchList(artists.artists).map(item => ({ ...item, type: 'artist' })),
    events: toSearchList(events.events).map(item => ({ ...item, type: 'event' }))
  }
}

export async function loadSearchCatalog({ force = false } = {}) {
  if (catalogCache && !force) return catalogCache
  if (catalogCachePromise && !force) return catalogCachePromise

  catalogCachePromise = Promise.all([
    apiFetchCached('/api/music').catch(() => ({ tracks: [], albums: [] })),
    apiFetchCached('/api/shows').catch(() => ({ shows: [] })),
    apiFetchCached('/api/podcasts').catch(() => ({ shows: [] })),
    apiFetchCached('/api/artists').catch(() => ({ artists: [] })),
    apiFetchCached('/api/events').catch(() => ({ events: [] }))
  ]).then(([music, shows, podcasts, artists, events]) => {
    catalogCache = normalizeSearchCatalog({ music, shows, podcasts, artists, events })
    return catalogCache
  }).finally(() => {
    catalogCachePromise = null
  })

  return catalogCachePromise
}

function searchableText(...values) {
  return values
    .flatMap(value => Array.isArray(value) ? value : [value])
    .filter(value => value !== undefined && value !== null)
    .join(' ')
    .toLowerCase()
}

function hasWordStart(text, q) {
  return text.split(/[^a-z0-9]+/).some(part => part.startsWith(q))
}

function scoreItem(item, query) {
  const q = (query || '').trim().toLowerCase()
  if (!q) return 0

  const primary = searchableText(item.title, item.name)
  const secondary = searchableText(item.artist, item.host, item.album, item.slug, item.showTitle, item.venue, item.filmmaker)
  const descriptive = searchableText(item.description, item.bio, item.type, item.genre, item.genres, item.tags, item.series)

  let score = 0
  if (primary === q) score = 120
  else if (primary.startsWith(q)) score = 100
  else if (hasWordStart(primary, q)) score = 90
  else if (primary.includes(q)) score = 75
  else if (secondary.includes(q)) score = 55
  else if (descriptive.includes(q)) score = 30

  if (!score) return 0
  return score - (TYPE_ORDER[item.type] || 20)
}

function sortByRelevance(items, query) {
  return items
    .map((item, index) => ({ item, index, score: scoreItem(item, query) }))
    .filter(match => match.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map(match => match.item)
}

export function flattenSearchCatalog(catalog) {
  return [
    ...(catalog.tracks || []),
    ...(catalog.albums || []),
    ...(catalog.shows || []),
    ...(catalog.podcasts || []),
    ...(catalog.artists || []),
    ...(catalog.events || [])
  ]
}

export function runFlatSearch(catalog, query, limit = 50) {
  const q = (query || '').trim()
  if (!q) return []
  return sortByRelevance(flattenSearchCatalog(catalog), q).slice(0, limit)
}

function normalizeTypedItems(items, fallbackType) {
  return toSearchList(items).map(item => ({ ...item, type: item.type || fallbackType }))
}

function normalizePodcastItems(podcasts) {
  const items = toSearchList(podcasts)
  if (items.some(item => item.type)) return items
  return buildPodcastSearchItems(items)
}

export function getSearchResultLabel(result) {
  return TYPE_LABELS[result?.type] || 'Result'
}

export function getSearchResultBadgeLabel(result) {
  return TYPE_BADGE_LABELS[result?.type] || getSearchResultLabel(result)
}

export function getSearchResultSubtitle(result) {
  return result?.artist || result?.host || result?.showTitle || result?.venue || result?.description || ''
}

export function highlightSearchText(value, query) {
  const text = `${value || ''}`
  const q = `${query || ''}`.trim()
  if (!text || !q) return escapeHtml(text)

  const escapedQuery = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = new RegExp(`(${escapedQuery})`, 'ig')
  return escapeHtml(text).replace(pattern, '<mark class="search-highlight">$1</mark>')
}

function escapeHtml(value) {
  return `${value || ''}`
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function getSearchResultUrl(result) {
  switch (result?.type) {
    case 'track':
      return musicUrl(result)
    case 'album':
      return `/music?q=${encodeURIComponent(result.title)}`
    case 'video':
    case 'show':
      return videoUrl(result)
    case 'podcast':
      return `/podcasts/${result.slug || result.id}`
    case 'podcastEpisode':
      return `/podcasts/${result.showSlug}?play=${encodeURIComponent(result.id)}`
    case 'artist':
      return `/artists/${result.slug || result.id}`
    case 'event':
      if (result.series && result.number) return `/events/${result.series}/${result.number}`
      return `/events/v/${encodeURIComponent(result.id)}`
    default:
      return '#'
  }
}

export function useSearch() {
  function runSearch(tracks, artists, shows, podcasts, events, query) {
    return {
      tracks: sortByRelevance(normalizeTypedItems(tracks, 'track'), query).slice(0, 20),
      artists: sortByRelevance(normalizeTypedItems(artists, 'artist'), query).slice(0, 15),
      shows: sortByRelevance(normalizeTypedItems(shows, 'video'), query).slice(0, 15),
      podcasts: sortByRelevance(normalizePodcastItems(podcasts), query).slice(0, 15),
      events: sortByRelevance(normalizeTypedItems(events || [], 'event'), query).slice(0, 10)
    }
  }

  return { runSearch }
}
