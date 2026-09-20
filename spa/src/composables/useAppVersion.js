import { ref } from 'vue'

const BUNDLED_VERSION = import.meta.env.VITE_APP_VERSION || '1.1.0'
const POLL_INTERVAL_MS = 30 * 60 * 1000

function isNewer(remote, local) {
  const parse = v => v.split('.').map(Number)
  const [rMaj, rMin, rPat] = parse(remote)
  const [lMaj, lMin, lPat] = parse(local)
  if (rMaj !== lMaj) return rMaj > lMaj
  if (rMin !== lMin) return rMin > lMin
  return rPat > lPat
}

export function useAppVersion() {
  const updateAvailable = ref(false)
  const serverVersion = ref(null)
  let pollTimer = null

  async function checkVersion() {
    if (!navigator.onLine) return
    try {
      const res = await fetch('/healthz')
      const data = await res.json()
      serverVersion.value = data.version
      const dismissed = localStorage.getItem(`ahoy:dismissed-update:${data.version}`)
      if (!dismissed && isNewer(data.version, BUNDLED_VERSION)) {
        updateAvailable.value = true
      }
    } catch {
      // Silent failure on network errors
    }
  }

  function dismissUpdate() {
    localStorage.setItem(`ahoy:dismissed-update:${serverVersion.value}`, '1')
    updateAvailable.value = false
  }

  function startPolling() {
    checkVersion()
    pollTimer = setInterval(checkVersion, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    clearInterval(pollTimer)
  }

  return { updateAvailable, serverVersion, dismissUpdate, startPolling, stopPolling }
}
