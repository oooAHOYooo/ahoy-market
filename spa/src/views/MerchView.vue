<template>
  <div class="merch-shell">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Merch"
      subtitle="Gear and goods from the Ahoy community."
    />
    <section class="merch-mobile-hero" aria-label="Merch store">
      <div class="merch-mobile-hero-copy">
        <span class="merch-mobile-eyebrow">Store</span>
        <h1>Merch</h1>
        <p>{{ items.length ? `${items.length} item${items.length === 1 ? '' : 's'} from the in house Ahoy merch team` : 'Gear and goods from the Ahoy merch team.' }}</p>
      </div>
    </section>
    <!-- Controls: search + sort (Flask: merch-controls) -->
    <div class="merch-controls">
      <div class="merch-search" role="search">
        <i class="fas fa-search" aria-hidden="true"></i>
        <input
          v-model="q"
          type="search"
          placeholder="Search merch…"
          aria-label="Search merch"
        />
      </div>
      <div class="merch-pill">
        <span style="opacity:.7;font-size:12px;letter-spacing:.08em;text-transform:uppercase;">Sort</span>
        <select v-model="sort" aria-label="Sort merch">
          <option value="featured">Featured</option>
          <option value="low">Price: Low</option>
          <option value="high">Price: High</option>
          <option value="az">Name: A–Z</option>
        </select>
      </div>
    </div>

    <!-- Grid (Flask: merch-grid, merch-card) -->
    <div v-if="filteredItems.length" class="merch-grid">
      <div
        v-for="i in filteredItems"
        :key="i.id"
        class="merch-card"
        :class="{ 'sale-pending': isPurchased(i) }"
      >
        <div
          class="merch-media"
          @mouseenter="hoverBack[i.id] = !!i.image_url_back"
          @mouseleave="hoverBack[i.id] = false"
        >
          <img
            :src="(hoverBack[i.id] && i.image_url_back) ? i.image_url_back : (i.image_url || '/static/img/default-cover.jpg')"
            :alt="i.name || i.id"
            loading="lazy"
            decoding="async"
            :title="hoverBack[i.id] ? 'Back view' : 'Front view'"
            @error="onMerchImageError($event, i)"
          />
          <div v-if="i.image_url_back" class="image-toggle-hint">
            <i class="fas fa-sync-alt"></i>
            <span>Hover to see back</span>
          </div>
          <div v-if="isPurchased(i)" class="sale-pending-badge">
            <i class="fas fa-clock" aria-hidden="true"></i>
            <span>Sale Pending</span>
          </div>
        </div>
        <div class="merch-body">
          <div class="merch-top">
            <h3 class="merch-title">{{ i.name || i.id }}</h3>
            <div class="merch-price">
              <div class="usd">{{ i.price_usd != null ? '$' + (+i.price_usd).toFixed(2) : '—' }}</div>
              <div class="sub">USD</div>
            </div>
          </div>
          <div class="merch-chips">
            <span v-for="c in chipsFor(i)" :key="c" class="merch-chip">{{ c }}</span>
          </div>
          <div class="merch-actions">
            <input
              class="qty"
              type="number"
              min="1"
              max="1"
              value="1"
              :id="'qty_' + (i.id || '')"
              disabled
              aria-label="Quantity"
              title="One-of-a-kind item"
            />
            <a
              class="merch-cta"
              :class="{ disabled: isPurchased(i) }"
              href="#"
              @click.prevent="isPurchased(i) ? null : checkout(i)"
            >
              <span>{{ isPurchased(i) ? 'Sold' : 'Checkout' }}</span>
              <i :class="isPurchased(i) ? 'fas fa-lock' : 'fas fa-arrow-right'" aria-hidden="true"></i>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state (Flask: merch-empty) -->
    <div v-else-if="!loading" class="merch-empty">
      No merch items found yet. Add images to <code>static/merch/images/</code> and run
      <code>python manifest.py merch</code> to generate <code>data/merch.json</code>.
    </div>

    <!-- Loading skeletons -->
    <div v-else class="merch-grid">
      <div v-for="j in 6" :key="j" class="merch-card">
        <div class="merch-media skeleton" style="aspect-ratio:4/3"></div>
        <div class="merch-body">
          <div class="skeleton" style="height:14px;width:60%;margin-bottom:6px"></div>
          <div class="skeleton" style="height:12px;width:30%"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'

const items = ref([])
const purchasedItemIds = ref(new Set())
const loading = ref(true)
const q = ref('')
const sort = ref('featured')
const hoverBack = ref({})

function norm(s) {
  return String(s || '').toLowerCase()
}

function isMerch(i) {
  const k = norm(i && (i.kind || i.type || i.category))
  return !['theme', 'themes', 'subscription', 'subscriptions', 'membership', 'memberships'].includes(k)
}

const filteredItems = computed(() => {
  let out = Array.isArray(items.value) ? [...items.value] : []
  out = out.filter((i) => isMerch(i))
  const query = norm(q.value)
  if (query) out = out.filter((i) => norm(i.name || i.id).includes(query))
  if (sort.value === 'low') out.sort((a, b) => (+a.price_usd || 0) - (+b.price_usd || 0))
  else if (sort.value === 'high') out.sort((a, b) => (+b.price_usd || 0) - (+a.price_usd || 0))
  else if (sort.value === 'az') out.sort((a, b) => String(a.name || a.id || '').localeCompare(String(b.name || b.id || '')))
  return out
})

function isPurchased(i) {
  if (!i || !i.id) return false
  return purchasedItemIds.value.has(String(i.id))
}

function chipsFor(i) {
  const name = norm(i.name || i.id)
  const price = +i.price_usd || 0
  const chips = []
  if (name.includes('limited') || name.includes('drop')) chips.push('Limited Drop')
  if (name.includes('bundle')) chips.push('Bundle')
  if (price >= 50) chips.push('Collector')
  else chips.push('Supporter')
  return chips.slice(0, 2)
}

function checkout(i) {
  if (isPurchased(i)) return
  const id = encodeURIComponent(i.id || '')
  const title = encodeURIComponent(i.name || i.id || 'Merch')
  const amount = encodeURIComponent(i.price_usd ?? '')
  const qtyEl = document.getElementById('qty_' + (i.id || ''))
  const qty = encodeURIComponent((qtyEl && qtyEl.value) ? qtyEl.value : '1')
  window.location.assign(`/checkout?type=merch&item_id=${id}&qty=${qty}&amount=${amount}&title=${title}`)
}

const defaultCover = '/static/img/default-cover.jpg'
function onMerchImageError(event, item) {
  const el = event?.target
  if (!el || el.dataset.merchFallback) return
  el.dataset.merchFallback = '1'
  const back = hoverBack.value[item?.id] && item?.image_url_back
  if (back && el.src === item?.image_url_back) {
    el.src = item?.image_url || defaultCover
  } else {
    el.src = defaultCover
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await apiFetchCached('/api/merch')
    items.value = data.items || []
    purchasedItemIds.value = new Set((data.purchased_item_ids || []).map(String))
  } catch {
    items.value = []
    purchasedItemIds.value = new Set()
  }
  loading.value = false
})
</script>

<style scoped>
.merch-mobile-hero {
  display: none;
}

@media (max-width: 768px) {
  .merch-shell {
    padding-left: 0;
    padding-right: 0;
  }

  :deep(.content-header) {
    display: none !important;
  }

  .merch-mobile-hero {
    display: block;
    margin: 2px var(--mobile-gutter, 10px) 12px !important;
    padding: 22px 16px 16px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 28px;
    background:
      radial-gradient(circle at 16% 0%, rgba(244, 196, 48, 0.13), transparent 34%),
      radial-gradient(circle at 92% 18%, rgba(255, 0, 96, 0.09), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.014));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.09),
      0 18px 44px rgba(0, 0, 0, 0.22);
    backdrop-filter: blur(24px) saturate(145%);
    -webkit-backdrop-filter: blur(24px) saturate(145%);
  }

  .merch-mobile-hero-copy {
    min-width: 0;
  }

  .merch-mobile-eyebrow {
    display: block;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .merch-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
  }

  .merch-mobile-hero-copy p {
    margin: 8px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.3;
  }

  .merch-mobile-hero-icon {
    width: 58px;
    height: 58px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    color: #1a1400;
    background: linear-gradient(180deg, #ffd95e 0%, #f4c430 100%);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.42),
      0 16px 30px rgba(244, 196, 48, 0.28);
  }
}
</style>
