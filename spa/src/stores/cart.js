import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])

  // Load from local storage on initialize
  try {
    const saved = localStorage.getItem('ahoy:boostCart')
    if (saved) {
      items.value = JSON.parse(saved)
    }
  } catch (e) {
    console.warn('Failed to load cart from local storage', e)
  }

  // Save to local storage on changes
  watch(items, (newItems) => {
    try {
      localStorage.setItem('ahoy:boostCart', JSON.stringify(newItems))
    } catch (e) {
      console.warn('Failed to save cart to local storage', e)
    }
  }, { deep: true })

  const cartTotal = computed(() => {
    return items.value.reduce((sum, item) => sum + (item.amount || 0), 0)
  })

  const itemCount = computed(() => items.value.length)

  function addBoost(artist_id, artist_name, artist_slug, amount = 0.05) {
    const existing = items.value.find(i => String(i.artist_id) === String(artist_id) || String(i.artist_slug) === String(artist_slug))
    if (existing) {
      existing.amount += amount
    } else {
      items.value.push({
        artist_id: String(artist_id || ''),
        artist_name: artist_name || '',
        artist_slug: artist_slug || '',
        amount: amount
      })
    }
  }

  function removeBoost(artist_id) {
    items.value = items.value.filter(i => String(i.artist_id) !== String(artist_id))
  }

  function updateAmount(artist_id, amount) {
    const existing = items.value.find(i => String(i.artist_id) === String(artist_id))
    if (existing) {
      existing.amount = amount
    }
  }

  function clearCart() {
    items.value = []
  }

  return {
    items,
    cartTotal,
    itemCount,
    addBoost,
    removeBoost,
    updateAmount,
    clearCart
  }
})
