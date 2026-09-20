import { ref } from 'vue'

const THEME_KEY = 'ahoyTheme'
const THEME_EXPLICIT_KEY = 'ahoyThemeExplicit'
const currentTheme = ref('ayu-night')

const THEME_COLORS = {
    default: '#00a2ff',
    'ayu-night': '#ff0060'
}

const THEME_BODY_CLASSES = [
    'theme-after-dark',
    'theme-deep-blue',
    'theme-bug-bug-bug',
    'theme-ayu-dark',
    'theme-ayu-night'
]

function normalizeTheme(theme) {
    return theme === 'default' ? 'default' : 'ayu-night'
}

function updateMetaThemeColor(theme) {
    const color = THEME_COLORS[theme] || THEME_COLORS['default']
    let meta = document.querySelector('meta[name="theme-color"]')
    if (!meta) {
        meta = document.createElement('meta')
        meta.name = 'theme-color'
        document.head.appendChild(meta)
    }
    meta.setAttribute('content', color)
}

export function useTheme() {
    function initTheme() {
        const explicitTheme = localStorage.getItem(THEME_EXPLICIT_KEY) === '1'
        const saved = normalizeTheme(explicitTheme ? localStorage.getItem(THEME_KEY) : 'ayu-night')
        setTheme(saved, { explicit: explicitTheme })
    }

    function setTheme(theme, options = {}) {
        const safeTheme = normalizeTheme(theme)

        if (options.explicit === true) {
            localStorage.setItem(THEME_EXPLICIT_KEY, '1')
        } else if (options.explicit === false) {
            localStorage.setItem(THEME_EXPLICIT_KEY, '0')
        }

        currentTheme.value = safeTheme
        localStorage.setItem(THEME_KEY, safeTheme)

        document.body.classList.remove(...THEME_BODY_CLASSES)
        if (safeTheme === 'ayu-night') {
            document.body.classList.add('theme-ayu-night')
        }

        updateMetaThemeColor(safeTheme)
    }

    return {
        currentTheme,
        initTheme,
        setTheme
    }
}
