const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 375, height: 812 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  await page.goto('http://localhost:5001/search', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Screenshot 1: initial state (autofocused input)
  await page.screenshot({ path: '/tmp/search_initial.png', fullPage: false });

  // Check: is the input focused?
  const inputFocused = await page.evaluate(() => {
    const input = document.querySelector('.search-input');
    return document.activeElement === input;
  });
  console.log('Input autofocused:', inputFocused);

  // Check outline/border on the input
  const inputStyles = await page.evaluate(() => {
    const input = document.querySelector('.search-input');
    const wrap = document.querySelector('.search-input-wrap');
    const cs = window.getComputedStyle(input);
    const ws = window.getComputedStyle(wrap);
    return {
      inputOutline: cs.outline,
      inputOutlineColor: cs.outlineColor,
      wrapBorder: ws.border,
      wrapBorderColor: ws.borderColor
    };
  });
  console.log('Input styles:', JSON.stringify(inputStyles, null, 2));

  // Check nav links layout
  const navStyles = await page.evaluate(() => {
    const nav = document.querySelector('.search-sidebar-nav');
    const links = document.querySelectorAll('.search-nav-link');
    if (!nav) return { error: 'no nav found' };
    const cs = window.getComputedStyle(nav);
    const firstLink = links[0];
    const lastLink = links[links.length - 1];
    return {
      navFlexDirection: cs.flexDirection,
      navOverflowX: cs.overflowX,
      linkCount: links.length,
      firstLinkTop: firstLink?.getBoundingClientRect().top,
      lastLinkTop: lastLink?.getBoundingClientRect().top,
      firstLinkLeft: firstLink?.getBoundingClientRect().left,
      lastLinkRight: lastLink?.getBoundingClientRect().right,
    };
  });
  console.log('Nav styles:', JSON.stringify(navStyles, null, 2));

  // Check gap between chips and content
  const gap = await page.evaluate(() => {
    const sidebar = document.querySelector('.search-sidebar');
    const main = document.querySelector('.search-main');
    if (!sidebar || !main) return { error: 'missing elements' };
    const sidebarBottom = sidebar.getBoundingClientRect().bottom;
    const mainTop = main.getBoundingClientRect().top;
    const firstSection = document.querySelector('.search-section');
    const firstSectionTop = firstSection?.getBoundingClientRect().top;
    return {
      sidebarBottom,
      mainTop,
      gap: mainTop - sidebarBottom,
      firstSectionTop,
      gapToContent: firstSectionTop - sidebarBottom
    };
  });
  console.log('Gap analysis:', JSON.stringify(gap, null, 2));

  // Click elsewhere to focus the input manually and screenshot
  await page.click('.search-input');
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/tmp/search_focused.png', fullPage: false });
  console.log('Focused screenshot saved');

  // Scroll to see full layout
  await page.screenshot({ path: '/tmp/search_full.png', fullPage: true });
  console.log('Full page screenshot saved');

  await browser.close();
})();
