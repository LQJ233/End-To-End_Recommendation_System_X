const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8080'

const PRODUCT_EMOJIS = ['🛍️', '🎧', '👟', '📱', '💄', '⌚', '💻', '🧴']

export class ApiError extends Error {
  constructor(code, message) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

async function request(path, options = {}) {
  const response = await globalThis.fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  const payload = await response.json()
  if (payload.code !== 0) {
    throw new ApiError(payload.code, payload.message || 'request failed')
  }
  return payload.data
}

export async function loginOrRegister(username, password) {
  try {
    return await request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  } catch (error) {
    if (error instanceof ApiError && error.code === 30003) {
      return request('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
    }
    throw error
  }
}

export async function fetchHome(userId, size = 20) {
  return request(`/api/v1/home?size=${size}`, {
    headers: {
      'X-User-Id': userId,
    },
  })
}

export async function fetchItem(itemId) {
  return request(`/api/v1/items/${itemId}`)
}

export function mapApiItemToProduct(item, index = 0) {
  return {
    id: Number(item.id),
    title: item.title,
    category: `类目 ${item.categoryId}`,
    brand: `品牌 ${item.brandId}`,
    price: Number(item.price),
    emoji: PRODUCT_EMOJIS[index % PRODUCT_EMOJIS.length],
    imageUrl: item.imageUrl || null,
  }
}
