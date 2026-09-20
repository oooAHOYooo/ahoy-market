import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loadSearchCatalog } from '../composables/useSearch'

export const useCatalogStore = defineStore('catalog', () => {
  const catalog = ref({ tracks: [], artists: [], shows: [], podcasts: [], events: [] })
  const loading = ref(false)
  const ready = ref(false)
  let _promise = null

  async function ensureLoaded(force = false) {
    if (ready.value && !force) return catalog.value
    if (_promise && !force) return _promise

    loading.value = true
    _promise = loadSearchCatalog({ force })
      .then(data => {
        catalog.value = data
        ready.value = true
        return data
      })
      .finally(() => {
        loading.value = false
        _promise = null
      })

    return _promise
  }

  return { catalog, loading, ready, ensureLoaded }
})
