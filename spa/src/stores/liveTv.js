import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLiveTvStore = defineStore('liveTv', () => {
  const channels = ref([])
  const selectedChannelIdx = ref(0)

  function setChannels(chs) {
    channels.value = chs
  }

  function selectChannel(idx) {
    selectedChannelIdx.value = idx
  }

  return { channels, selectedChannelIdx, setChannels, selectChannel }
})
