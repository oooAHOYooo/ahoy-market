import { ref, watch } from 'vue'

const STORAGE_KEY = 'ahoy.sidebarCollapsed'

let initial = false
try {
  initial = localStorage.getItem(STORAGE_KEY) === '1'
} catch { /* ignore */ }

const collapsed = ref(initial)

watch(collapsed, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  } catch { /* ignore */ }
})

function toggleSidebar() {
  collapsed.value = !collapsed.value
}

function setSidebarCollapsed(value) {
  collapsed.value = !!value
}

export function useSidebarCollapse() {
  return {
    collapsed,
    toggleSidebar,
    setSidebarCollapsed,
  }
}
