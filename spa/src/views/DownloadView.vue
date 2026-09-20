<template>
  <div class="download-app-page">
    <!-- Hero -->
    <section class="download-hero download-hero-glass">
      <div class="download-hero-glow"></div>
      <div class="download-hero-inner">
        <div class="download-hero-icon">
          <i class="fas fa-download" aria-hidden="true"></i>
        </div>
        <h1>Get Ahoy</h1>
        <p>Use Ahoy Indie Media on your favorite device.</p>
        <p class="download-version-badge">Latest: v{{ LATEST_VERSION }} — {{ LATEST_DATE }}</p>
      </div>
    </section>

    <!-- Platform cards -->
    <div class="download-content-glass">
      <div class="download-platform-grid">

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon web">
            <i class="fas fa-globe"></i>
          </div>
          <h3>Web</h3>
          <p>Use Ahoy in any modern browser. No install required.</p>
          <a href="/" class="download-platform-cta neu-btn neu-btn-primary" @click.prevent="$router.push('/')">
            Open in browser
          </a>
        </div>

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon linux">
            <i class="fab fa-linux"></i>
          </div>
          <h3>Linux</h3>
          <p>Arch, Garuda, Ubuntu, Raspberry Pi, and more.</p>
          <div class="download-install-block">
            <code class="download-install-cmd">yay ahoy</code>
            <span class="download-install-or">or</span>
            <code class="download-install-cmd small">curl -sL get.ahoy.ooo/install | bash</code>
          </div>
          <div class="download-btn-row">
            <a :href="ghRelease('x86_64.AppImage')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-primary">
              <i class="fas fa-download"></i> AppImage x64
            </a>
            <a :href="ghRelease('arm64.AppImage')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-secondary">
              <i class="fas fa-download"></i> ARM64
            </a>
          </div>
        </div>

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon windows">
            <i class="fab fa-windows"></i>
          </div>
          <h3>Windows</h3>
          <p>Native installer for Windows 10 and 11.</p>
          <div class="download-install-block">
            <code class="download-install-cmd">winget install ahoy</code>
          </div>
          <div class="download-btn-row">
            <a :href="ghRelease('x64-setup.exe')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-primary">
              <i class="fas fa-download"></i> .exe x64
            </a>
            <a :href="ghRelease('arm64-setup.exe')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-secondary">
              <i class="fas fa-download"></i> ARM64
            </a>
          </div>
        </div>

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon mac">
            <i class="fab fa-apple"></i>
          </div>
          <h3>macOS</h3>
          <p>Native app for Mac. Intel and Apple Silicon.</p>
          <div class="download-install-block">
            <code class="download-install-cmd small">brew install oooAHOYooo/tap/ahoy</code>
          </div>
          <div class="download-btn-row">
            <a :href="ghRelease('arm64.dmg')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-primary">
              <i class="fas fa-download"></i> DMG (Apple Silicon)
            </a>
            <a :href="ghRelease('x64.dmg')" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-secondary">
              <i class="fas fa-download"></i> Intel
            </a>
          </div>
        </div>

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon android">
            <i class="fab fa-android"></i>
          </div>
          <h3>Android</h3>
          <p>Native app for phones and tablets.</p>
          <a href="https://play.google.com/store/apps?q=ahoy" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-primary">
            Download on Google Play
          </a>
        </div>

        <div class="download-platform-card glass-card">
          <div class="download-platform-icon ios">
            <i class="fab fa-apple"></i>
          </div>
          <h3>iOS</h3>
          <p>Native app for iPhone and iPad. Early access via TestFlight.</p>
          <a href="https://testflight.apple.com/join/mQnXrRax" target="_blank" rel="noopener noreferrer" class="download-platform-cta neu-btn neu-btn-primary">
            Join TestFlight
          </a>
        </div>

      </div>

      <p class="download-footer-note">
        Desktop and mobile apps load from the cloud. Your account and progress sync everywhere.
        <a href="https://github.com/oooAHOYooo/ahoy-little-platform/releases" target="_blank" rel="noopener noreferrer">All releases on GitHub →</a>
      </p>
    </div>

    <!-- Release history table -->
    <div class="release-history-glass">
      <h2 class="release-history-title">Release History</h2>
      <div class="release-table-wrap">
        <table class="release-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Date</th>
              <th>Linux</th>
              <th>Windows</th>
              <th>macOS</th>
              <th>Android</th>
              <th>iOS</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in releases" :key="r.version" :class="{ 'release-latest': r.latest }">
              <td>
                <a :href="`https://github.com/oooAHOYooo/ahoy-little-platform/releases/tag/v${r.version}`" target="_blank" rel="noopener noreferrer" class="release-version-link">
                  v{{ r.version }}
                </a>
                <span v-if="r.latest" class="release-tag-latest">latest</span>
              </td>
              <td class="release-date">{{ r.date }}</td>
              <td><span :class="badgeClass(r.linux)">{{ r.linux }}</span></td>
              <td><span :class="badgeClass(r.windows)">{{ r.windows }}</span></td>
              <td><span :class="badgeClass(r.mac)">{{ r.mac }}</span></td>
              <td><span :class="badgeClass(r.android)">{{ r.android }}</span></td>
              <td><span :class="badgeClass(r.ios)">{{ r.ios }}</span></td>
              <td class="release-notes">{{ r.notes }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const LATEST_VERSION = ref('0.2.3')
const LATEST_DATE = ref('March 11, 2026')
const releases = ref([])
const loading = ref(true)
const error = ref(null)

// Fetch latest release from GitHub API
async function fetchLatestRelease() {
  try {
    const res = await fetch('https://api.github.com/repos/oooAHOYooo/ahoy-little-platform/releases/latest')
    if (!res.ok) throw new Error('Failed to fetch release')
    const data = await res.json()

    const version = data.tag_name.replace(/^v/, '')
    const date = new Date(data.published_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })

    LATEST_VERSION.value = version
    LATEST_DATE.value = date
  } catch (e) {
    console.warn('Could not fetch latest release from GitHub:', e.message)
    // Falls back to hardcoded values above
  }
}

// Fetch all releases and build history table
async function fetchReleaseHistory() {
  try {
    const res = await fetch('https://api.github.com/repos/oooAHOYooo/ahoy-little-platform/releases?per_page=20')
    if (!res.ok) throw new Error('Failed to fetch releases')
    const data = await res.json()

    releases.value = data.map((r, idx) => {
      const version = r.tag_name.replace(/^v/, '')
      const date = new Date(r.published_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })

      // Detect which platforms are in release assets
      const assets = r.assets.map(a => a.name)
      const linux = assets.some(a => a.includes('AppImage') || a.includes('.deb')) ? 'AppImage + AUR' : '—'
      const windows = assets.some(a => a.includes('setup.exe')) ? 'NSIS installer' : '—'
      const mac = assets.some(a => a.includes('.dmg')) ? 'DMG' : '—'

      return {
        version,
        date,
        latest: idx === 0,
        linux,
        windows,
        mac,
        android: '—',
        ios: '—',
        notes: r.body ? r.body.split('\n')[0].substring(0, 50) : 'Release'
      }
    })
  } catch (e) {
    console.warn('Could not fetch release history:', e.message)
    // Use fallback hardcoded releases
    releases.value = [
      {
        version: '0.2.3',
        date: '2026-03-11',
        latest: true,
        linux: 'AppImage + AUR',
        windows: 'NSIS installer',
        mac: 'DMG',
        android: 'pending',
        ios: 'pending',
        notes: 'Downloads page + release history, alembic fixes',
      },
      {
        version: '0.2.2',
        date: '2026-03-09',
        latest: false,
        linux: 'AppImage + AUR',
        windows: 'NSIS installer',
        mac: 'DMG',
        android: '—',
        ios: '—',
        notes: 'Windows build + AUR live, Snap Store registered',
      },
    ]
  }
}

function ghRelease(suffix) {
  return `https://github.com/oooAHOYooo/ahoy-little-platform/releases/download/v${LATEST_VERSION.value}/ahoy-indie-media-${LATEST_VERSION.value}-${suffix}`
}

function badgeClass(val) {
  if (!val || val === '—') return 'rb rb-none'
  if (val === 'pending') return 'rb rb-pending'
  return 'rb rb-yes'
}

// Load data on mount
onMounted(async () => {
  await Promise.all([
    fetchLatestRelease(),
    fetchReleaseHistory()
  ])
  loading.value = false
})
</script>

<style scoped>
.download-app-page {
  min-height: 100vh;
  background: var(--background-dark, #0c0c0e);
  color: var(--text-primary, #e5e7eb);
  padding: var(--gutter, 20px);
  padding-bottom: 4rem;
}

/* ===== Hero ===== */
.download-hero-glass {
  position: relative;
  background: linear-gradient(135deg, rgba(15,15,25,0.95) 0%, rgba(20,20,35,0.9) 50%, rgba(25,25,45,0.85) 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 24px;
  margin-bottom: var(--section-gap, 22px);
  overflow: hidden;
  backdrop-filter: saturate(140%) blur(20px);
  -webkit-backdrop-filter: saturate(140%) blur(20px);
  box-shadow: 0 20px 50px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1), inset 0 -1px 0 rgba(0,0,0,0.3);
}
.download-hero-glow {
  position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
  background: radial-gradient(circle at 30% 30%, rgba(99,102,241,0.08) 0%, transparent 50%),
              radial-gradient(circle at 70% 70%, rgba(139,92,246,0.06) 0%, transparent 50%);
  pointer-events: none;
}
.download-hero-inner {
  position: relative; z-index: 2;
  padding: var(--spacing-xl, 2rem); text-align: center;
}
.download-hero-icon {
  width: 64px; height: 64px; margin: 0 auto 1rem;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(139,92,246,0.2) 100%);
  border: 1px solid rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem; color: rgba(139,92,246,0.95);
  box-shadow: 0 8px 24px rgba(99,102,241,0.15);
}
.download-hero-inner h1 { margin: 0 0 0.25rem; font-size: 1.75rem; font-weight: 700; color: #fff; }
.download-hero-inner p { margin: 0; font-size: 0.95rem; color: rgba(255,255,255,0.6); }
.download-version-badge {
  display: inline-block; margin-top: 0.6rem;
  font-size: 0.8rem; color: rgba(139,92,246,0.85);
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2);
  padding: 3px 10px; border-radius: 20px;
}

/* ===== Platform cards ===== */
.download-content-glass {
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px;
  padding: var(--spacing-xl, 1.5rem);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
  margin-bottom: var(--section-gap, 22px);
}
.download-platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem; margin-bottom: 1.5rem;
}
.download-platform-card {
  background: rgba(19,19,22,0.8);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 18px; padding: 1.5rem; text-align: center;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
  box-shadow: inset 4px 4px 10px rgba(0,0,0,0.3), inset -2px -2px 6px rgba(255,255,255,0.02);
}
.download-platform-card:hover {
  background: rgba(22,22,26,0.9);
  border-color: rgba(255,255,255,0.1);
  box-shadow: inset 3px 3px 8px rgba(0,0,0,0.4), inset -2px -2px 6px rgba(255,255,255,0.03), 0 0 20px rgba(99,102,241,0.06);
}
.download-platform-icon {
  width: 52px; height: 52px; margin: 0 auto 1rem;
  border-radius: 14px; display: flex; align-items: center;
  justify-content: center; font-size: 1.5rem; flex-shrink: 0;
}
.download-platform-icon.web    { background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(99,102,241,0.2));   color: rgba(96,165,250,0.95); }
.download-platform-icon.android{ background: linear-gradient(135deg, rgba(52,168,83,0.25), rgba(139,92,246,0.15));  color: rgba(134,239,172,0.95); }
.download-platform-icon.ios    { background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06)); color: rgba(255,255,255,0.9); }
.download-platform-icon.linux  { background: linear-gradient(135deg, rgba(250,204,21,0.2), rgba(234,179,8,0.12));   color: rgba(250,204,21,0.9); }
.download-platform-icon.windows{ background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.15));  color: rgba(96,165,250,0.9); }
.download-platform-icon.mac    { background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06)); color: rgba(255,255,255,0.9); }

.download-platform-card h3 { margin: 0 0 0.5rem; font-size: 1.1rem; font-weight: 600; color: rgba(255,255,255,0.9); }
.download-platform-card p  { margin: 0 0 1rem; font-size: 0.85rem; color: rgba(255,255,255,0.5); line-height: 1.5; }

.download-install-block {
  background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px; padding: 0.6rem 0.75rem; margin-bottom: 1rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
}
.download-install-cmd {
  font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8rem;
  color: rgba(167,139,250,0.9); background: rgba(99,102,241,0.1);
  padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(99,102,241,0.15);
}
.download-install-cmd.small { font-size: 0.72rem; }
.download-install-or { font-size: 0.72rem; color: rgba(255,255,255,0.3); }

.download-btn-row { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }
.download-platform-cta {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
  padding: 9px 16px; border-radius: 12px; font-size: 0.82rem; font-weight: 600;
  text-decoration: none; color: inherit;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}
.neu-btn-primary {
  background: linear-gradient(135deg, #1e1b2e, #1a1730);
  color: rgba(139,92,246,0.95);
  box-shadow: 4px 4px 12px rgba(0,0,0,0.5), -3px -3px 8px rgba(255,255,255,0.02), 0 0 12px rgba(99,102,241,0.08);
}
.neu-btn-primary:hover { color: rgba(139,92,246,1); box-shadow: 2px 2px 8px rgba(0,0,0,0.4), 0 0 20px rgba(99,102,241,0.12); }
.neu-btn-secondary {
  background: #18181b; color: rgba(255,255,255,0.55);
  box-shadow: 4px 4px 12px rgba(0,0,0,0.5), -3px -3px 8px rgba(255,255,255,0.02);
}
.neu-btn-secondary:hover { color: rgba(255,255,255,0.85); }

.download-footer-note {
  margin: 0; padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  font-size: 0.85rem; color: rgba(255,255,255,0.4); line-height: 1.5; text-align: center;
}
.download-footer-note a { color: rgba(139,92,246,0.7); text-decoration: none; margin-left: 0.5rem; }
.download-footer-note a:hover { color: rgba(139,92,246,1); }

/* ===== Release history ===== */
.release-history-glass {
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px; padding: 1.5rem;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.release-history-title {
  margin: 0 0 1.25rem; font-size: 1.1rem; font-weight: 700; color: rgba(255,255,255,0.85);
}
.release-table-wrap { overflow-x: auto; }
.release-table {
  width: 100%; border-collapse: collapse; font-size: 0.82rem;
}
.release-table th {
  text-align: left; padding: 8px 12px;
  color: rgba(255,255,255,0.4); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.release-table td {
  padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.65); vertical-align: middle;
}
.release-latest td { background: rgba(99,102,241,0.04); }
.release-version-link { color: rgba(139,92,246,0.9); text-decoration: none; font-weight: 600; }
.release-version-link:hover { color: rgba(139,92,246,1); text-decoration: underline; }
.release-tag-latest {
  display: inline-block; margin-left: 6px;
  background: rgba(99,102,241,0.2); color: rgba(139,92,246,0.9);
  font-size: 0.68rem; font-weight: 700; padding: 1px 7px; border-radius: 20px;
  border: 1px solid rgba(99,102,241,0.3); vertical-align: middle;
}
.release-date { color: rgba(255,255,255,0.4); font-variant-numeric: tabular-nums; white-space: nowrap; }
.release-notes { color: rgba(255,255,255,0.4); font-size: 0.78rem; }

/* release badges */
.rb { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 500; white-space: nowrap; }
.rb-yes     { background: rgba(52,168,83,0.15);  color: rgba(134,239,172,0.9); border: 1px solid rgba(52,168,83,0.2); }
.rb-pending { background: rgba(250,204,21,0.12); color: rgba(250,204,21,0.8); border: 1px solid rgba(250,204,21,0.2); }
.rb-none    { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.25); border: 1px solid rgba(255,255,255,0.06); }

@media (max-width: 768px) {
  .download-app-page { padding: 16px 12px 100px; }
  .download-hero-inner { padding: 1.5rem 1rem; }
  .download-platform-grid { grid-template-columns: 1fr; }
  .release-table th:nth-child(n+6),
  .release-table td:nth-child(n+6) { display: none; }
}
</style>
