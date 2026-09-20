<template>
  <div class="sub-menu-filter" :class="{ 'has-toolbar': hasToolbar }">
    <div class="sub-menu-filter-glass">
      <!-- Search first: primary action -->
      <div v-if="showSearch" class="sub-menu-filter-search">
        <i class="fas fa-search" aria-hidden="true"></i>
        <input
          :value="searchQuery"
          type="search"
          class="sub-menu-filter-search-input"
          :placeholder="searchPlaceholder"
          :aria-label="searchPlaceholder"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
          enterkeyhint="search"
          @input="$emit('update:searchQuery', ($event.target).value)"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="sub-menu-filter-search-clear"
          aria-label="Clear search"
          @click="$emit('update:searchQuery', '')"
        >
          <i class="fas fa-times" aria-hidden="true"></i>
        </button>
      </div>

      <!-- Filter dropdown + view toggle -->
      <div v-show="filters.length > 0" class="filter-main-controls">
        <select
          :value="modelValue"
          class="sub-menu-filter-sort main-filter"
          :aria-label="filterLabel"
          @change="$emit('update:modelValue', ($event.target).value)"
        >
          <option :value="allValue">{{ filterAllLabel || 'All Artists' }}</option>
          <option v-for="item in filters" :key="String(item.value)" :value="item.value">
            {{ item.label }}
          </option>
        </select>

        <div v-if="showViewToggle" class="sub-menu-filter-view">
          <button
            type="button"
            class="sub-menu-filter-view-btn"
            :class="{ active: viewMode === 'grid' }"
            aria-label="Grid view"
            @click="$emit('update:viewMode', 'grid')"
          >
            <i class="fas fa-th" aria-hidden="true"></i>
          </button>
          <button
            type="button"
            class="sub-menu-filter-view-btn"
            :class="{ active: viewMode === 'list' }"
            aria-label="List view"
            @click="$emit('update:viewMode', 'list')"
          >
            <i class="fas fa-list" aria-hidden="true"></i>
          </button>
        </div>
      </div>

      <select
        v-if="sortOptions && sortOptions.length"
        :value="sortBy"
        class="sub-menu-filter-sort"
        :aria-label="sortLabel"
        @change="$emit('update:sortBy', ($event.target).value)"
      >
        <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <select
        v-if="albums && albums.length"
        :value="selectedAlbum"
        class="sub-menu-filter-sort"
        aria-label="Filter by Album"
        @change="$emit('update:selectedAlbum', ($event.target).value)"
      >
        <option value="">All Albums</option>
        <option v-for="alb in albums" :key="alb.value" :value="alb.value">{{ alb.label }}</option>
      </select>

      <button
        v-if="showFavoritesToggle"
        type="button"
        class="sub-menu-filter-view-btn"
        :class="{ active: favoritesOnly }"
        title="Show Favorites Only"
        aria-label="Top Favorites Only"
        @click="$emit('update:favoritesOnly', !favoritesOnly)"
      >
        <i :class="favoritesOnly ? 'fas fa-heart' : 'far fa-heart'" aria-hidden="true"></i>
      </button>

      <slot name="toolbar-right"></slot>

      <button
        v-if="actionLabel || $slots.action"
        type="button"
        class="sub-menu-filter-action"
        @click="$emit('action')"
      >
        <slot name="action">
          <i v-if="actionIcon" :class="actionIcon" aria-hidden="true"></i>
          <span>{{ actionLabel }}</span>
        </slot>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Currently selected filter value (e.g. '' for All or artist name) */
  modelValue: { type: [String, Number], default: '' },
  /** Aria-label for the main filter dropdown */
  filterLabel: { type: String, default: 'Filter' },
  /** List of { value, label, image? } for filter chips */
  filters: { type: Array, default: () => [] },
  /** Value that means "all" (e.g. '') */
  allValue: { type: [String, Number], default: '' },
  /** Label for the "All" chip */
  filterAllLabel: { type: String, default: 'All' },
  /** Show search input */
  showSearch: { type: Boolean, default: false },
  searchPlaceholder: { type: String, default: 'Search…' },
  searchQuery: { type: String, default: '' },
  /** Sort dropdown: [{ value, label }] */
  sortOptions: { type: Array, default: () => [] },
  sortLabel: { type: String, default: 'Sort' },
  sortBy: { type: String, default: '' },
  /** Show grid/list toggle */
  showViewToggle: { type: Boolean, default: false },
  viewMode: { type: String, default: 'list' },
  /** Primary action button */
  actionLabel: { type: String, default: '' },
  actionIcon: { type: String, default: '' },
  /** Favorites Toggle */
  showFavoritesToggle: { type: Boolean, default: false },
  favoritesOnly: { type: Boolean, default: false },
  /** Album Filter */
  albums: { type: Array, default: () => [] },
  selectedAlbum: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'update:searchQuery', 'update:sortBy', 'update:viewMode', 'update:favoritesOnly', 'update:selectedAlbum', 'action'])

const selectedValue = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const hasToolbar = computed(
  () =>
    props.showSearch ||
    (props.sortOptions && props.sortOptions.length) ||
    props.showViewToggle ||
    props.actionLabel ||
    (props.actionIcon && !props.actionLabel)
)

function select(value) {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.sub-menu-filter {
  width: 100%;
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .sub-menu-filter {
    position: sticky;
    top: 0;
    z-index: 100;
    margin: 0 -16px 12px;
    width: calc(100% + 32px);
  }

  .sub-menu-filter-glass {
    border-radius: 0;
    border-left: none;
    border-right: none;
    background: rgba(10, 10, 15, 0.7);
    padding: 10px 16px;
  }
}

.sub-menu-filter-glass {
  background: rgba(0, 0, 0, 0.14);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 10px 12px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-main-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

/* Make the main artist filter prominent */
.sub-menu-filter-sort.main-filter {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: #fff;
  font-weight: 600;
  padding: 7px 12px;
  flex: 1;
  min-width: 140px;
  max-width: 200px;
  transition: all 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='white' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 32px;
}

.sub-menu-filter-sort.main-filter:hover {
  background-color: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.sub-menu-filter-sort.main-filter:focus {
  border-color: var(--accent-primary, #6ddcff);
  background-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 0 0 3px rgba(109, 220, 255, 0.15);
  outline: none;
}

/* Toolbar items */
.sub-menu-filter-search {
  flex: 2;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.sub-menu-filter-search:focus-within {
  border-color: var(--accent-primary, #6ddcff);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(109, 220, 255, 0.15);
}

.sub-menu-filter-search i {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.sub-menu-filter-search-input {
  flex: 1;
  min-width: 0;
  background: none;
  border: none;
  outline: none;
  color: #f8fafc;
  font-size: 14px;
}

.sub-menu-filter-search-input::placeholder {
  color: rgba(255, 255, 255, 0.45);
}

.sub-menu-filter-search-clear {
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  font-size: 13px;
  flex-shrink: 0;
}

.sub-menu-filter-search-clear:hover {
  color: rgba(255, 255, 255, 0.9);
}

.sub-menu-filter-sort {
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  cursor: pointer;
  min-width: 0;
  flex-shrink: 0;
  appearance: none;
  transition: all 0.2s ease;
}

.sub-menu-filter-view {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.sub-menu-filter-view-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-menu-filter-view-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.95);
  border-color: rgba(255, 255, 255, 0.2);
}

.sub-menu-filter-view-btn.active {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.sub-menu-filter-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.sub-menu-filter-action:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .sub-menu-filter-glass {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 12px;
  }

  .sub-menu-filter-search {
    width: 100%;
    order: 1;
    min-width: 0;
  }

  .filter-main-controls {
    width: 100%;
    order: 2;
  }

  .sub-menu-filter-sort.main-filter {
    flex: 1;
    max-width: none;
    min-width: 0;
  }

  .sub-menu-filter-action {
    width: 100%;
    order: 3;
    padding: 10px;
  }

  .sub-menu-filter-sort:not(.main-filter) {
    width: 100%;
    order: 4;
  }

  /* Prevent iOS viewport zoom on focus (requires font-size >= 16px) */
  .sub-menu-filter-search-input,
  .sub-menu-filter-sort {
    font-size: 16px;
  }
}
</style>
