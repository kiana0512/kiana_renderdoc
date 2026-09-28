import { mkdirSync, writeFileSync } from 'node:fs'

const cdpPort = process.env.KIANA_CDP_PORT || '9229'
const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json/list`)).json()
const target = targets.find(item => item.type === 'page' && item.title === 'Kiana Studio')
if (!target) throw new Error('Kiana Studio CDP page not found')

const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})

let id = 0
const pending = new Map()
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data)
  if (!message.id) return
  const waiter = pending.get(message.id)
  if (!waiter) return
  pending.delete(message.id)
  if (message.error) waiter.reject(new Error(JSON.stringify(message.error)))
  else waiter.resolve(message.result)
})

function call(method, params = {}) {
  const messageId = ++id
  socket.send(JSON.stringify({ id: messageId, method, params }))
  return new Promise((resolve, reject) => pending.set(messageId, { resolve, reject }))
}

async function evaluate(expression) {
  const reply = await call('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  if (reply.exceptionDetails) throw new Error(reply.exceptionDetails.text)
  return reply.result.value
}

const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))
const output = 'E:/KianaStudioElectron/test-results/ui-smoke'
mkdirSync(output, { recursive: true })

await call('Page.enable')
await call('Runtime.enable')
await call('Page.reload', { ignoreCache: true })
await wait(2200)

const initial = await evaluate(`(() => ({
  title: document.title,
  passRows: [...document.querySelectorAll('.pass-row:not(.pass-header)')].map(row => row.children[0]?.textContent?.trim()),
  selectedPass: document.querySelector('.pass-row.selected')?.children[0]?.textContent?.trim(),
  toolbarButtons: [...document.querySelectorAll('.viewport-toolbar button')].map(button => ({
    title: button.title, text: button.textContent?.trim(), width: Math.round(button.getBoundingClientRect().width), height: Math.round(button.getBoundingClientRect().height), whiteSpace: getComputedStyle(button).whiteSpace
  }))
}))()`)

await evaluate(`(() => {
  const row = [...document.querySelectorAll('.pass-row:not(.pass-header)')].find(item => item.children[0]?.textContent?.trim() === '13')
  if (!row) throw new Error('Pass 13 row missing')
  row.click()
  return true
})()`)
await wait(500)

const uiStageList = await evaluate(`(() => ({
  selectedPass: document.querySelector('.pass-row.selected')?.children[0]?.textContent?.trim(),
  stageCount: document.querySelectorAll('.composition-stage').length,
  first: document.querySelector('.composition-stage')?.textContent?.trim(),
  last: [...document.querySelectorAll('.composition-stage')].at(-1)?.textContent?.trim(),
  clear: [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('Clear'))?.textContent?.trim(),
  copy: [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('Copy'))?.textContent?.trim(),
  present: [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('Present'))?.textContent?.trim()
}))()`)

await evaluate(`(() => {
  const stage = [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('EID 2487'))
  if (!stage) throw new Error('UI EID 2487 missing')
  stage.click()
  return true
})()`)
await wait(4500)

const uiMid = await evaluate(`(() => ({
  selectedStage: document.querySelector('.composition-stage.selected')?.textContent?.trim(),
  hud: document.querySelector('.viewport-hud')?.innerText,
  imagePrefix: document.querySelector('.viewport-image')?.getAttribute('src')?.slice(0, 30),
  toolbarOverflow: document.querySelector('.viewport-toolbar')?.scrollWidth > document.querySelector('.viewport-toolbar')?.clientWidth,
  inspectorTitle: document.querySelector('.asset-title')?.innerText,
  inspectorEvidence: document.querySelector('.material-row')?.innerText
}))()`)

for (const title of ['放大', '适配整个帧', '重置到 1:1', '切换真实数据叠加层']) {
  await evaluate(`(() => { const button = [...document.querySelectorAll('.viewport-toolbar button')].find(item => item.title === ${JSON.stringify(title)}); if (!button) throw new Error('missing toolbar button: ${title}'); button.click(); return true })()`)
}

let shot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
writeFileSync(`${output}/pass13-ui-eid2487.png`, Buffer.from(shot.data, 'base64'))

await evaluate(`(() => {
  const row = [...document.querySelectorAll('.pass-row:not(.pass-header)')].find(item => item.children[0]?.textContent?.trim() === '8')
  if (!row) throw new Error('Pass 8 row missing')
  row.click()
  return true
})()`)
await wait(300)
await evaluate(`(() => {
  const stage = [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('EID 1610'))
  if (!stage) throw new Error('transparent cloth EID 1610 missing')
  stage.click()
  return true
})()`)
await wait(4500)

const cloth = await evaluate(`(() => ({
  selectedPass: document.querySelector('.pass-row.selected')?.children[0]?.textContent?.trim(),
  selectedStage: document.querySelector('.composition-stage.selected')?.textContent?.trim(),
  hud: document.querySelector('.viewport-hud')?.innerText,
  transform: document.querySelector('.viewport-image')?.style.transform
}))()`)
shot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
writeFileSync(`${output}/pass08-eid1610-transparent-cloth.png`, Buffer.from(shot.data, 'base64'))

await evaluate(`(() => {
  const row = [...document.querySelectorAll('.pass-row:not(.pass-header)')].find(item => item.children[0]?.textContent?.trim() === '13')
  row.click()
  return true
})()`)
await wait(250)
await evaluate(`(() => {
  const stage = [...document.querySelectorAll('.composition-stage')].find(item => item.textContent?.includes('EID 3199'))
  if (!stage) throw new Error('UI EID 3199 missing')
  stage.click()
  return true
})()`)
await wait(4500)
const finalUi = await evaluate(`(() => ({
  selectedStage: document.querySelector('.composition-stage.selected')?.textContent?.trim(),
  inspectorTitle: document.querySelector('.asset-title')?.innerText,
  toolbarOverflow: document.querySelector('.viewport-toolbar')?.scrollWidth > document.querySelector('.viewport-toolbar')?.clientWidth
}))()`)
shot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
writeFileSync(`${output}/pass13-ui-eid3199.png`, Buffer.from(shot.data, 'base64'))

const result = { initial, uiStageList, uiMid, cloth, finalUi, screenshots: [
  `${output}/pass13-ui-eid2487.png`,
  `${output}/pass08-eid1610-transparent-cloth.png`,
  `${output}/pass13-ui-eid3199.png`,
] }
writeFileSync(`${output}/result.json`, JSON.stringify(result, null, 2))
console.log(JSON.stringify(result, null, 2))
socket.close()
