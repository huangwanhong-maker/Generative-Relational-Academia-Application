/**
 * Photograph the running application for the gallery.
 *
 * The pictures in the README are of the real thing, taken from a real server
 * with a real record behind it — not mockups. A gallery of mockups is a
 * promise; a gallery of screenshots is a claim you can check by running it.
 *
 *   node tools/gallery.mjs            # server must already be running
 *
 * Deliberately not part of the build. It needs a browser, a server and a
 * populated record, and none of those should be a dependency of anything.
 */

import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import puppeteer from 'puppeteer'

const BASE = process.env.GRA_BASE ?? 'http://127.0.0.1:5173'
const OUT = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/gallery')
const NAME = process.env.GRA_USER ?? 'ada'
const PASSWORD = process.env.GRA_PASSWORD ?? 'a-good-enough-password'

mkdirSync(OUT, { recursive: true })

const browser = await puppeteer.launch({ headless: 'new' })
const page = await browser.newPage()
await page.setViewport({ width: 1180, height: 900, deviceScaleFactor: 2 })

const settle = async (ms = 700) => new Promise((done) => setTimeout(done, ms))

async function shoot(name, { path, full = false, click, wait } = {}) {
  if (path) {
    await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle0' })
    // The client renders an empty shell until /api/me resolves, so waiting on
    // the network is not enough -- wait for something to actually be there.
    await page.waitForSelector(wait ?? 'header, .bar', { timeout: 15000 })
    await settle()
  }
  if (click) {
    await page.evaluate(click)
    await settle()
  }
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: full })
  console.log(`  ${name}.png`)
}

console.log('signed out:')
await shoot('01-front-page', { path: '/', full: true })
await shoot('02-sign-in', { path: '/sign-in', wait: 'input[type="password"]' })

console.log('signing in…')
await page.goto(`${BASE}/sign-in`, { waitUntil: 'networkidle0' })
await page.waitForSelector('input[autocomplete="username"]', { timeout: 15000 })
await page.type('input[autocomplete="username"]', NAME)
await page.type('input[type="password"]', PASSWORD)
await Promise.all([page.click('button[type="submit"]'), settle(1500)])

console.log('signed in:')
await shoot('03-your-projects', { path: '/projects', full: true })
await shoot('04-project-overview', { path: '/p/trust', full: true })
await shoot('05-trajectories', { path: '/p/trust?tab=trajectories', full: true, wait: 'svg g.n' })

// Open the node panel by clicking the first transition box in the drawing.
await shoot('06-node-panel', {
  path: '/p/trust?tab=trajectories',
  full: true,
  wait: 'svg g.n',
  click: () => {
    const box = document.querySelector('svg g.n')
    box?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  },
})

await shoot('07-questions', { path: '/p/trust?tab=questions', full: true })
await shoot('08-search', { path: '/search?q=trust', full: true })

await browser.close()
console.log(`written to ${OUT}`)
