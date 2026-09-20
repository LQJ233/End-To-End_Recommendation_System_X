import assert from 'node:assert/strict'
import test from 'node:test'

class MemoryStorage {
  constructor() {
    this.values = new Map()
  }

  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null
  }

  setItem(key, value) {
    this.values.set(key, String(value))
  }

  removeItem(key) {
    this.values.delete(key)
  }

  clear() {
    this.values.clear()
  }
}

globalThis.localStorage = new MemoryStorage()
console.info = () => {}
globalThis.fetch = () => Promise.resolve({ ok: true })

const tracking = await import('../src/services/tracking.js')

test.beforeEach(() => {
  localStorage.clear()
})

test('tracking enums use the agreed event names', () => {
  assert.equal(tracking.EventType.EXPOSE, 'expose')
  assert.equal(tracking.EventType.CLICK, 'click')
  assert.equal(tracking.PageType.HOME, 'home')
  assert.equal(tracking.SourceType.CARD_EXPOSURE, 'card_exposure')
})

test('trackExposure stores a complete exposure event', () => {
  localStorage.setItem('mock_user_id', 'local_user_alice')
  localStorage.setItem('mock_session_id', 'session-1')

  tracking.trackExposure(
    { id: 1001 },
    { page: 'home', position: 2, request_id: 'req-1', recommendation_id: 'rec-1' },
  )

  const history = JSON.parse(localStorage.getItem('mock_tracking_history'))
  assert.equal(history.length, 1)
  assert.equal(history[0].user_id, 'local_user_alice')
  assert.equal(history[0].session_id, 'session-1')
  assert.equal(history[0].item_id, 1001)
  assert.equal(history[0].event_type, 'expose')
  assert.equal(history[0].page, 'home')
  assert.equal(history[0].position, 2)
  assert.equal(history[0].source, 'card_exposure')
  assert.equal(history[0].request_id, 'req-1')
  assert.equal(history[0].recommendation_id, 'rec-1')
  assert.match(history[0].event_id, /^evt-/)
  assert.equal(typeof history[0].event_time, 'number')
})

test('tracking events are also posted to the backend asynchronously', () => {
  const calls = []
  globalThis.fetch = (url, options) => {
    calls.push({ url, options })
    return Promise.resolve({ ok: true })
  }

  tracking.trackClick(
    { id: 1003 },
    { page: 'home', position: 2, request_id: 'req-backend' },
  )

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8080/api/v1/events')
  assert.equal(calls[0].options.method, 'POST')
  assert.equal(calls[0].options.headers['Content-Type'], 'application/json')
  assert.equal(JSON.parse(calls[0].options.body).item_id, 1003)
})

test('trackRefreshHome stores a non-item home event', () => {
  tracking.trackRefreshHome({ request_id: 'req-refresh', recommendation_id: 'rec-refresh' })

  const [event] = JSON.parse(localStorage.getItem('mock_tracking_history'))
  assert.equal(event.item_id, null)
  assert.equal(event.event_type, 'refresh_home')
  assert.equal(event.page, 'home')
  assert.equal(event.source, 'refresh_button')
  assert.equal(event.request_id, 'req-refresh')
})

test('trackClick keeps position and source from the caller', () => {
  tracking.trackClick(
    { id: 1002 },
    { page: 'home', position: 4, source: 'home_card', request_id: 'req-click' },
  )

  const [event] = JSON.parse(localStorage.getItem('mock_tracking_history'))
  assert.equal(event.item_id, 1002)
  assert.equal(event.event_type, 'click')
  assert.equal(event.position, 4)
  assert.equal(event.source, 'home_card')
})

test('tracking history keeps only the newest 50 events', () => {
  for (let index = 0; index < 55; index += 1) {
    tracking.trackClick({ id: index + 1 }, { page: 'home', position: index + 1 })
  }

  const history = JSON.parse(localStorage.getItem('mock_tracking_history'))
  assert.equal(history.length, 50)
  assert.equal(history[0].item_id, 6)
  assert.equal(history[49].item_id, 55)
})
