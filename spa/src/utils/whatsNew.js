export function makeWhatsNewSlug(item) {
  const title = String(item?.title || '').toLowerCase()
  const date = String(item?.date || '').toLowerCase()
  return `${title}-${date}`
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '')
}

export function getWhatsNewMonthPath(item) {
  if (!item?.year || !item?.month) return '/whats-new'
  return `/whats-new/${item.year}/${item.month}`
}

export function getWhatsNewDetailPath(item) {
  if (!item?.year || !item?.month || !item?.section) return getWhatsNewMonthPath(item)
  return `/whats-new/${item.year}/${item.month}/${item.section}/${item.slug || makeWhatsNewSlug(item)}`
}
