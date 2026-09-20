import { ref } from 'vue'

const deckMode = ref('nav')
const deckModes = ['nav', 'player', 'utility']

const setDeckMode = (mode) => {
  if (!deckModes.includes(mode)) return
  deckMode.value = mode
}

const toggleDeckMode = () => {
  const currentIndex = deckModes.indexOf(deckMode.value)
  deckMode.value = deckModes[(currentIndex + 1) % deckModes.length]
}

const resetDeckMode = () => {
  deckMode.value = 'nav'
}

export function useMobileCollapse() {
  return {
    deckMode,
    deckModes,
    setDeckMode,
    toggleDeckMode,
    resetDeckMode,
  }
}
