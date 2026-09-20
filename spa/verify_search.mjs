import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 375, height: 812 },
  deviceScaleFactor: 2
});
const page = await context.newPage();

await page.goto('http://localhost:5001/search', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);

await page.screenshot({ path: '/tmp/search_initial.png' });

const inputStyles = await page.evaluate(() => {
  const input = document.querySelector('.search-input');
  const wrap = document.querySelector('.search-input-wrap');
  const cs = window.getComputedStyle(input);
  const ws = window.getComputedStyle(wrap);
  return {
    inputOutline: cs.outline,
    inputOutlineColor: cs.outlineColor,
    wrapBorderColor: ws.borderColor,
    wrapBackground: ws.background,
  };
});
console.log('Input styles:', JSON.stringify(inputStyles, null, 2));

const navInfo = await page.evaluate(() => {
  const nav = document.querySelector('.search-sidebar-nav');
  const links = [...document.querySelectorAll('.search-nav-link')];
  if (!nav) return { error: 'no nav' };
  const cs = window.getComputedStyle(nav);
  const rects = links.map(l => ({ top: l.getBoundingClientRect().top, left: l.getBoundingClientRect().left }));
  return {
    flexDirection: cs.flexDirection,
    overflowX: cs.overflowX,
    linkRects: rects
  };
});
console.log('Nav:', JSON.stringify(navInfo, null, 2));

const gapInfo = await page.evaluate(() => {
  const sidebar = document.querySelector('.search-sidebar');
  const firstSection = document.querySelector('.search-results .search-section');
  if (!sidebar || !firstSection) return { error: 'missing' };
  return {
    sidebarBottom: Math.round(sidebar.getBoundingClientRect().bottom),
    firstSectionTop: Math.round(firstSection.getBoundingClientRect().top),
    gap: Math.round(firstSection.getBoundingClientRect().top - sidebar.getBoundingClientRect().bottom)
  };
});
console.log('Gap:', JSON.stringify(gapInfo, null, 2));

await page.click('.search-input');
await page.waitForTimeout(300);
await page.screenshot({ path: '/tmp/search_focused.png' });

await browser.close();
console.log('Done. Screenshots at /tmp/search_initial.png and /tmp/search_focused.png');
