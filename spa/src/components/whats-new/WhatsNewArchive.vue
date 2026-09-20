<template>
  <div class="wn-archive">
    <section class="wn-mobile-archive-hero" aria-label="What's New archive summary">
      <div class="wn-mobile-hero-copy">
        <span class="wn-mobile-eyebrow">Archive</span>
        <h1>What's New</h1>
        <p>{{ totalUpdates }} update{{ totalUpdates === 1 ? '' : 's' }} across {{ archive.length }} month{{ archive.length === 1 ? '' : 's' }}</p>
      </div>
      <router-link
        v-if="archive.length"
        :to="`/whats-new/${archive[0].year}/${archive[0].month}`"
        class="wn-mobile-hero-action"
        aria-label="Open latest month"
      >
        <i class="fas fa-arrow-right" aria-hidden="true"></i>
      </router-link>
    </section>

    <section v-if="latestUpdates.length" class="wn-mobile-latest" aria-label="Latest updates">
      <div class="wn-mobile-section-header">
        <span>Latest</span>
        <router-link v-if="archive.length" :to="`/whats-new/${archive[0].year}/${archive[0].month}`">View month</router-link>
      </div>
      <div class="wn-latest-scroll">
        <router-link
          v-for="(update, index) in latestUpdates"
          :key="update.slug || `${update.date}-${update.title}-${index}`"
          :to="detailLinkFor(update)"
          class="wn-latest-card"
        >
          <span v-if="getThumbnail(update)" class="wn-latest-thumb">
            <img :src="getThumbnail(update)" :alt="update.title" loading="lazy" @error="onImageError" />
          </span>
          <span v-else class="wn-latest-icon" :class="update.section">
            <i :class="sectionIcon(update.section)" aria-hidden="true"></i>
          </span>
          <span class="wn-latest-copy">
            <span class="wn-latest-title">{{ update.title }}</span>
            <span class="wn-latest-meta">
              {{ getSectionLabel(update) || 'Update' }}
              <span v-if="formatDate(update.date)">• {{ formatDate(update.date) }}</span>
            </span>
          </span>
        </router-link>
      </div>
    </section>

    <div class="wn-mobile-section-header months-heading">
      <span>Browse by month</span>
    </div>

    <div class="months-grid">
      <router-link
        v-for="month in archive"
        :key="`${month.year}-${month.month}`"
        :to="`/whats-new/${month.year}/${month.month}`"
        class="month-card"
      >
        <div class="month-card-header">
          <h3>{{ month.month_name }}</h3>
          <span class="month-year">{{ month.year }}</span>
        </div>
        <div v-if="month.section_keys?.length" class="month-section-hints" aria-label="Update sections">
          <span
            v-for="section in month.section_keys"
            :key="section"
            class="month-section-hint"
            :class="section"
            :title="`${sectionLabel(section)} updates`"
          >
            <i :class="sectionIcon(section)" aria-hidden="true"></i>
          </span>
        </div>
        <div class="month-card-content">
          <span v-if="isLatestMonth(month)" class="month-latest-pill">Latest</span>
          <span class="month-items-count">{{ month.total_items }} update{{ month.total_items !== 1 ? 's' : '' }}</span>
        </div>
        <div class="month-card-arrow">
          <i class="fas fa-chevron-right"></i>
        </div>
      </router-link>
    </div>

    <section class="wn-feature-section" aria-label="Events">
      <router-link to="/events" class="wn-feature-link">
        <span class="wn-feature-link-icon">
          <i class="fas fa-calendar-alt" aria-hidden="true"></i>
        </span>
        <span class="wn-feature-link-copy">
          <span class="wn-feature-link-title">Events</span>
          <span class="wn-feature-link-desc">Browse upcoming shows &amp; live events</span>
        </span>
        <i class="fas fa-chevron-right wn-feature-link-arrow" aria-hidden="true"></i>
      </router-link>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  archive: { type: Array, default: () => [] },
  latestUpdates: { type: Array, default: () => [] },
  getThumbnail: { type: Function, default: () => '' },
  formatDate: { type: Function, default: () => '' },
  getSectionLabel: { type: Function, default: () => '' },
  detailLinkFor: { type: Function, default: () => '/whats-new' },
})

const totalUpdates = computed(() =>
  props.archive.reduce((sum, month) => sum + Number(month.total_items || 0), 0)
)

function sectionIcon(section) {
  if (section === 'music') return 'fas fa-music'
  if (section === 'videos') return 'fas fa-play'
  if (section === 'artists') return 'fas fa-user'
  if (section === 'events') return 'fas fa-calendar'
  if (section === 'merch') return 'fas fa-shopping-bag'
  return 'fas fa-cog'
}

function sectionLabel(section) {
  if (section === 'music') return 'Music'
  if (section === 'videos') return 'Video'
  if (section === 'artists') return 'Artist'
  if (section === 'events') return 'Event'
  if (section === 'merch') return 'Merch'
  return 'Platform'
}

function isLatestMonth(month) {
  const latest = props.archive[0]
  return latest && month.year === latest.year && month.month === latest.month
}

function onImageError(event) {
  event.currentTarget.src = '/static/img/default-cover.jpg'
}
</script>

<style scoped>
.wn-mobile-archive-hero,
.wn-mobile-latest,
.wn-mobile-section-header {
  display: none;
}

.months-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.month-card {
  display: flex;
  flex-direction: column;
  background: rgba(20, 20, 20, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.month-card-icon {
  display: none;
}

.month-latest-pill {
  display: none;
}

.month-section-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.6rem;
}

.month-section-hint {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.055);
  color: rgba(255, 255, 255, 0.58);
  font-size: 9px;
}

.month-section-hint.music { color: #ff4b9b; background: rgba(255, 75, 155, 0.09); }
.month-section-hint.videos { color: #6ddcff; background: rgba(109, 220, 255, 0.09); }
.month-section-hint.events { color: #56f08c; background: rgba(86, 240, 140, 0.09); }
.month-section-hint.platform { color: #a78bfa; background: rgba(167, 139, 250, 0.09); }

.month-card:hover {
  background: rgba(30, 30, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.month-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.month-card-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.month-year {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.month-items-count {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.month-card-arrow {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  color: rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
}

.month-card:hover .month-card-arrow {
  color: #fff;
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .wn-archive {
    padding-bottom: 8px;
  }

  .wn-mobile-archive-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 50px;
    align-items: end;
    gap: 14px;
    margin: 2px 0 12px;
    padding: 22px 16px 16px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 28px;
    background:
      radial-gradient(circle at 16% 0%, rgba(109, 220, 255, 0.11), transparent 34%),
      radial-gradient(circle at 92% 18%, rgba(255, 0, 96, 0.09), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.014));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.09),
      0 18px 44px rgba(0, 0, 0, 0.22);
    backdrop-filter: blur(24px) saturate(145%);
    -webkit-backdrop-filter: blur(24px) saturate(145%);
  }

  .wn-mobile-hero-copy {
    min-width: 0;
  }

  .wn-mobile-eyebrow {
    display: block;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .wn-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 34px;
    font-weight: 900;
    line-height: 0.98;
  }

  .wn-mobile-hero-copy p {
    margin: 8px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.3;
  }

  .wn-mobile-hero-action {
    width: 50px;
    height: 50px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #031108;
    text-decoration: none;
    background: linear-gradient(180deg, #56f08c 0%, #1ed760 100%);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.42),
      0 16px 30px rgba(30, 215, 96, 0.24);
  }

  .wn-mobile-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2px;
    margin: 0 0 8px;
    color: rgba(255, 255, 255, 0.92);
    font-size: 13px;
    font-weight: 850;
  }

  .wn-mobile-section-header a {
    color: rgba(109, 220, 255, 0.82);
    font-size: 12px;
    font-weight: 800;
    text-decoration: none;
  }

  .wn-mobile-latest {
    display: block;
    margin-bottom: 18px;
  }

  .wn-latest-scroll {
    display: flex;
    gap: 8px;
    margin: 0 -10px;
    padding: 0 10px 2px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .wn-latest-scroll::-webkit-scrollbar {
    display: none;
  }

  .wn-latest-card {
    flex: 0 0 238px;
    min-height: 82px;
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr);
    gap: 10px;
    align-items: center;
    padding: 10px;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.065);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.016));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
    color: inherit;
    text-decoration: none;
  }

  .wn-latest-icon,
  .month-card-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    color: #6ddcff;
    background: rgba(109, 220, 255, 0.09);
  }

  .wn-latest-icon {
    width: 42px;
    height: 42px;
  }

  .wn-latest-thumb {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 18px rgba(0, 0, 0, 0.22);
  }

  .wn-latest-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .wn-latest-icon.music { color: #ff4b9b; background: rgba(255, 75, 155, 0.09); }
  .wn-latest-icon.videos { color: #6ddcff; background: rgba(109, 220, 255, 0.09); }
  .wn-latest-icon.events { color: #56f08c; background: rgba(86, 240, 140, 0.09); }

  .wn-latest-copy {
    min-width: 0;
    display: grid;
    gap: 5px;
  }

  .wn-latest-title {
    color: rgba(255, 255, 255, 0.92);
    font-size: 13px;
    font-weight: 850;
    line-height: 1.14;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .wn-latest-meta {
    color: rgba(255, 255, 255, 0.48);
    font-size: 11px;
    font-weight: 650;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .months-heading {
    margin-bottom: 8px;
  }

  .months-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .month-card {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr) auto 28px;
    align-items: center;
    gap: 10px;
    min-height: 62px;
    padding: 9px 8px 9px 10px;
    border-radius: 18px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.016));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.07),
      0 10px 22px rgba(0, 0, 0, 0.14);
  }

  .month-card:hover {
    transform: none;
  }

  .month-card-icon {
    width: 42px;
    height: 42px;
    color: #ff4b9b;
    background: rgba(255, 75, 155, 0.09);
  }

  .month-card-header {
    min-width: 0;
    display: grid;
    gap: 3px;
    margin: 0;
  }

  .month-section-hints {
    grid-column: 2 / 3;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
    margin-top: 24px;
  }

  .month-section-hint {
    width: 18px;
    height: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.055);
    color: rgba(255, 255, 255, 0.58);
    font-size: 9px;
  }

  .month-section-hint.music { color: #ff4b9b; background: rgba(255, 75, 155, 0.09); }
  .month-section-hint.videos { color: #6ddcff; background: rgba(109, 220, 255, 0.09); }
  .month-section-hint.events { color: #56f08c; background: rgba(86, 240, 140, 0.09); }
  .month-section-hint.platform { color: #a78bfa; background: rgba(167, 139, 250, 0.09); }

  .month-card-header h3 {
    color: rgba(255, 255, 255, 0.94);
    font-size: 18px;
    font-weight: 850;
    line-height: 1.05;
    overflow: visible;
    text-overflow: unset;
    white-space: normal;
    word-break: keep-all;
  }

  .month-year,
  .month-items-count {
    font-size: 12px;
    line-height: 1;
  }

  .month-card-content {
    justify-self: end;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .month-items-count {
    color: rgba(255, 255, 255, 0.54);
    white-space: nowrap;
  }

  .month-latest-pill {
    display: inline-flex;
    padding: 2px 7px;
    border-radius: 999px;
    background: rgba(86, 240, 140, 0.11);
    color: rgba(86, 240, 140, 0.9);
    font-size: 10px;
    font-weight: 850;
    line-height: 1.3;
  }

  .month-card-arrow {
    position: static;
    justify-self: center;
    color: rgba(255, 75, 155, 0.92);
  }
}

.wn-feature-section {
  margin-top: 2rem;
}

.wn-feature-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(86, 240, 140, 0.06);
  border: 1px solid rgba(86, 240, 140, 0.18);
  border-radius: 14px;
  padding: 1.1rem 1.25rem;
  text-decoration: none;
  color: inherit;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.wn-feature-link:hover {
  background: rgba(86, 240, 140, 0.11);
  border-color: rgba(86, 240, 140, 0.35);
  transform: translateY(-2px);
}

.wn-feature-link-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(86, 240, 140, 0.12);
  color: #56f08c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.wn-feature-link-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.wn-feature-link-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
}

.wn-feature-link-desc {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.wn-feature-link-arrow {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.8rem;
  flex-shrink: 0;
}
</style>
