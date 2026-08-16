import puppeteer from 'puppeteer'
const B = 'http://127.0.0.1:5173'
const out = process.argv[2] ?? '/tmp/shot.png'
const path = process.argv[3] ?? '/p/field-memory?tab=trajectories'
const clickNode = process.argv[4] // optional data-node substring to click
const b = await puppeteer.launch({ headless: 'new' })
const p = await b.newPage()
await p.setViewport({ width: 1280, height: 940, deviceScaleFactor: 2 })
await p.goto(`${B}/sign-in`, { waitUntil: 'networkidle0' })
await p.waitForSelector('input[autocomplete="username"]')
await p.type('input[autocomplete="username"]', 'ada')
await p.type('input[type="password"]', 'a-good-enough-password')
await Promise.all([p.click('button[type="submit"]'), new Promise(r => setTimeout(r, 1500))])
await p.goto(`${B}${path}`, { waitUntil: 'networkidle0' })
await p.waitForSelector('svg', { timeout: 12000 }).catch(() => {})
await new Promise(r => setTimeout(r, 900))
if (clickNode) {
  const box = await p.evaluate((needle) => {
    const lower = needle.toLowerCase()
    const el = [...document.querySelectorAll('[data-node]')].find(
      (e) => e.getAttribute('data-node').includes(needle) || e.textContent.toLowerCase().includes(lower),
    )
    if (!el) return null
    const r = el.getBoundingClientRect()
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 }
  }, clickNode)
  if (box) {
    await p.mouse.click(box.x, box.y)   // the real path: pointerdown, pointerup
    await new Promise(r => setTimeout(r, 900))
  }
}
await p.screenshot({ path: out, fullPage: true })
await b.close()
console.log('shot ->', out)
