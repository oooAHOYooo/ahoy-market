import { ref } from 'vue'

const STORAGE_KEY = 'ahoy_recent_searches'
const MAX_ITEMS = 5

export function useRecentSearches() {
  const searches = ref(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'))

  function add(query) {
    const q = (query || '').trim()
    if (!q) return
    const next = [q, ...searches.value.filter(s => s !== q)].slice(0, MAX_ITEMS)
    searches.value = next
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  }

  function remove(query) {
    searches.value = searches.value.filter(s => s !== query)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(searches.value))
  }

  return { searches, add, remove }
}
