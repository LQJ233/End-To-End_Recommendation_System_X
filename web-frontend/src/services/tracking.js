const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8080'

function getUserId() {
  return localStorage.getItem('mock_user_id') || 'anonymous'
}

export const EventType = {
  LOGIN: 'login',
  REFRESH_HOME: 'refresh_home',
  EXPOSE: 'expose',
  CLICK: 'click',
  DETAIL_VIEW: 'detail_view',
  ADD_CART: 'add_cart',
}

export const PageType = {
  LOGIN: 'login',
  HOME: 'home',
  ITEM_DETAIL: 'item_detail',
  CART: 'cart',
  SEARCH: 'search',
  OTHER: 'other',
}

export const SourceType = {
  LOGIN_FORM: 'login_form',
  REFRESH_BUTTON: 'refresh_button',
  CARD_EXPOSURE: 'card_exposure',
  HOME_CARD: 'home_card',
  DETAIL_PAGE: 'detail_page',
  CART_BUTTON: 'cart_button',
  OTHER: 'other',
}

function createRequestId() {
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function send(eventType, item, context = {}) {
  const event = {
    event_id: `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    user_id: getUserId(),
    session_id: localStorage.getItem('mock_session_id') || 'session-unknown',
    item_id: item?.id ?? null,
    event_type: eventType,
    page: context.page || 'unknown',
    position: context.position ?? null,
    source: context.source || 'mock',
    request_id: context.request_id || createRequestId(),
    recommendation_id: context.recommendation_id || null,
    event_time: Date.now(),
  }

  console.info('[tracking]', event)

  const history = JSON.parse(localStorage.getItem('mock_tracking_history') || '[]')
  history.push(event)
  localStorage.setItem('mock_tracking_history', JSON.stringify(history.slice(-50)))

  if (typeof globalThis.fetch === 'function') {
    globalThis.fetch(`${API_BASE_URL}/api/v1/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
      keepalive: true,
    }).catch(() => {
      // 埋点上报失败不阻塞前端操作
    })
  }
}

export function trackExposure(item, context = {}) {
  send(EventType.EXPOSE, item, {
    source: SourceType.CARD_EXPOSURE,
    ...context,
  })
}

export function trackClick(item, context = {}) {
  send(EventType.CLICK, item, context)
}

export function trackDetailView(item, context = {}) {
  send(EventType.DETAIL_VIEW, item, context)
}

export function trackRefreshHome(context = {}) {
  send(EventType.REFRESH_HOME, null, {
    page: PageType.HOME,
    source: SourceType.REFRESH_BUTTON,
    ...context,
  })
}

export function trackLogin(context = {}) {
  send(EventType.LOGIN, null, {
    page: PageType.LOGIN,
    source: SourceType.LOGIN_FORM,
    ...context,
  })
}

export function trackAddCart(item, context = {}) {
  send(EventType.ADD_CART, item, context)
}
