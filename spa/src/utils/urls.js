/**
 * URL builders for hierarchical slugs
 * - Music: /music/:artistSlug/:trackSlug
 * - Video: /videos/:videoSlug
 * Includes fallback to old URL format if slug data is missing
 */

function normalizeKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function isMusicVideo(show) {
  const category = normalizeKey(show?.category)
  const tags = Array.isArray(show?.tags) ? show.tags.map(normalizeKey) : []
  const title = normalizeKey(show?.title)

  return (
    category === 'music video' ||
    category === 'music-video' ||
    tags.includes('music-video') ||
    tags.includes('musicvideos') ||
    title.includes('music video')
  )
}

export function videoDetailSlug(show) {
  if (!show) return ''

  const explicitSlug = normalizeKey(show.slug || show.show_slug || show.video_slug)
  if (explicitSlug) return explicitSlug

  const hostSlug = normalizeKey(show.host_slug || show.host || '')
  const titleSlug = normalizeKey(show.title || '')
  const idSlug = normalizeKey(show.id || show.show_id || '')

  let slug = ''
  if (hostSlug && titleSlug) slug = `${hostSlug}-${titleSlug}`
  else slug = titleSlug || hostSlug || idSlug

  if (!slug) return ''
  if (isMusicVideo(show) && !slug.endsWith('-mv')) slug = `${slug}-mv`
  return slug
}

export function musicUrl(track) {
  if (!track) return '/music'
  const artistSlug = track.artist_slug
  const trackSlug = track.track_slug
  if (artistSlug && trackSlug) {
    return `/music/${artistSlug}/${trackSlug}`
  }
  return `/music/${track.id}`
}

export function videoUrl(show) {
  if (!show) return '/videos'
  const slug = videoDetailSlug(show)
  if (slug) return `/videos/${slug}`
  if (show.host_slug && show.id) return `/videos/${show.host_slug}/${show.id}`
  return `/videos/${show.id || show.show_id || ''}`
}

export function directVideoHref(show) {
  if (!show) return ''
  return show.video_url || show.url || show.mp4_link || ''
}
