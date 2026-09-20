import assert from 'node:assert/strict'
import test from 'node:test'

import { mockProducts } from '../src/mock/products.js'

test('mock product catalog has unique and complete items', () => {
  assert.equal(mockProducts.length, 8)
  assert.equal(new Set(mockProducts.map((item) => item.id)).size, mockProducts.length)

  for (const item of mockProducts) {
    assert.equal(typeof item.id, 'number')
    assert.equal(typeof item.title, 'string')
    assert.equal(typeof item.category, 'string')
    assert.equal(typeof item.brand, 'string')
    assert.equal(typeof item.price, 'number')
    assert.equal(typeof item.emoji, 'string')
  }
})
