import { ref } from 'vue'

const STORAGE_KEY = 'ahoy:notifications'
const AUTO_DISMISS_MS = 24 * 60 * 60 * 1000

const notifications = ref([])
let nextId = 0

function saveToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(
      notifications.value.map(n => ({
        ...n,
        timestamp: n.timestamp instanceof Date ? n.timestamp.toISOString() : n.timestamp,
        autoDismissAt: n.autoDismissAt instanceof Date ? n.autoDismissAt.toISOString() : (n.autoDismissAt ?? null),
      }))
    ))
  } catch { /* quota / private mode */ }
}

function removeNotification(id) {
  notifications.value = notifications.value.filter(n => n.id !== id)
  saveToStorage()
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const items = JSON.parse(raw)
    const now = Date.now()
    for (const item of items) {
      const autoDismissAt = item.autoDismissAt ? new Date(item.autoDismissAt) : null
      if (autoDismissAt && autoDismissAt.getTime() <= now) continue
      notifications.value.push({
        ...item,
        timestamp: new Date(item.timestamp),
        autoDismissAt,
      })
      if (item.id >= nextId) nextId = item.id
      if (autoDismissAt) {
        const remaining = autoDismissAt.getTime() - now
        setTimeout(() => removeNotification(item.id), remaining)
      }
    }
    if (notifications.value.length) nextId++
  } catch { /* corrupted data — start fresh */ }
}

loadFromStorage()

export function useNotificationCenter() {
  function addNotification(message, type = 'info', autoDismissMs = null, link = null) {
    const id = ++nextId
    const timestamp = new Date()
    const autoDismissAt = autoDismissMs === false
      ? null
      : new Date(Date.now() + (autoDismissMs || AUTO_DISMISS_MS))

    notifications.value.unshift({ id, message, type, timestamp, read: false, link, autoDismissAt })

    if (autoDismissMs !== false) {
      setTimeout(() => removeNotification(id), autoDismissMs || AUTO_DISMISS_MS)
    }

    saveToStorage()
    return id
  }

  function clearAll() {
    notifications.value = []
    saveToStorage()
  }

  function markAllRead() {
    notifications.value.forEach(n => { n.read = true })
    saveToStorage()
  }

  return { notifications, addNotification, removeNotification, clearAll, markAllRead }
}
