<template>
  <div class="support-page">
    <ContentHeader
      title="Boosts"
    />

    <section class="page-mobile-hero support-mobile-hero" aria-label="Support">
      <div class="page-mobile-hero-copy">
        <h1>Boosts</h1>
      </div>
    </section>

    <section class="support-directory">
      <div class="support-directory-header">
        <div class="support-directory-top">
          <div>
            <h2>Choose an artist to boost</h2>
          </div>
        </div>

        <div class="support-stats-strip" aria-label="Boost marketplace stats">
          <div class="support-stat-pill">
            <span class="support-stat-value">{{ stats.total }}</span>
          </div>
          <div class="support-stat-pill">
            <span class="support-stat-value">{{ stats.featured }}</span>
          </div>
          <div class="support-stat-pill">
            <span class="support-stat-value">{{ stats.verified }}</span>
          </div>
        </div>
        <template v-if="loading">
          <div class="support-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading artists...</p>
          </div>
        </template>
        <template v-else>
          <div v-if="filteredArtists.length && currentArtist" class="support-spotlight-wrapper">
            <div class="spotlight-controls">
              <button type="button" class="spotlight-arrow prev" @click="prevArtist" aria-label="Previous Artist">
                <i class="fas fa-chevron-left"></i>
              </button>
              
              <div
                class="spotlight-card-view"
                @touchstart.passive="handleSpotlightTouchStart"
                @touchend.passive="handleSpotlightTouchEnd"
              >
                <transition name="spotlight-swipe" mode="out-in">
                  <article 
                    :key="currentArtist.slug || currentArtist.id || currentArtist.name" 
                    class="support-card spotlight-card"
                  >
                    <router-link :to="artistRoute(currentArtist)" class="spotlight-media-flat" :aria-label="`Open ${currentArtist.name}`">
                      <div class="spotlight-image-wrap">
                        <img
                          :src="currentArtist.image || '/static/img/default-avatar.png'"
                          :alt="currentArtist.name"
                          class="spotlight-image"
                        />
                      </div>
                    </router-link>
                    <div class="support-card-body">
                      <div class="support-card-heading">
                        <div>
                          <h3>{{ currentArtist.name }}</h3>
                          <p v-if="currentArtist.genre || currentArtist.genres?.length" class="spotlight-genre">{{ currentArtist.genre || currentArtist.genres[0] }}</p>
                        </div>
                        <span v-if="currentArtist.verified" class="profile-badge profile-badge--verified">Verified</span>
                      </div>
                      <p v-if="currentArtist.description || currentArtist.bio" class="spotlight-description">{{ currentArtist.description || currentArtist.bio }}</p>
                      <div v-if="artistMediaTags.length" class="spotlight-media-tags">
                        <button
                          v-for="tag in artistMediaTags"
                          :key="tag.label"
                          type="button"
                          class="spotlight-media-tag"
                          :class="{ active: mediaPreviewTab === tag.type }"
                          @click="mediaPreviewTab = mediaPreviewTab === tag.type ? null : tag.type"
                        >
                          <i :class="tag.icon"></i> {{ tag.label }}
                          <i class="fas fa-chevron-down spotlight-media-tag-arrow" :class="{ open: mediaPreviewTab === tag.type }"></i>
                        </button>
                      </div>
                      <transition name="media-preview-slide">
                        <div v-if="mediaPreviewTab && mediaPreviewItems.length" class="media-preview-panel">
                          <div class="media-preview-list">
                            <div v-for="item in mediaPreviewItems" :key="item.id || item.title" class="media-preview-item">
                              <img v-if="item.cover_art || item.thumbnail" :src="item.cover_art || item.thumbnail" alt="" class="media-preview-thumb" />
                              <div v-else class="media-preview-thumb media-preview-thumb-placeholder">
                                <i :class="mediaPreviewTab === 'tracks' ? 'fas fa-music' : mediaPreviewTab === 'albums' ? 'fas fa-compact-disc' : 'fas fa-film'"></i>
                              </div>
                              <div class="media-preview-info">
                                <span class="media-preview-title">{{ item.title }}</span>
                                <span v-if="item.genre || item.category || item.release_date" class="media-preview-meta">{{ item.genre || item.category || item.release_date }}</span>
                              </div>
                              <button
                                type="button"
                                class="media-preview-bookmark"
                                :class="{ saved: isBookmarked(mediaBookmarkPayload(item)) }"
                                @click.stop="toggleBookmark(mediaBookmarkPayload(item))"
                                :title="isBookmarked(mediaBookmarkPayload(item)) ? 'Remove from saved' : 'Save'"
                              >
                                <i :class="isBookmarked(mediaBookmarkPayload(item)) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      </transition>
                      <div class="support-card-footer">
                        <span class="support-price-anchor">From $0.05</span>
                        <div class="support-card-cta-row">
                          <router-link :to="artistRoute(currentArtist)" class="support-secondary-cta">View</router-link>
                          <button
                            type="button"
                            class="support-primary-cta"
                            @click="goToArtistSupport(currentArtist, quickAmounts[0])"
                          >
                            Boost
                          </button>
                        </div>
                      </div>
                      <div class="boost-slider-block">
                        <div class="boost-slider-display">
                          <span class="boost-slider-amount">${{ sliderAmount < 1 ? sliderAmount.toFixed(2) : sliderAmount }}</span>
                          <span class="boost-slider-label">to {{ currentArtist.name }}</span>
                        </div>
                        <div class="boost-slider-track-wrap">
                          <input
                            type="range"
                            min="0"
                            :max="boostSteps.length - 1"
                            step="1"
                            v-model.number="sliderStepIndex"
                            class="boost-slider-input"
                            :style="`--pct: ${(sliderStepIndex / (boostSteps.length - 1)) * 100}%`"
                          />
                          <div class="boost-slider-ticks">
                            <span v-for="tick in [0.05, 1, 10, 100, 1000]" :key="tick" class="boost-tick" :class="{ active: sliderAmount >= tick }">${{ tick >= 1000 ? '1k' : tick < 1 ? tick.toFixed(2) : tick }}</span>
                          </div>
                        </div>
                        <button
                          type="button"
                          class="boost-slider-cta"
                          @click="goToArtistSupport(currentArtist, sliderAmount)"
                        >
                          <i class="fas fa-bolt"></i> Boost ${{ sliderAmount < 1 ? sliderAmount.toFixed(2) : sliderAmount }}
                        </button>
                      </div>
                    </div>
                  </article>
                </transition>
              </div>

              <button type="button" class="spotlight-arrow next" @click="nextArtist" aria-label="Next Artist">
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>

            <div class="spotlight-indicator">
              <span class="current-count">{{ currentIndex + 1 }}</span>
              <span class="count-divider">/</span>
              <span class="total-count">{{ sortedArtists.length }}</span>
            </div>
          </div>

          <div v-else class="support-state">
            <i class="fas fa-search-minus" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
            <p>No creators matched "{{ searchQuery }}"</p>
            <button class="support-amount-chip" style="margin-top: 0.5rem;" @click="searchQuery = ''; selectedType = 'all'">Clear Search</button>
          </div>

          <div class="support-directory-tools">
            <label class="support-search better-search">
              <i class="fas fa-search" aria-hidden="true"></i>
              <input v-model="searchQuery" type="search" placeholder="Search artists, bands, podcasts..." />
            </label>
            <label class="support-sort better-search support-sort-select">
              <i class="fas fa-arrow-down-wide-short" aria-hidden="true"></i>
              <select v-model="selectedSort">
                <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <div class="support-filter-pills">
            <button 
              type="button" 
              :class="['filter-pill', 'filter-pill-all', { active: selectedType === 'all' }]"
              @click="selectedType = 'all'"
            >
              <span class="filter-pill-avatar" aria-hidden="true">
                <i class="fas fa-layer-group"></i>
              </span>
              <span class="filter-pill-title">All Creators</span>
            </button>
            <button 
              v-for="filter in typeFilters" 
              :key="filter" 
              type="button" 
              :class="['filter-pill', `filter-pill-${filter}`, { active: selectedType === filter }]"
              @click="selectedType = filter"
            >
              <span class="filter-pill-avatar" aria-hidden="true">
                <i :class="filterIcon(filter)"></i>
              </span>
              <span class="filter-pill-title">{{ formatType(filter) }}</span>
            </button>
          </div>
        </template>
      </div>
    </section>

    <section class="support-portfolio" aria-label="Support Portfolio">
        <div class="support-portfolio-header">
        <div>
          <h2>Portfolio</h2>
        </div>
        <router-link v-if="!isLoggedIn" to="/login" class="support-portfolio-signin">Sign in to track</router-link>
      </div>

      <template v-if="isLoggedIn">
        <div v-if="portfolioLoading" class="support-state portfolio-state">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Loading your support portfolio...</p>
        </div>

        <template v-else-if="portfolioError">
          <div class="support-state portfolio-state">
            <i class="fas fa-chart-line"></i>
            <p>{{ portfolioError }}</p>
          </div>
        </template>

        <template v-else>
          <div class="portfolio-summary-strip">
            <div class="portfolio-metric">
              <span class="portfolio-metric-value">${{ formatCents(portfolioStats.total_boosted_cents) }}</span>
            </div>
            <div class="portfolio-metric">
              <span class="portfolio-metric-value">{{ portfolioStats.artist_count }}</span>
            </div>
            <div class="portfolio-metric">
              <span class="portfolio-metric-value">{{ portfolioStats.boost_count }}</span>
            </div>
            <div class="portfolio-metric">
              <span class="portfolio-metric-value">{{ portfolioStats.badges[0] || 'Supporter' }}</span>
            </div>
          </div>

          <div class="portfolio-progress-card">
            <div class="portfolio-progress-head">
              <div>
                <h3>{{ portfolioStats.next_badge ? `Next: ${portfolioStats.next_badge}` : 'Top tier' }}</h3>
              </div>
              <span class="portfolio-progress-meta">
                {{ portfolioStats.next_badge ? `$${formatCurrency(portfolioStats.next_badge_amount)}` : 'Keep going' }}
              </span>
            </div>
            <div class="portfolio-progress-bar" aria-hidden="true">
              <span :style="{ width: `${portfolioStats.progress_to_next ?? 100}%` }"></span>
            </div>
          </div>

          <div class="portfolio-compact-grid">
            <div class="portfolio-panel">
              <div class="portfolio-section-title">
                <h3>Holdings</h3>
              </div>

              <div v-if="portfolioHoldings.length" class="portfolio-holding-list">
                <article v-for="holding in portfolioHoldings" :key="holding.artist_name" class="portfolio-holding">
                  <div class="portfolio-holding-head">
                    <div>
                      <h4>{{ holding.artist_name }}</h4>
                      <p>{{ holding.tip_count }} boost{{ holding.tip_count === 1 ? '' : 's' }}</p>
                    </div>
                    <strong>${{ formatCents(holding.total_amount) }}</strong>
                  </div>
                  <div class="portfolio-holding-bar" aria-hidden="true">
                    <span :style="{ width: `${holding.share_pct}%` }"></span>
                  </div>
                  <div class="portfolio-holding-meta">
                    <span>{{ holding.share_pct.toFixed(0) }}% of support</span>
                    <span>Last boosted {{ formatPortfolioDate(holding.last_tip_date) }}</span>
                  </div>
                </article>
              </div>
              <div v-else class="support-state portfolio-state">
                <i class="fas fa-seedling"></i>
                <p>No boosts yet. Your first artist will show up here.</p>
              </div>
            </div>

            <div class="portfolio-panel">
              <div class="portfolio-section-title">
                <h3>Recent</h3>
              </div>

              <div v-if="portfolioRecent.length" class="portfolio-activity-list">
                <article v-for="tip in portfolioRecent" :key="tip.id" class="portfolio-activity-item">
                  <div>
                    <h4>{{ tip.artist_name }}</h4>
                    <p>{{ formatPortfolioDate(tip.created_at) }}</p>
                  </div>
                  <strong>${{ formatCents(tip.amount) }}</strong>
                </article>
              </div>
              <div v-else class="support-state portfolio-state">
                <i class="fas fa-arrow-up-right-dots"></i>
                <p>No recent boosts to show yet.</p>
              </div>
            </div>
          </div>
        </template>
      </template>

      <div v-else class="portfolio-guest">
        <div class="portfolio-guest-copy">
          <h3>Portfolio</h3>
        </div>
        <router-link to="/login" class="portfolio-guest-btn">Sign in</router-link>
      </div>
    </section>

    <section class="support-ahoy-featured" aria-label="Support Ahoy">
      <div class="support-ahoy-featured-content">
        <div class="support-ahoy-featured-copy">
          <h2>Ahoy</h2>
          <p class="ahoy-tier-description">{{ ahoyTierDescription }}</p>
        </div>
        <div class="support-ahoy-actions">
          <div class="tier-slider-wrapper">
            <div class="tier-info">
              <h3 class="tier-amount">${{ selectedTier.amount }}</h3>
            </div>
            
            <input 
              type="range" 
              class="tier-slider" 
              min="0" 
              :max="ahoyTiers.length - 1" 
              v-model.number="sliderIndex" 
              aria-label="Select support amount"
            />
            <div class="tier-slider-labels">
              <span>${{ ahoyTiers[0].amount }}</span>
              <span>${{ ahoyTiers[ahoyTiers.length - 1].amount }}</span>
            </div>

            <button 
              type="button" 
              class="tier-submit-btn"
              @click="goToAhoySupport(selectedTier.amount)"
            >
              Add Ahoy ${{ selectedTier.amount }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="support-intro faq-section">
      <div class="support-intro-copy">
        <h2>Boost math</h2>
        
        <div class="example-boost-widget">
          <div class="widget-header">Checkout Preview</div>
          <div class="widget-row interactive-row">
            <span>Boost Amount:</span>
            <div class="example-input-wrapper">
              <span class="currency-symbol">$</span>
              <input type="number" v-model.number="exampleBoostAmount" min="1" max="10000" />
            </div>
          </div>
          <div class="widget-row">
            <span>Processing Fee (4.9%):</span>
            <strong>${{ exampleAhoyFee.toFixed(2) }}</strong>
          </div>
          <div class="widget-row">
            <span>Stripe Fee (2.9% + 30¢):</span>
            <strong>${{ exampleStripeFee.toFixed(2) }}</strong>
          </div>
          <div class="widget-row">
            <span>Est. Tax (8%):</span>
            <strong>${{ exampleTax.toFixed(2) }}</strong>
          </div>
          <div class="widget-divider"></div>
          <div class="widget-row total-row">
            <span>You Pay:</span>
            <strong>${{ exampleTotalCharged.toFixed(2) }}</strong>
          </div>
          <div class="widget-row total-row payout-row" style="margin-top: 0.5rem; color: rgba(255, 255, 255, 0.86);">
            <span>Artist Receives:</span>
            <strong>${{ (exampleBoostAmount || 0).toFixed(2) }}</strong>
          </div>
          <div class="widget-badge">Payout</div>
        </div>
      </div>

      <div class="support-faq-accordion" aria-label="Support FAQ">
        <details class="faq-details">
          <summary class="faq-summary">
            <strong>Find artists</strong>
            <i class="fas fa-chevron-down faq-icon"></i>
          </summary>
        </details>
      
        
        <details class="faq-details">
          <summary class="faq-summary">
            <strong>Payout</strong>
            <i class="fas fa-chevron-down faq-icon"></i>
          </summary>
        </details>
        
        <details class="faq-details">
          <summary class="faq-summary">
            <strong>Ahoy support</strong>
            <i class="fas fa-chevron-down faq-icon"></i>
          </summary>
        </details>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, apiFetchCached } from '../composables/useApi'
import { trackEvent } from '../composables/useAnalytics'
import { useAuth } from '../composables/useAuth'
import { useBookmarks } from '../composables/useBookmarks'
import ContentHeader from '../components/ContentHeader.vue'

const router = useRouter()
const auth = useAuth()
const { isBookmarked, toggle: toggleBookmark } = useBookmarks()
const isLoggedIn = computed(() => auth.isLoggedIn.value)
const artists = ref([])
const loading = ref(true)
const mediaPreviewTab = ref(null)
const searchQuery = ref('')
const selectedType = ref('all')
const selectedSort = ref('featured')
const quickAmounts = [0.05, 0.50, 5]
const customArtistAmounts = ref({})

// Boost steps: $0.05 -> $1000
const boostSteps = [0.05, 0.10, 0.25, 0.50, 0.75, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000]
const sliderStepIndex = ref(0)
const sliderAmount = computed(() => boostSteps[sliderStepIndex.value] || 0.05)
const exampleBoostAmount = ref(20)

const exampleStripeFee = computed(() => {
  const amt = exampleBoostAmount.value || 0;
  return Math.round(((amt * 0.029) + 0.30) * 100) / 100;
})
const exampleTax = computed(() => {
  const amt = exampleBoostAmount.value || 0;
  return Math.round((amt * 0.08) * 100) / 100;
})
const exampleAhoyFee = computed(() => {
  const amt = exampleBoostAmount.value || 0;
  return Math.round((amt * 0.05) * 100) / 100;
})
const exampleTotalCharged = computed(() => {
  const amt = exampleBoostAmount.value || 0;
  return Math.round((amt + exampleAhoyFee.value + exampleStripeFee.value + exampleTax.value) * 100) / 100;
})

const ahoyTiers = [
  { amount: 5, perk: 'Supporter' },
  { amount: 10, perk: 'Backer' },
  { amount: 25, perk: 'Patron' },
  { amount: 50, perk: 'VIP' },
  { amount: 100, perk: 'Champion' },
  { amount: 250, perk: 'Benefactor' },
  { amount: 500, perk: 'Legend' },
  { amount: 1000, perk: 'Executive Producer (Listed on About page)' },
]
const sliderIndex = ref(2)
const selectedTier = computed(() => ahoyTiers[sliderIndex.value])
const ahoyTierDescription = computed(() => {
  const amount = Number(selectedTier.value?.amount || 0)
  if (amount <= 5) return 'Small but real support for daily upkeep.'
  if (amount <= 10) return 'Helps cover the basics and keep things moving.'
  if (amount <= 25) return 'A solid push toward new work and polish.'
  if (amount <= 50) return 'Meaningful support for releases and stability.'
  if (amount <= 100) return 'Big backing that helps the platform grow.'
  if (amount <= 250) return 'Major support for the road ahead.'
  if (amount <= 500) return 'Serious patron energy for long-term growth.'
  return 'Top-tier backing for the whole Ahoy stack.'
})
const sortOptions = [
  { value: 'featured', label: 'Featured' },
  { value: 'popular', label: 'Most active' },
  { value: 'az', label: 'A-Z' },
  { value: 'verified', label: 'Verified first' },
]
const portfolioLoading = ref(false)
const portfolioError = ref('')
const portfolioStats = ref({
  xp: 0,
  badges: [],
  total_boosted: 0,
  total_boosted_cents: 0,
  boost_count: 0,
  next_badge: null,
  next_badge_amount: null,
  progress_to_next: null,
  artist_count: 0,
})
const portfolioHoldings = ref([])
const portfolioRecent = ref([])

const typeFilters = computed(() => {
  const values = new Set()
  for (const artist of artists.value) {
    const type = normalizedType(artist)
    if (type) values.add(type)
  }
  return Array.from(values).sort()
})

const filteredArtists = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return artists.value.filter((artist) => {
    const type = normalizedType(artist)
    const matchesType = selectedType.value === 'all' || type === selectedType.value
    if (!matchesType) return false
    if (!q) return true
    const haystack = [
      artist.name,
      artist.description,
      artist.genre,
      ...(Array.isArray(artist.genres) ? artist.genres : []),
      type,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return haystack.includes(q)
  })
})

const sortedArtists = computed(() => {
  const list = filteredArtists.value.slice()
  const nameSort = (a, b) => String(a?.name || '').localeCompare(String(b?.name || ''), undefined, { sensitivity: 'base', numeric: true })

  if (selectedSort.value === 'az') {
    return list.sort(nameSort)
  }

  if (selectedSort.value === 'verified') {
    return list.sort((a, b) => Number(Boolean(b?.verified)) - Number(Boolean(a?.verified)) || nameSort(a, b))
  }

  if (selectedSort.value === 'popular') {
    return list.sort((a, b) => Number(b?.followers || 0) - Number(a?.followers || 0) || nameSort(a, b))
  }

  return list.sort((a, b) => Number(Boolean(b?.featured)) - Number(Boolean(a?.featured)) || Number(b?.followers || 0) - Number(a?.followers || 0) || nameSort(a, b))
})

const stats = computed(() => ({
  total: artists.value.length,
  featured: artists.value.filter((artist) => Boolean(artist?.featured)).length,
  verified: artists.value.filter((artist) => Boolean(artist?.verified)).length,
}))

const currentIndex = ref(0)
const touchStartX = ref(0)
const touchStartY = ref(0)
const currentArtist = computed(() => {
  if (!sortedArtists.value.length) return null
  const idx = Math.min(currentIndex.value, sortedArtists.value.length - 1)
  return sortedArtists.value[Math.max(0, idx)] || sortedArtists.value[0]
})

const artistMediaTags = computed(() => {
  const a = currentArtist.value
  if (!a) return []
  const tags = []
  const trackCount = Array.isArray(a.tracks) ? a.tracks.length : 0
  const albumCount = Array.isArray(a.albums) ? a.albums.length : 0
  const showCount = Array.isArray(a.shows) ? a.shows.length : 0
  if (trackCount) tags.push({ icon: 'fas fa-music', label: `${trackCount} track${trackCount !== 1 ? 's' : ''}`, type: 'tracks' })
  if (albumCount) tags.push({ icon: 'fas fa-compact-disc', label: `${albumCount} album${albumCount !== 1 ? 's' : ''}`, type: 'albums' })
  if (showCount) tags.push({ icon: 'fas fa-film', label: `${showCount} show${showCount !== 1 ? 's' : ''}`, type: 'shows' })
  return tags
})

const mediaPreviewItems = computed(() => {
  const a = currentArtist.value
  if (!a || !mediaPreviewTab.value) return []
  const tab = mediaPreviewTab.value
  if (tab === 'tracks') return (a.tracks || []).slice(0, 8)
  if (tab === 'albums') return (a.albums || []).slice(0, 8)
  if (tab === 'shows') return (a.shows || []).slice(0, 8)
  return []
})

function mediaBookmarkPayload(item) {
  const a = currentArtist.value
  const tab = mediaPreviewTab.value
  return {
    id: item.id || item.track_ref_id || item.album_id || item.show_ref_id || item.title,
    slug: item.id || item.track_ref_id || item.album_id || item.show_ref_id,
    title: item.title,
    artist: a?.name || '',
    cover_art: item.cover_art || item.thumbnail || '',
    type: tab === 'tracks' ? 'track' : tab === 'albums' ? 'album' : 'show',
    _type: tab === 'tracks' ? 'track' : tab === 'albums' ? 'album' : 'show',
  }
}

function nextArtist() {
  if (!sortedArtists.value.length) return
  currentIndex.value = (currentIndex.value + 1) % sortedArtists.value.length
}

function prevArtist() {
  if (!sortedArtists.value.length) return
  currentIndex.value = (currentIndex.value - 1 + sortedArtists.value.length) % sortedArtists.value.length
}

function formatCurrency(amount) {
  const value = Number(amount || 0)
  if (!Number.isFinite(value)) return '0.00'
  return value.toFixed(2)
}

function formatCents(amount) {
  const value = Number(amount || 0)
  if (!Number.isFinite(value)) return '0.00'
  return (value / 100).toFixed(2)
}

function formatPortfolioDate(value) {
  if (!value) return 'recently'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function handleSpotlightTouchStart(e) {
  const touch = e.changedTouches?.[0]
  if (!touch) return
  touchStartX.value = touch.clientX
  touchStartY.value = touch.clientY
}

function handleSpotlightTouchEnd(e) {
  const touch = e.changedTouches?.[0]
  if (!touch) return
  const deltaX = touch.clientX - touchStartX.value
  const deltaY = touch.clientY - touchStartY.value
  if (Math.abs(deltaX) < 36 || Math.abs(deltaX) < Math.abs(deltaY)) return
  if (deltaX < 0) nextArtist()
  else prevArtist()
}

watch([sortedArtists, selectedType, searchQuery, selectedSort], () => {
  currentIndex.value = 0
  mediaPreviewTab.value = null
})

watch(currentIndex, () => {
  mediaPreviewTab.value = null
})

async function loadPortfolio() {
  if (!auth.isLoggedIn.value) return
  portfolioLoading.value = true
  portfolioError.value = ''
  try {
    const [statsRes, historyRes, recentRes] = await Promise.all([
      apiFetch('/api/gamification/user/boost-stats'),
      apiFetch('/api/tips/history'),
      apiFetch('/api/tips'),
    ])

    const totalBoosted = Number(statsRes?.total_boosted || 0)
    portfolioStats.value = {
      xp: Number(statsRes?.xp || 0),
      badges: Array.isArray(statsRes?.badges) ? statsRes.badges : [],
      total_boosted: totalBoosted,
      total_boosted_cents: Math.round(totalBoosted * 100),
      boost_count: Number(statsRes?.boost_count || 0),
      next_badge: statsRes?.next_badge || null,
      next_badge_amount: statsRes?.next_badge_amount ?? null,
      progress_to_next: statsRes?.progress_to_next ?? null,
      artist_count: Number(historyRes?.artist_count || 0),
    }

    const history = Array.isArray(historyRes?.history) ? historyRes.history : []
    const totalAll = Number(historyRes?.total_all || 0) || history.reduce((sum, row) => sum + Number(row.total_amount || 0), 0)
    portfolioHoldings.value = history
      .map((row) => ({
        ...row,
        total_amount: Number(row.total_amount || 0),
        tip_count: Number(row.tip_count || 0),
        share_pct: totalAll > 0 ? Math.max(0, Math.min(100, (Number(row.total_amount || 0) / totalAll) * 100)) : 0,
      }))
      .slice(0, 6)

    const recentTips = Array.isArray(recentRes?.tips) ? recentRes.tips : []
    portfolioRecent.value = recentTips.slice(0, 5).map((tip) => ({
      ...tip,
      amount: Number(tip.amount || 0),
    }))
  } catch (e) {
    if (e?.status === 401) {
      portfolioError.value = 'Sign in to view your portfolio.'
    } else {
      portfolioError.value = 'Could not load portfolio data right now.'
    }
    portfolioHoldings.value = []
    portfolioRecent.value = []
  } finally {
    portfolioLoading.value = false
  }
}

function handleKeyDown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  if (e.key === 'ArrowRight') nextArtist()
  if (e.key === 'ArrowLeft') prevArtist()
}

function shuffleArray(arr) {
  const shuffled = [...arr]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled
}

function normalizedType(artist) {
  return String(artist?.type || '').trim().toLowerCase()
}

function formatType(type) {
  return type ? type.charAt(0).toUpperCase() + type.slice(1) : 'Artist'
}

function filterIcon(type) {
  switch (type) {
    case 'music':
    case 'musician':
      return 'fas fa-music'
    case 'host':
      return 'fas fa-podcast'
    case 'filmmaker':
      return 'fas fa-film'
    case 'athlete':
      return 'fas fa-running'
    default:
      return 'fas fa-tag'
  }
}

function artistIdentifier(artist) {
  return artist.slug || artist.id || artist.name
}

function artistRoute(artist) {
  return `/artists/${artistIdentifier(artist)}`
}

function goToArtistSupport(artist, amount) {
  if (!amount || amount < 1) return
  trackEvent('support_intent', {
    context: 'support_directory',
    artist_id: String(artistIdentifier(artist)),
    artist_name: artist.name || '',
    amount: Number(amount),
  })
  router.push({
    path: '/checkout',
    query: {
      type: 'boost',
      artist_id: String(artistIdentifier(artist)),
      artist_name: artist.name,
      amount: String(amount),
    },
  })
}

function goToAhoySupport(amount) {
  if (!amount || amount < 1) return
  trackEvent('support_intent', {
    context: 'platform_boost',
    artist_id: 'ahoy-indie-media',
    artist_name: 'Ahoy Indie Media',
    amount: Number(amount),
  })
  router.push({
    path: '/checkout',
    query: {
      type: 'boost',
      artist_id: 'ahoy-indie-media',
      artist_name: 'Ahoy Indie Media',
      amount: String(amount),
      support_target: 'ahoy',
    },
  })
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeyDown)
  try {
    const data = await apiFetchCached('/api/artists')
    const list = Array.isArray(data) ? data : (data.artists || [])
    artists.value = shuffleArray(list)
  } catch (e) {
    console.warn('Failed to load artists for support page:', e)
    artists.value = []
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

watch(() => auth.isLoggedIn.value, (loggedIn) => {
  if (loggedIn) {
    loadPortfolio()
  } else {
    portfolioHoldings.value = []
    portfolioRecent.value = []
    portfolioError.value = ''
  }
}, { immediate: true })
</script>

<style scoped>
.support-page {
  padding: 0;
}

.support-mobile-hero {
  display: none;
}

.support-intro,
.support-directory {
  margin: 0 1rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.035);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(18px) saturate(120%);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
}

.support-intro {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 1.25rem;
  padding: 1.35rem;
}

.support-intro-copy h2,
.support-directory-header h2,
.support-ahoy-copy h2 {
  margin: 0 0 0.55rem;
  font-size: clamp(1.35rem, 2.1vw, 2.05rem);
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.support-faq-accordion {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  width: 100%;
}

.faq-details {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  overflow: hidden;
  transition: background 0.2s ease;
}

.faq-details:hover {
  background: rgba(255, 255, 255, 0.07);
}

.faq-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.4rem;
  cursor: pointer;
  list-style: none; /* Hide default triangle */
}

.faq-summary::-webkit-details-marker {
  display: none;
}

.faq-summary strong {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
}

.faq-icon {
  color: rgba(255, 255, 255, 0.5);
  transition: transform 0.3s ease;
}

.faq-details[open] .faq-icon {
  transform: rotate(180deg);
}

.support-ahoy-featured {
  margin: 0 1rem 1rem;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.11);
  padding: 1.35rem;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(18px) saturate(120%);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
}

.support-ahoy-featured-content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 420px);
  gap: 1.25rem;
  align-items: center;
  text-align: left;
}

.support-ahoy-featured h2 {
  font-size: clamp(1.4rem, 2.5vw, 2.25rem);
  font-weight: 900;
  letter-spacing: -0.04em;
  margin: 0 0 1.2rem;
  line-height: 1.1;
  color: #fff;
}

.tier-slider-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 420px;
  margin: 0;
  background: rgba(0, 0, 0, 0.18);
  padding: 1.25rem;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tier-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ahoy-tier-description {
  margin: -0.35rem 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.92rem;
  line-height: 1.45;
  max-width: 34ch;
}

.tier-amount {
  font-size: 2rem;
  font-weight: 900;
  color: #fff;
  margin: 0;
  line-height: 1;
}

.tier-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  outline: none;
  border-radius: 999px;
  margin: 0.85rem 0;
}

.tier-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #dfe6ec;
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.08);
  transition: transform 0.2s ease;
}

.tier-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #dfe6ec;
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.08);
  border: none;
  transition: transform 0.2s ease;
}

.tier-slider::-webkit-slider-thumb:hover,
.tier-slider::-moz-range-thumb:hover {
  transform: scale(1.05);
}

.tier-slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 700;
  margin-top: -0.5rem;
}

.tier-submit-btn {
  background: rgba(255, 255, 255, 0.92);
  color: #101418;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 0.85rem;
  font: inherit;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 0.5rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.14);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.tier-submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.support-ahoy-actions {
  display: flex;
  justify-content: center;
  width: 100%;
}

.support-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
}

.support-amount-chip {
  min-height: 38px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  padding: 0.55rem 1rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.support-amount-chip:hover,
.support-amount-chip:focus-visible {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.24);
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  box-shadow: none;
}

.support-directory {
  padding: 1.35rem;
}

.support-directory-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: -1.35rem -1.35rem 1rem;
  padding: 1.35rem 1.35rem 1rem;
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(10, 10, 10, 0.6);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.support-directory-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}

.support-directory-top h2 {
  margin-bottom: 0;
}

.support-directory-tools {
  flex-grow: 1;
  display: flex;
  justify-content: flex-end;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.better-search {
  flex-grow: 1;
  max-width: 360px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  padding: 0 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  height: 46px;
  transition: all 0.2s ease;
}

.better-search:focus-within {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.28);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.08);
}

.better-search input {
  background: transparent;
  border: none;
  color: #fff;
  font: inherit;
  font-size: 0.95rem;
  width: 100%;
  height: 100%;
  outline: none;
}

.better-search i {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1rem;
}

.support-sort {
  max-width: 220px;
}

.support-sort select {
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  border: none;
  color: #fff;
  font: inherit;
  width: 100%;
  height: 100%;
  outline: none;
  cursor: pointer;
}

.support-stats-strip {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.support-stat-pill {
  flex: 0 0 auto;
  min-width: 72px;
  padding: 0.65rem 0.75rem;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  display: grid;
}

.support-stat-value {
  font-size: 1.05rem;
  font-weight: 900;
  color: #fff;
  line-height: 1;
}

.support-filter-pills {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
  gap: 0.65rem;
  padding-bottom: 0.25rem;
}

.filter-pill {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.8rem;
  width: 100%;
  min-height: 74px;
  white-space: normal;
  text-align: left;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.82);
  padding: 0.75rem 0.85rem;
  font: inherit;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
  box-shadow: none;
}

.filter-pill-avatar {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

.filter-pill-avatar i {
  font-size: 0.9rem;
  opacity: 0.9;
}

.filter-pill-title {
  font-size: 1rem;
  line-height: 1.05;
  color: #fff;
  white-space: nowrap;
}

.filter-pill:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  transform: none;
}

.filter-pill.active {
  background: linear-gradient(135deg, rgba(104, 116, 132, 0.24), rgba(28, 32, 39, 0.96));
  color: #fff;
  border-color: rgba(255, 255, 255, 0.2);
}

.filter-pill.active .filter-pill-avatar {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.filter-pill.active i {
  opacity: 1;
}

.filter-pill-all {
  grid-column: 1 / -1;
}

.filter-pill-host,
.filter-pill-filmmaker {
  background: rgba(255, 255, 255, 0.045);
}

.support-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 1.25rem;
}

.support-card {
  overflow: hidden;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.support-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.045);
}

.support-card-media {
  display: block;
  aspect-ratio: 1.4;
  overflow: hidden;
  background: #000;
}

.support-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.4s ease;
}

.support-card:hover .support-card-media img {
  transform: scale(1.04);
}

.support-card-body {
  display: grid;
  gap: 0.7rem;
  padding: 1rem;
  background: rgba(8, 10, 14, 0.68);
}

.support-card-heading {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.support-card-heading h3 {
  margin: 0 0 0.2rem;
  font-size: 1.08rem;
  font-weight: 900;
  letter-spacing: -0.03em;
}

.profile-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.035);
  color: rgba(255, 255, 255, 0.72);
}

.profile-badge--verified {
  background: rgba(255, 255, 255, 0.05);
}

.support-price-anchor {
  display: inline-flex;
  align-self: flex-start;
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.035);
  color: rgba(255, 255, 255, 0.82);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.support-card-cta-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.support-secondary-cta,
.support-primary-cta {
  min-height: 34px;
  border-radius: 999px;
  padding: 0.45rem 0.75rem;
  font: inherit;
  font-weight: 800;
  font-size: 0.82rem;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.support-secondary-cta {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.84);
}

.support-primary-cta {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.9);
  color: #101418;
  cursor: pointer;
}

.support-secondary-cta:hover,
.support-secondary-cta:focus-visible {
  background: rgba(255, 255, 255, 0.05);
}

.support-primary-cta:hover,
.support-primary-cta:focus-visible {
  filter: brightness(0.98);
}

.support-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
  padding-top: 0.1rem;
}

.support-state {
  display: grid;
  place-items: center;
  gap: 0.5rem;
  min-height: 180px;
  color: rgba(255, 255, 255, 0.62);
}

.support-portfolio {
  margin: 0 1rem 1rem;
  padding: 1.15rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.035);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(18px) saturate(120%);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
}

.support-portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.85rem;
}

.support-portfolio-header h2 {
  margin: 0 0 0.35rem;
  font-size: clamp(1.35rem, 2.3vw, 1.95rem);
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.05;
}

.support-portfolio-header p {
  max-width: 60ch;
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.45;
  font-size: 0.88rem;
}

.support-portfolio-signin,
.portfolio-guest-btn {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.55rem 0.9rem;
  background: rgba(255, 255, 255, 0.92);
  color: #101418;
  text-decoration: none;
  font-weight: 800;
  font: inherit;
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
}

.portfolio-state {
  min-height: 180px;
}

.portfolio-summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;
  margin-bottom: 0.7rem;
}

.portfolio-metric {
  padding: 0.7rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  display: grid;
  gap: 0.28rem;
}

.portfolio-metric-value {
  font-size: 1.05rem;
  font-weight: 900;
  color: #fff;
}

.portfolio-progress-card {
  margin-bottom: 0.7rem;
  padding: 0.8rem 0.9rem;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.portfolio-progress-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.55rem;
}

.portfolio-progress-head h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 900;
}

.portfolio-progress-meta {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 700;
  white-space: nowrap;
}

.portfolio-progress-bar,
.portfolio-holding-bar {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.portfolio-progress-bar span,
.portfolio-holding-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.54));
}

.portfolio-compact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}

.portfolio-panel {
  padding: 0.8rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.portfolio-section-title {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin-bottom: 0.55rem;
}

.portfolio-section-title h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 900;
}

.portfolio-holding-list,
.portfolio-activity-list {
  display: grid;
  gap: 0.45rem;
}

.portfolio-holding,
.portfolio-activity-item {
  padding: 0.65rem;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.portfolio-holding-head,
.portfolio-activity-item {
  display: flex;
  justify-content: space-between;
  gap: 0.9rem;
  align-items: center;
}

.portfolio-holding-head h4,
.portfolio-activity-item h4 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 900;
}

.portfolio-holding-head p,
.portfolio-activity-item p {
  margin: 0.2rem 0 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.72rem;
}

.portfolio-holding-head strong,
.portfolio-activity-item strong {
  font-size: 0.88rem;
  font-weight: 900;
  color: #fff;
  white-space: nowrap;
}

.portfolio-holding-bar {
  margin: 0.4rem 0 0.35rem;
  height: 6px;
}

.portfolio-holding-meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.56);
  font-size: 0.68rem;
}

.portfolio-guest {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.8rem 0.9rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.portfolio-guest-copy h3 {
  margin: 0 0 0.35rem;
  font-size: 0.92rem;
  font-weight: 900;
}

.portfolio-guest-copy p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  line-height: 1.45;
  font-size: 0.85rem;
}

.artist-custom-boost {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 0 0.5rem 0 0.8rem;
  min-height: 44px;
  flex-grow: 1;
  max-width: 140px;
}

.artist-custom-boost input {
  background: transparent;
  border: none;
  color: #fff;
  font: inherit;
  font-weight: 700;
  width: 100%;
  outline: none;
  padding: 0 0.25rem;
}

.artist-custom-boost input::-webkit-outer-spin-button,
.artist-custom-boost input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.artist-custom-boost input[type=number] {
  -moz-appearance: textfield;
}

.artist-custom-boost button {
  background: rgba(255, 255, 255, 0.9);
  color: #101418;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.artist-custom-boost button:hover {
  transform: scale(1.03);
  background: rgba(255, 255, 255, 0.96);
}

.example-boost-widget {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  margin-top: 2rem;
  max-width: 320px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.widget-header {
  font-size: 0.85rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 1rem;
}

.widget-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 1.05rem;
}

.highlight-zero {
  color: rgba(255, 255, 255, 0.82);
}

.widget-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 0.8rem 0;
}

.total-row {
  font-weight: 800;
  font-size: 1.2rem;
  color: #fff;
}

.widget-badge {
  position: absolute;
  top: 1.2rem;
  right: -2rem;
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.92);
  font-weight: 800;
  font-size: 0.75rem;
  padding: 0.25rem 2.5rem;
  transform: rotate(45deg);
  box-shadow: none;
}

.example-input-wrapper {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  max-width: 90px;
}

.example-input-wrapper input {
  background: transparent;
  border: none;
  color: #fff;
  font: inherit;
  font-weight: 800;
  width: 100%;
  outline: none;
  padding: 0 0.1rem;
}

.example-input-wrapper input::-webkit-outer-spin-button,
.example-input-wrapper input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.example-input-wrapper input[type=number] {
  -moz-appearance: textfield;
}

.interactive-row {
  align-items: center;
}

@media (max-width: 768px) {
  :deep(.content-header) {
    display: none !important;
  }

  .support-mobile-hero {
    display: block;
    margin: 2px var(--mobile-gutter, 10px) 12px !important;
    padding: 22px 16px 16px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.035);
    box-shadow: 0 18px 36px rgba(0, 0, 0, 0.18);
    backdrop-filter: blur(18px) saturate(120%);
    -webkit-backdrop-filter: blur(18px) saturate(120%);
  }

  .page-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
  }

  .support-intro,
  .support-ahoy-featured,
  .support-directory {
    margin: 0 var(--mobile-gutter, 10px) 12px;
    border-radius: 24px;
  }

  .support-intro {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .support-ahoy-featured {
    padding: 2.5rem 1.5rem;
  }

  .support-ahoy-featured-content {
    grid-template-columns: 1fr;
    text-align: left;
  }

  .support-ahoy-actions {
    justify-content: flex-start;
  }

  .support-directory-header {
    align-items: stretch;
    flex-direction: column;
    gap: 1.25rem;
    position: relative;
    top: auto;
    background: transparent;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    margin: 0 0 1.5rem;
    padding: 0;
    border-bottom: none;
  }

  .support-search input {
    width: 100%;
  }

  .support-directory-tools {
    flex-direction: column;
    align-items: stretch;
  }

  .support-type-select {
    width: 100%;
  }

  .support-sort {
    max-width: none;
  }

  .support-sort select {
    width: 100%;
  }

  .filter-pill {
    min-height: 70px;
  }

  .filter-pill-avatar {
    width: 40px;
    height: 40px;
  }

  .support-card-heading {
    flex-direction: column;
  }

  .support-directory,
  .support-intro {
    padding: 1.5rem;
  }

  .support-portfolio {
    margin: 0 var(--mobile-gutter, 10px) 12px;
    padding: 1.25rem;
    border-radius: 24px;
  }

  .support-portfolio-header {
    align-items: stretch;
  }

  .portfolio-summary-strip,
  .portfolio-compact-grid {
    grid-template-columns: 1fr;
  }

  .portfolio-holding-head,
  .portfolio-activity-item,
  .portfolio-holding-meta,
  .portfolio-progress-head,
  .portfolio-guest {
    align-items: flex-start;
    flex-direction: column;
  }

  .support-intro-copy h2, 
  .support-directory-header h2, 
  .support-ahoy-featured h2 {
    font-size: 1.8rem;
  }
}

.support-spotlight-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  margin: 1rem 0 0.9rem;
}

.spotlight-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  max-width: 660px;
}

.spotlight-card-view {
  flex: 1;
  width: min(100%, 520px);
  max-width: 520px;
}

@media (min-width: 769px) {
  .spotlight-card-view {
    min-width: 450px;
  }
}

.spotlight-card {
  width: 100%;
  box-shadow: 0 20px 42px rgba(0, 0, 0, 0.38);
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.035);
}

.spotlight-arrow {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
  outline: none;
}

.spotlight-arrow:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: scale(1.03);
  box-shadow: none;
}

.spotlight-arrow:active {
  transform: scale(0.95);
}

.spotlight-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(0, 0, 0, 0.22);
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

.current-count {
  color: rgba(255, 255, 255, 0.92);
}
.count-divider {
  opacity: 0.3;
}

/* Spotlight Fade/Slide Transition */
.spotlight-swipe-enter-active,
.spotlight-swipe-leave-active {
  transition: all 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.spotlight-swipe-enter-from {
  opacity: 0;
  transform: translateX(22px);
}

.spotlight-swipe-leave-to {
  opacity: 0;
  transform: translateX(-22px);
}

@media (max-width: 768px) {
  .spotlight-controls {
    gap: 0.75rem;
    position: relative;
  }
  
  .spotlight-arrow {
    position: absolute;
    z-index: 5;
    width: 42px;
    height: 42px;
    top: 35%;
    transform: translateY(-50%);
  }
  
  .spotlight-arrow.prev {
    left: -10px;
  }
  
  .spotlight-arrow.next {
    right: -10px;
  }
  
  .spotlight-arrow:hover {
    transform: translateY(-50%) scale(1.05);
  }
  
  .spotlight-card-view {
    max-width: 100%;
    width: 100%;
  }

  .spotlight-media-flat {
    aspect-ratio: 1.45 / 1;
    min-height: 200px;
    height: auto;
  }

  .spotlight-image {
    width: 160px;
    height: 160px;
  }
}

.spotlight-media-flat {
  display: flex;
  justify-content: center;
  align-items: center;
  aspect-ratio: 1.55 / 1;
  min-height: 286px;
  height: auto;
  width: 100%;
  margin-top: 1rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border-radius: 22px 22px 18px 18px;
  background: rgba(255, 255, 255, 0.03);
}

.spotlight-image-wrap {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.spotlight-glow-background {
  position: absolute;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: transparent;
  filter: none;
}

.spotlight-image {
  width: clamp(160px, 38vw, 200px);
  height: clamp(160px, 38vw, 200px);
  border-radius: 50%;
  object-fit: cover;
  display: block;
  border: 4px solid rgba(255, 255, 255, 0.12);
  box-shadow: none;
  filter: saturate(0.9) brightness(1.0);
  position: relative;
  z-index: 1;
  transition: transform 0.35s ease, box-shadow 0.35s ease, filter 0.35s ease;
}

.spotlight-media-flat:hover .spotlight-image,
.spotlight-media-flat:focus-visible .spotlight-image {
  transform: none;
  filter: saturate(0.92) brightness(1.02);
  box-shadow: none;
}

.spotlight-media-flat::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 30%, rgba(0, 0, 0, 0.16) 100%);
  pointer-events: none;
}

.spotlight-genre {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.42);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.spotlight-description {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.62);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.spotlight-media-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.spotlight-media-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.58);
  white-space: nowrap;
}

.spotlight-media-tag i:first-child {
  font-size: 0.65rem;
  opacity: 0.7;
}

.spotlight-media-tag-arrow {
  font-size: 0.55rem;
  opacity: 0.4;
  transition: transform 0.2s ease;
  margin-left: 0.1rem;
}

.spotlight-media-tag-arrow.open {
  transform: rotate(180deg);
  opacity: 0.7;
}

.spotlight-media-tag.active {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.82);
}

.media-preview-panel {
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 0.5rem;
  max-height: 240px;
  overflow-y: auto;
}

.media-preview-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.media-preview-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.5rem;
  border-radius: 10px;
  transition: background 0.15s ease;
}

.media-preview-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.media-preview-thumb {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
}

.media-preview-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.25);
  font-size: 0.85rem;
}

.media-preview-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.media-preview-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.88);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.media-preview-meta {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.media-preview-bookmark {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.media-preview-bookmark:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
}

.media-preview-bookmark.saved {
  color: rgba(255, 200, 60, 0.9);
  border-color: rgba(255, 200, 60, 0.25);
}

.media-preview-bookmark.saved:hover {
  background: rgba(255, 200, 60, 0.1);
}

/* Preview slide transition */
.media-preview-slide-enter-active,
.media-preview-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  overflow: hidden;
}

.media-preview-slide-enter-from,
.media-preview-slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
}

.media-preview-slide-enter-to,
.media-preview-slide-leave-from {
  opacity: 1;
  max-height: 280px;
}

/* ---- Boost Slider ---- */
.boost-slider-block {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.9rem 0 0.25rem;
}

.boost-slider-display {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.boost-slider-amount {
  font-size: 2.2rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -1.5px;
  line-height: 1;
  transition: transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.boost-slider-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.boost-slider-track-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.boost-slider-input {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    rgba(255, 0, 96, 0.85) 0%,
    rgba(255, 0, 96, 0.85) var(--pct, 0%),
    rgba(255, 255, 255, 0.12) var(--pct, 0%),
    rgba(255, 255, 255, 0.12) 100%
  );
  outline: none;
  cursor: pointer;
}

.boost-slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(255, 0, 96, 0.35), 0 2px 8px rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.15s;
}

.boost-slider-input:active::-webkit-slider-thumb {
  transform: scale(1.2);
  box-shadow: 0 0 0 5px rgba(255, 0, 96, 0.4), 0 2px 12px rgba(0, 0, 0, 0.5);
}

.boost-slider-input::-moz-range-thumb {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(255, 0, 96, 0.35), 0 2px 8px rgba(0, 0, 0, 0.4);
  cursor: pointer;
}

.boost-slider-ticks {
  display: flex;
  justify-content: space-between;
  padding: 0 2px;
}

.boost-tick {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.28);
  transition: color 0.2s;
}

.boost-tick.active {
  color: rgba(255, 0, 96, 0.7);
}

.boost-slider-cta {
  width: 100%;
  padding: 0.8rem 1rem;
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #ff0060, #ff3d7f);
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  box-shadow: 0 6px 20px rgba(255, 0, 96, 0.35);
  transition: transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.15s;
  letter-spacing: 0.01em;
}

.boost-slider-cta:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(255, 0, 96, 0.45);
}

.boost-slider-cta:active {
  transform: scale(0.97);
}
</style>
