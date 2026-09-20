import posthog from 'posthog-js'
import { apiUrl } from './useApi'

const runtimeConfig = typeof window !== 'undefined' ? (window.__AHOY_POSTHOG__ || {}) : {}
const POSTHOG_KEY = (import.meta.env.VITE_POSTHOG_KEY || runtimeConfig.key || '').trim()
const POSTHOG_HOST = (import.meta.env.VITE_POSTHOG_HOST || runtimeConfig.host || '').trim()
const POSTHOG_DEBUG = String(import.meta.env.VITE_POSTHOG_DEBUG || runtimeConfig.debug || '').toLowerCase() === 'true'

let initialized = false
let enabled = false
let lastPageviewPath = ''
const DB_ANALYTICS_ENDPOINT = apiUrl('/api/admin/analytics/event')

function toPath(routeLike) {
  if (!routeLike) return '/'
  const fullPath = routeLike.fullPath || routeLike.path || '/'
  return String(fullPath || '/')
}

function toTitle(routeLike) {
  const title = routeLike?.meta?.title || document.title || 'Ahoy Indie Media'
  return String(title).replace(/\s+/g, ' ').trim()
}

function distinctIdForUser(user) {
  return String(user?.id || user?.user_id || user?.username || user?.email || '').trim()
}

async function sendDbEvent(type, props = {}) {
  try {
    await fetch(DB_ANALYTICS_ENDPOINT, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        type,
        path: props.path || (typeof window !== 'undefined' ? window.location.pathname : '/'),
        metadata: props,
      }),
    })
  } catch {
    // ignore analytics failures
  }
}

export function initAnalytics(router) {
  if (initialized) return { enabled, trackEvent, identifyUser, resetIdentity }
  initialized = true

  if (!POSTHOG_KEY) return { enabled: false, trackEvent, identifyUser, resetIdentity }

  try {
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST || undefined,
      autocapture: true,
      capture_pageview: false,
      capture_pageleave: true,
      persistence: 'localStorage',
      loaded: (client) => {
        enabled = !!client
        if (POSTHOG_DEBUG && client?.debug) client.debug()
      },
    })
  } catch (err) {
    console.warn('[analytics] PostHog failed to initialize', err)
    return { enabled: false, trackEvent, identifyUser, resetIdentity }
  }

  enabled = true

  const sendPageview = (routeLike) => {
    const path = toPath(routeLike)
    if (!path || path === lastPageviewPath) return
    lastPageviewPath = path
    const title = toTitle(routeLike)
    void sendDbEvent('page_view', {
      path,
      title,
      source: 'spa',
      current_url: typeof window !== 'undefined' ? window.location.href : path,
    })
    if (enabled) {
      posthog.capture('$pageview', {
        $current_url: typeof window !== 'undefined' ? window.location.href : path,
        path,
        title,
      })
    }
  }

  if (router?.afterEach) {
    router.afterEach((to) => {
      sendPageview(to)
    })
  }

  if (router?.currentRoute?.value) {
    sendPageview(router.currentRoute.value)
  }

  return { enabled, trackEvent, identifyUser, resetIdentity }
}

export function trackEvent(name, props = {}) {
  if (!name) return
  void sendDbEvent(name, props)
  if (!enabled) return
  try {
    posthog.capture(name, props)
  } catch {
    // ignore analytics failures
  }
}

export function identifyUser(user) {
  if (!enabled) return

  const distinctId = distinctIdForUser(user)
  if (!distinctId) return

  try {
    posthog.identify(distinctId, {
      email: user?.email || undefined,
      username: user?.username || undefined,
      display_name: user?.display_name || undefined,
    })
  } catch {
    // ignore analytics failures
  }
}

export function resetIdentity() {
  if (!enabled) return
  try {
    posthog.reset()
  } catch {
    // ignore analytics failures
  }
}
