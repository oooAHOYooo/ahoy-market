const SITE_NAME = 'Ahoy Indie Media'
const DEFAULT_DESCRIPTION = 'Stream music, videos, and podcasts from independent artists. Send tips directly to creators.'
const DEFAULT_IMAGE = '/static/img/ahoy_logo.png'
const DEFAULT_PUBLIC_ORIGIN = import.meta.env.VITE_PUBLIC_SITE_URL || 'https://app.ahoy.ooo'

function getPublicOrigin() {
  if (typeof window === 'undefined') return DEFAULT_PUBLIC_ORIGIN
  const origin = String(window.location?.origin || '').trim()
  if (origin && !/^(http:\/\/localhost|https?:\/\/localhost|capacitor:\/\/localhost|ionic:\/\/localhost)/i.test(origin)) {
    return origin
  }
  return DEFAULT_PUBLIC_ORIGIN
}

function absoluteUrl(pathOrUrl, fallbackPath = '/') {
  const value = String(pathOrUrl || '').trim() || fallbackPath
  if (/^https?:\/\//i.test(value)) return value
  return new URL(value, getPublicOrigin()).toString()
}

function pickImage(image) {
  const candidates = Array.isArray(image) ? image : [image]
  for (const candidate of candidates) {
    const value = String(candidate || '').trim()
    if (value) return value
  }
  return DEFAULT_IMAGE
}

function setMeta(selector, value) {
  if (typeof document === 'undefined') return
  const el = document.querySelector(selector)
  if (el) el.setAttribute('content', value)
}

function ensureCanonical(href) {
  if (typeof document === 'undefined') return
  let link = document.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  link.setAttribute('href', href)
}

export function setSeoMeta({
  title = SITE_NAME,
  description = DEFAULT_DESCRIPTION,
  image = DEFAULT_IMAGE,
  type = 'website',
  url = '',
} = {}) {
  if (typeof document === 'undefined') return

  const pageTitle = String(title || SITE_NAME).trim()
  const fullTitle = pageTitle.includes(SITE_NAME) ? pageTitle : `${pageTitle} — ${SITE_NAME}`
  const pageDescription = String(description || DEFAULT_DESCRIPTION).trim()
  const pageImage = absoluteUrl(pickImage(image), DEFAULT_IMAGE)
  const pageUrl = absoluteUrl(url || window.location?.pathname || '/', '/')

  document.title = fullTitle
  setMeta('meta[name="title"]', pageTitle)
  setMeta('meta[name="description"]', pageDescription)
  setMeta('meta[property="og:type"]', type)
  setMeta('meta[property="og:url"]', pageUrl)
  setMeta('meta[property="og:title"]', fullTitle)
  setMeta('meta[property="og:description"]', pageDescription)
  setMeta('meta[property="og:image"]', pageImage)
  setMeta('meta[property="og:site_name"]', SITE_NAME)
  setMeta('meta[property="og:image:width"]', '1200')
  setMeta('meta[property="og:image:height"]', '630')
  setMeta('meta[property="twitter:url"]', pageUrl)
  setMeta('meta[property="twitter:title"]', fullTitle)
  setMeta('meta[property="twitter:description"]', pageDescription)
  setMeta('meta[property="twitter:image"]', pageImage)
  setMeta('meta[property="twitter:card"]', 'summary_large_image')
  ensureCanonical(pageUrl)
}

export function routeSeoMeta(route) {
  setSeoMeta({
    title: route?.meta?.title || SITE_NAME,
    description: route?.meta?.description || DEFAULT_DESCRIPTION,
    url: route?.path || window.location?.pathname || '/',
  })
}

export function publicOrigin() {
  return getPublicOrigin()
}
