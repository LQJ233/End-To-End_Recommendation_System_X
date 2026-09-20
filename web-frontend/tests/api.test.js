import assert from 'node:assert/strict'
import test from 'node:test'

globalThis.localStorage = {
  values: new Map(),
  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null
  },
  setItem(key, value) {
    this.values.set(key, String(value))
  },
  clear() {
    this.values.clear()
  },
}

const api = await import('../src/services/api.js')

test.beforeEach(() => {
  localStorage.clear()
  globalThis.fetch = () => Promise.reject(new Error('fetch not stubbed'))
})

test('loginOrRegister returns login data for an existing user', async () => {
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      code: 0,
      message: 'success',
      data: { userId: 1, username: 'alice', token: 'token-1' },
    }),
  })

  const user = await api.loginOrRegister('alice', 'password123')

  assert.equal(user.userId, 1)
  assert.equal(user.token, 'token-1')
})

test('loginOrRegister registers when backend says user not found', async () => {
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) })
    if (url.endsWith('/login')) {
      return {
        ok: true,
        json: async () => ({ code: 30003, message: '用户不存在', data: null }),
      }
    }
    return {
      ok: true,
      json: async () => ({
        code: 0,
        message: 'success',
        data: { userId: 2, username: 'bob', token: 'token-2' },
      }),
    }
  }

  const user = await api.loginOrRegister('bob', 'password123')

  assert.equal(user.userId, 2)
  assert.equal(calls.length, 2)
  assert.match(calls[0].url, /\/api\/v1\/auth\/login$/)
  assert.match(calls[1].url, /\/api\/v1\/auth\/register$/)
})

test('fetchHome sends X-User-Id and returns home payload', async () => {
  let captured
  globalThis.fetch = async (url, options) => {
    captured = { url, options }
    return {
      ok: true,
      json: async () => ({
        code: 0,
        data: { requestId: 'req-1', recommendationId: 'rec-1', userId: 'user-1', items: [] },
      }),
    }
  }

  const home = await api.fetchHome('user-1')

  assert.equal(home.requestId, 'req-1')
  assert.equal(captured.options.headers['X-User-Id'], 'user-1')
})

test('mapApiItemToProduct maps backend item fields for display', () => {
  const product = api.mapApiItemToProduct({
    id: 102,
    title: '广告商品 102',
    categoryId: 6406,
    brandId: 95471,
    price: 170.0,
  })

  assert.equal(product.id, 102)
  assert.equal(product.title, '广告商品 102')
  assert.equal(product.category, '类目 6406')
  assert.equal(product.brand, '品牌 95471')
  assert.equal(product.price, 170.0)
  assert.equal(typeof product.emoji, 'string')
})
