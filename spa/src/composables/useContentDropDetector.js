const firedThisSession = new Set()

const SECTION_MAP = {
  videos: { type: 'video', message: 'New videos just dropped' },
  podcasts: { type: 'podcast', message: 'New podcast episodes available' },
  artists: { type: 'artist', message: 'New artists added' },
  music: { type: 'music', message: 'New music added' },
  events: { type: 'events', message: 'New events posted' },
}

export function useContentDropDetector() {
  async function checkForNewContent() {
    try {
      const lastCheck = localStorage.getItem('ahoy:last-whats-new-check')
      const lastCheckDate = lastCheck ? new Date(lastCheck) : null

      const res = await fetch('/api/whats-new', { cache: 'no-store' })
      const data = await res.json()
      localStorage.setItem('ahoy:last-whats-new-check', new Date().toISOString())

      if (!lastCheckDate) return

      const structured = data.structured || {}
      const now = new Date()
      const year = String(now.getFullYear())
      const monthKey = now.toLocaleString('en-US', { month: 'short' }).toLowerCase()
      const monthData = structured[year]?.[monthKey]
      if (!monthData) return

      for (const [sectionKey, sectionData] of Object.entries(monthData)) {
        if (firedThisSession.has(sectionKey)) continue
        const config = SECTION_MAP[sectionKey]
        if (!config) continue

        const items = sectionData?.items || []
        const newItems = items.filter(item => item.date && new Date(item.date) > lastCheckDate)
        if (!newItems.length) continue

        firedThisSession.add(sectionKey)
        const newest = newItems.sort((a, b) => new Date(b.date) - new Date(a.date))[0]
        const link = newest?.detail_path || newest?.month_path || `/whats-new/${year}/${monthKey}`

        window.dispatchEvent(new CustomEvent('ahoy:toast', {
          detail: { message: config.message, type: config.type, duration: 5000, link },
        }))
      }
    } catch {
      // Silent failure on network errors
    }
  }

  return { checkForNewContent }
}
