#!/usr/bin/env node
// Local-only Playwright QA: Vite preview is bound to loopback and is stopped on exit.
import { spawn } from 'node:child_process'
import { mkdir } from 'node:fs/promises'
import { chromium } from '../../spa/node_modules/playwright/index.mjs'

const [outputDir, routesJson] = process.argv.slice(2)
const routes = JSON.parse(routesJson || '[]')
await mkdir(outputDir, { recursive: true })

const preview = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4179', '--strictPort'], {
  cwd: new URL('../../spa/', import.meta.url), stdio: ['ignore', 'pipe', 'pipe'],
})
let startup = ''
preview.stdout.on('data', chunk => { startup += chunk })
preview.stderr.on('data', chunk => { startup += chunk })
const stop = () => { if (!preview.killed) preview.kill('SIGTERM') }
process.on('exit', stop)
try {
  for (let attempt = 0; attempt < 30 && !startup.includes('http://127.0.0.1:4179'); attempt++) {
    await new Promise(resolve => setTimeout(resolve, 250))
  }
  if (!startup.includes('http://127.0.0.1:4179')) throw new Error(`Vite preview did not start: ${startup.slice(-500)}`)
  const browser = await chromium.launch({ headless: true })
  const problems = []
  for (const viewport of [{ name: 'desktop', width: 1440, height: 900 }, { name: 'mobile', width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } })
    const consoleErrors = []
    const failedRequests = []
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()) })
    page.on('requestfailed', request => failedRequests.push(`${request.method()} ${request.url()} (${request.failure()?.errorText || 'failed'})`))
    for (const route of routes) {
      const response = await page.goto(`http://127.0.0.1:4179${route}`, { waitUntil: 'domcontentloaded', timeout: 15000 })
      // The static preview intentionally has no API proxy; waiting for network
      // idle would turn a useful UI check into a long wait for API retries.
      await page.waitForTimeout(750)
      await page.screenshot({ path: `${outputDir}/${viewport.name}-${route === '/' ? 'home' : route.slice(1).replaceAll('/', '-')}.png`, fullPage: true })
      if (!response || response.status() >= 400) problems.push(`${viewport.name} ${route}: HTTP ${response?.status() || 'no response'}`)
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2)
      if (overflow) problems.push(`${viewport.name} ${route}: horizontal overflow`)
      const brokenLinks = await page.locator('a[href]').evaluateAll(links => links.filter(link => link.href.startsWith(location.origin) && link.getAttribute('href') === '#').length)
      if (brokenLinks) problems.push(`${viewport.name} ${route}: ${brokenLinks} empty same-origin link(s)`)
    }
    if (consoleErrors.length) problems.push(`${viewport.name} console: ${consoleErrors.slice(0, 5).join(' | ')}`)
    if (failedRequests.length) problems.push(`${viewport.name} failed requests: ${failedRequests.slice(0, 5).join(' | ')}`)
    await page.close()
  }
  await browser.close()
  if (problems.length) throw new Error(problems.join('; '))
} finally {
  stop()
}
