<template>
  <div class="wn-month">
    <section class="wn-mobile-month-hero" aria-label="Month update summary">
      <div>
        <span class="wn-mobile-eyebrow">Updates</span>
        <h1>{{ compactTitle }}</h1>
        <p>{{ monthUpdates.length }} update{{ monthUpdates.length === 1 ? '' : 's' }} this month</p>
      </div>
    </section>

    <div class="month-header-nav">
      <router-link to="/whats-new" class="back-link">
        <i class="fas fa-arrow-left"></i> Archive
      </router-link>
    </div>

    <div class="section-tabs">
      <button type="button" class="section-tab" :class="{ active: activeSection === 'all' }" @click="$emit('set-section', 'all')">
        All <span class="tab-badge" v-if="monthUpdates.length">{{ monthUpdates.length }}</span>
      </button>
      <button
        v-for="section in availableSections"
        :key="section.key"
        type="button"
        class="section-tab"
        :class="{ active: activeSection === section.key }"
        @click="$emit('set-section', section.key)"
      >
        {{ section.label }}
        <span class="tab-badge" v-if="section.count">{{ section.count }}</span>
      </button>
    </div>

    <div class="wn-feed">
      <div v-if="filteredUpdates.length === 0" class="wn-empty">
        <p>No updates found for this section.</p>
      </div>
      <template v-else>
        <article
          v-for="(update, idx) in filteredUpdates"
          :key="update.slug || idx"
          class="wn-card"
          :class="[update.section, { latest: idx === 0 }]"
          role="link"
          tabindex="0"
          @click="openDetail(update)"
          @keydown.enter.prevent="openDetail(update)"
          @keydown.space.prevent="openDetail(update)"
        >
          <div v-if="isLatest(update)" class="wn-card-badge new">Latest</div>
          <div v-if="getThumbnail(update)" class="wn-card-hero">
            <img :src="getThumbnail(update)" :alt="update.title" loading="lazy" @error="onImageError" />
          </div>
          <div class="wn-card-body">
            <div class="wn-card-header">
              <div>
                <h2>{{ update.title }}</h2>
                <div class="wn-meta">
                  <time class="wn-date">{{ formatDate(update.date) }}</time>
                  <span v-if="getSectionLabel(update)" class="wn-pill section" :class="`s-${update.section}`">{{ getSectionLabel(update) }}</span>
                </div>
              </div>
            </div>
            <p class="wn-body">{{ update.description }}</p>
            <div class="wn-card-footer">
              <router-link v-if="detailLinkFor(update)" :to="detailLinkFor(update)" class="wn-cta" @click.stop>
                <span>{{ getCtaText(update) }}</span>
              </router-link>
              <a v-else-if="update.link" :href="update.link" class="wn-cta" @click.stop>
                <span>{{ getCtaText(update) }}</span>
              </a>
            </div>
          </div>
        </article>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  activeSection: String,
  monthUpdates: { type: Array, default: () => [] },
  availableSections: { type: Array, default: () => [] },
  filteredUpdates: { type: Array, default: () => [] },
  getThumbnail: Function,
  getIcon: Function,
  formatDate: Function,
  getTypeLabel: Function,
  getSectionLabel: Function,
  getFeatureIcon: Function,
  getCtaIcon: Function,
  getCtaText: Function,
  detailLinkFor: Function,
})
defineEmits(['set-section'])

const router = useRouter()

const compactTitle = computed(() => {
  return props.title.replace(/^What's New\s+—\s+/i, '') || 'Updates'
})

function isLatest(update) {
  return props.monthUpdates.length > 0 && update === props.monthUpdates[0]
}

function openDetail(update) {
  const path = props.detailLinkFor?.(update)
  if (path) router.push(path)
}

function onImageError(event) {
  event.currentTarget.src = '/static/img/default-cover.jpg'
}
</script>

<style scoped>
.wn-month {
  padding-top: 0.5rem;
}

.wn-mobile-month-hero {
  display: none;
}

.month-header-nav {
  margin-bottom: 1.25rem;
}

.section-tabs {
  display: flex;
  gap: 0.75rem;
  margin: 0 0 2rem;
  flex-wrap: nowrap;
  justify-content: flex-start;
  overflow-x: auto;
  padding: 0 0 1rem;
  scrollbar-width: none;
}

.section-tabs::-webkit-scrollbar {
  display: none;
}

.section-tab {
  padding: 0.65rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.9rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  cursor: pointer;
  flex-shrink: 0;
}

.section-tab.active {
  background: rgba(255, 255, 255, 0.92);
  color: #050505;
  border-color: rgba(255, 255, 255, 0.92);
}

.tab-badge {
  min-width: 1.3rem;
  height: 1.3rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.74rem;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.12);
  color: inherit;
}

.section-tab.active .tab-badge {
  background: rgba(0, 0, 0, 0.12);
}

.wn-feed {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 860px;
  margin: 0 auto;
}

.wn-card {
  position: relative;
  background: rgba(18, 18, 20, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  overflow: hidden;
  padding: 0;
}

.wn-card-badge {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 2;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(86, 240, 140, 0.18);
  border: 1px solid rgba(86, 240, 140, 0.3);
  color: #56f08c;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.wn-card-hero {
  width: 100%;
  aspect-ratio: 1 / 1;
  max-height: 420px;
  overflow: hidden;
  background:
    radial-gradient(circle at 30% 20%, rgba(109, 220, 255, 0.12), transparent 35%),
    radial-gradient(circle at 75% 65%, rgba(255, 0, 96, 0.08), transparent 32%),
    rgba(255, 255, 255, 0.02);
}

.wn-card-hero img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
}

.wn-card-body {
  padding: 1.2rem 1.45rem 1.35rem;
}

.wn-card-header {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  margin-bottom: 0.75rem;
}

.wn-card-header h2 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1.2;
  color: rgba(255, 255, 255, 0.95);
}

.wn-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.wn-date {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.48);
}

.wn-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: rgba(255, 255, 255, 0.65);
}

.wn-pill.section.s-music { color: #ff4b9b; border-color: rgba(255, 75, 155, 0.25); background: rgba(255, 75, 155, 0.07); }
.wn-pill.section.s-videos { color: #6ddcff; border-color: rgba(109, 220, 255, 0.25); background: rgba(109, 220, 255, 0.07); }
.wn-pill.section.s-events { color: #56f08c; border-color: rgba(86, 240, 140, 0.25); background: rgba(86, 240, 140, 0.07); }
.wn-pill.section.s-platform { color: #a78bfa; border-color: rgba(167, 139, 250, 0.25); background: rgba(167, 139, 250, 0.07); }

.wn-body {
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.65;
  margin: 0 0 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wn-card:not(:has(.wn-card-hero)) {
  border-left-width: 3px;
}

.wn-card.music:not(:has(.wn-card-hero)) { border-left-color: rgba(255, 75, 155, 0.5); }
.wn-card.videos:not(:has(.wn-card-hero)) { border-left-color: rgba(109, 220, 255, 0.5); }
.wn-card.events:not(:has(.wn-card-hero)) { border-left-color: rgba(86, 240, 140, 0.5); }
.wn-card.platform:not(:has(.wn-card-hero)) { border-left-color: rgba(167, 139, 250, 0.5); }

.wn-card-footer {
  display: flex;
  justify-content: flex-start;
  margin-top: 0.25rem;
}

.wn-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  text-decoration: none;
  transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.wn-card.music .wn-cta {
  color: #ff4b9b;
  border-color: rgba(255, 75, 155, 0.2);
  background: rgba(255, 75, 155, 0.08);
}

.wn-card.videos .wn-cta {
  color: #6ddcff;
  border-color: rgba(109, 220, 255, 0.2);
  background: rgba(109, 220, 255, 0.08);
}

.wn-card.events .wn-cta {
  color: #56f08c;
  border-color: rgba(86, 240, 140, 0.2);
  background: rgba(86, 240, 140, 0.08);
}

.wn-card.platform .wn-cta {
  color: #a78bfa;
  border-color: rgba(167, 139, 250, 0.2);
  background: rgba(167, 139, 250, 0.08);
}

.wn-cta:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
}

.wn-cta:focus-visible,
.section-tab:focus-visible,
.back-link:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.9);
  outline-offset: 3px;
}

@media (max-width: 768px) {
  .wn-month {
    padding-top: 0;
  }

  .wn-mobile-month-hero {
    display: block;
    margin: 2px 0 12px;
    padding: 18px 16px 15px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 24px;
    background:
      radial-gradient(circle at 16% 0%, rgba(109, 220, 255, 0.1), transparent 34%),
      radial-gradient(circle at 92% 18%, rgba(255, 0, 96, 0.08), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.014));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.08),
      0 16px 34px rgba(0, 0, 0, 0.18);
  }

  .wn-mobile-eyebrow {
    display: block;
    margin-bottom: 7px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .wn-mobile-month-hero h1 {
    margin: 0;
    color: #fff;
    font-size: 30px;
    font-weight: 900;
    line-height: 0.98;
  }

  .wn-mobile-month-hero p {
    margin: 7px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.25;
  }

  .month-header-nav {
    margin: 0 0 0.75rem;
  }

  .back-link {
    min-height: 34px;
    padding: 0 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.07);
    color: rgba(255, 255, 255, 0.74);
    font-size: 0.78rem;
    font-weight: 800;
  }

  .section-tabs {
    position: sticky;
    top: 0;
    z-index: 20;
    gap: 0.5rem;
    margin: 0 calc(var(--mobile-gutter, 10px) * -1) 0.85rem;
    padding: 0 var(--mobile-gutter, 10px) 0.9rem;
    background: linear-gradient(180deg, rgba(12, 12, 14, 0.98), rgba(12, 12, 14, 0.9) 72%, rgba(12, 12, 14, 0.58));
    backdrop-filter: blur(18px) saturate(145%);
    -webkit-backdrop-filter: blur(18px) saturate(145%);
  }

  .section-tab {
    width: auto !important;
    flex: 0 0 auto;
    min-height: 36px;
    padding: 0 0.85rem;
    font-size: 0.78rem;
    border-color: rgba(255, 255, 255, 0.075);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.016));
  }

  .tab-badge {
    min-width: 1.15rem;
    height: 1.15rem;
    font-size: 0.68rem;
  }

  .wn-feed {
    gap: 10px;
    max-width: none;
  }

  .wn-card {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr) 34px;
    align-items: center;
    gap: 10px;
    min-height: 64px;
    padding: 8px 8px 8px 10px;
    border-radius: 18px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.016));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.07),
      0 10px 22px rgba(0, 0, 0, 0.14);
    overflow: hidden;
    cursor: pointer;
  }

  .wn-card-badge {
    top: 6px;
    right: 42px;
    padding: 2px 6px;
    font-size: 0.58rem;
  }

  .wn-card.latest {
    border-color: rgba(86, 240, 140, 0.14);
    padding-top: 12px;
    row-gap: 8px;
  }

  .wn-card.latest .wn-card-badge {
    position: static;
    grid-column: 1 / -1;
    grid-row: 1;
    justify-self: start;
    align-self: start;
    width: max-content;
    margin: 0;
  }

  .wn-card.latest .wn-card-hero,
  .wn-card.latest .wn-card-header {
    grid-row: 2;
  }

  .wn-card-hero {
    grid-column: 1;
    grid-row: 1;
    width: 48px;
    height: 48px;
    margin: 0;
    aspect-ratio: 1;
    border: 0;
    border-radius: 10px;
    box-shadow: 0 10px 18px rgba(0, 0, 0, 0.24);
  }

  .wn-card-hero img {
    object-fit: cover;
  }

  .wn-card-body {
    display: contents;
  }

  .wn-card-header {
    grid-column: 1 / 3;
    grid-row: 1;
    min-width: 0;
    align-items: center;
    gap: 10px;
    margin: 0;
  }

  .wn-card:has(.wn-card-hero) .wn-card-header {
    grid-column: 2 / 3;
  }

  .wn-card-header > div:last-child {
    min-width: 0;
  }

  .wn-card-header h2 {
    margin: 0 0 5px;
    color: rgba(255, 255, 255, 0.94);
    font-size: 0.92rem;
    font-weight: 850;
    line-height: 1.12;
    letter-spacing: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .wn-meta {
    gap: 7px;
    flex-wrap: nowrap;
    overflow: hidden;
  }

  .wn-date {
    flex-shrink: 0;
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.46);
  }

  .wn-pill {
    max-width: none;
    padding: 1px 8px;
    font-size: 0.6rem;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .wn-pill:not(.section) {
    display: none;
  }


  .wn-body {
    grid-column: 2 / 3;
    grid-row: 3;
    margin: 0;
    color: rgba(255, 255, 255, 0.54);
    font-size: 0.74rem;
    line-height: 1.25;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .wn-card:not(:has(.wn-card-hero)) .wn-body {
    grid-column: 1 / 3;
    grid-row: 2;
  }

  .wn-card-footer {
    display: contents;
  }

  .wn-cta {
    grid-column: 3;
    grid-row: 1 / -1;
    align-self: center;
    justify-self: end;
    width: 34px;
    height: 34px;
    min-width: 34px;
    margin: 0;
    padding: 0;
    border-radius: 999px;
    justify-content: center;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.11);
    color: rgba(255, 255, 255, 0.86);
    box-shadow: none;
  }

  .wn-card.latest .wn-cta {
    align-self: end;
  }

  .wn-card.music .wn-cta { color: #ff4b9b; }
  .wn-card.videos .wn-cta { color: #6ddcff; }
  .wn-card.events .wn-cta { color: #56f08c; }
  .wn-card.platform .wn-cta { color: #a78bfa; }

  .wn-cta span {
    display: none;
  }

  .wn-cta:hover {
    transform: none;
    box-shadow: none;
  }
}
</style>
