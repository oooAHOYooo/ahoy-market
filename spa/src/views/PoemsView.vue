<template>
  <div class="poems-page">
    <ContentHeader
      kicker="Poets & Friends"
      title="Poems"
      subtitle="Original poems from our community of poets."
    />

    <section class="poems-list-section">
      <div v-if="loading" class="poems-loading">
        <i class="fas fa-spinner fa-spin"></i>
      </div>

      <div v-else-if="allPoems.length === 0" class="poems-empty">
        <i class="fas fa-feather-alt"></i>
        <p>No poems yet. Check back soon.</p>
      </div>

      <div v-else>
        <div class="poems-controls">
          <div class="control-group">
            <label for="poet-filter">Poet</label>
            <select v-model="selectedPoet" id="poet-filter">
              <option value="">All Poets</option>
              <option v-for="poet in uniquePoets" :key="poet" :value="poet">
                {{ poet }}
              </option>
            </select>
          </div>
          <div class="control-group">
            <label for="sort-by">Sort</label>
            <select v-model="sortBy" id="sort-by">
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
              <option value="alphabetical">A–Z</option>
            </select>
          </div>
        </div>

        <div class="poems-grid">
          <router-link
            v-for="poem in filteredPoems"
            :key="poem.poem_id"
            :to="`/poems/${poem.poem_id}`"
            class="poem-card"
          >
            <div class="poem-card-title">{{ poem.title }}</div>
            <div class="poem-card-poet">{{ poem.poet_name }}</div>
            <div v-if="poem.note" class="poem-card-note">{{ poem.note }}</div>
            <div class="poem-card-preview">{{ firstLines(poem.body_text) }}</div>
            <div class="poem-card-meta">
              <span class="poem-card-date">{{ formatDate(poem.published_at) }}</span>
              <span class="poem-card-read">Read →</span>
            </div>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import ContentHeader from '../components/ContentHeader.vue'

const allPoems = ref([])
const loading = ref(true)
const selectedPoet = ref('')
const sortBy = ref('newest')

const uniquePoets = computed(() => {
  const poets = new Set(allPoems.value.map(p => p.poet_name))
  return Array.from(poets).sort()
})

const filteredPoems = computed(() => {
  let result = allPoems.value

  if (selectedPoet.value) {
    result = result.filter(p => p.poet_name === selectedPoet.value)
  }

  if (sortBy.value === 'newest') {
    result.sort((a, b) => new Date(b.published_at) - new Date(a.published_at))
  } else if (sortBy.value === 'oldest') {
    result.sort((a, b) => new Date(a.published_at) - new Date(b.published_at))
  } else if (sortBy.value === 'alphabetical') {
    result.sort((a, b) => a.title.localeCompare(b.title))
  }

  return result
})

onMounted(async () => {
  try {
    const res = await fetch('/api/poems')
    const data = await res.json()
    allPoems.value = data.poems || []
  } catch (e) {
    console.error('Failed to load poems', e)
  } finally {
    loading.value = false
  }
})

function firstLines(text, n = 3) {
  if (!text) return ''
  return text.split('\n').filter(l => l.trim()).slice(0, n).join(' / ')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.poems-page {
  min-height: 100vh;
}

.poems-list-section {
  padding: 24px var(--mobile-gutter, 16px) 120px;
  max-width: 720px;
  margin: 0 auto;
}

.poems-loading,
.poems-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--color-text-muted, #888);
  font-size: 15px;
}

.poems-loading i,
.poems-empty i {
  font-size: 28px;
  opacity: 0.4;
}

.poems-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-muted, #888);
}

.control-group select {
  padding: 8px 12px;
  background: var(--color-surface, rgba(255,255,255,0.04));
  border: 1px solid var(--color-border, rgba(255,255,255,0.08));
  border-radius: 8px;
  color: var(--color-text, #fff);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.control-group select:hover {
  background: var(--color-surface-hover, rgba(255,255,255,0.08));
  border-color: var(--color-border-hover, rgba(255,255,255,0.16));
}

.control-group select:focus {
  outline: none;
  border-color: var(--color-accent, #7eb8ff);
}

.poems-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.poem-card {
  display: block;
  padding: 24px 28px;
  background: var(--color-surface, rgba(255,255,255,0.04));
  border: 1px solid var(--color-border, rgba(255,255,255,0.08));
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: background 0.2s, border-color 0.2s;
}

.poem-card:hover {
  background: var(--color-surface-hover, rgba(255,255,255,0.08));
  border-color: var(--color-border-hover, rgba(255,255,255,0.16));
}

.poem-card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--color-text, #fff);
}

.poem-card-poet {
  font-size: 13px;
  color: var(--color-text-muted, #888);
  margin-bottom: 8px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.poem-card-note {
  font-size: 13px;
  color: var(--color-text-secondary, #bbb);
  margin-bottom: 12px;
  font-style: italic;
}

.poem-card-preview {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary, #bbb);
  font-style: italic;
  margin-bottom: 16px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.poem-card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.poem-card-date {
  color: var(--color-text-muted, #888);
}

.poem-card-read {
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-accent, #7eb8ff);
}
</style>
