import { defineStore } from 'pinia'
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister, refreshToken as apiRefresh } from '../api/auth'

const TOKEN_KEY = 'recsys.token'
const REFRESH_KEY = 'recsys.refresh'
const USERID_KEY = 'recsys.userId'

function ensureGuestId () {
  let id = localStorage.getItem(USERID_KEY)
  if (!id) {
    id = 'guest_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
    localStorage.setItem(USERID_KEY, id)
  }
  return id
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: ensureGuestId(),
    token: localStorage.getItem(TOKEN_KEY) || '',
    refreshTokenValue: localStorage.getItem(REFRESH_KEY) || '',
    profile: null
  }),
  getters: {
    isLogin: (s) => !!s.token && !!s.profile,
    roles: (s) => s.profile?.roles || []
  },
  actions: {
    async bootstrap () {
      if (this.token) {
        try {
          const r = await getMe()
          if (r.code === 0) {
            this.profile = r.data
            this.userId = r.data.userId
          } else {
            this.clearAuth()
          }
        } catch {
          this.clearAuth()
        }
      }
    },
    async login (body) {
      const r = await apiLogin(body)
      if (r.code !== 0) throw new Error(r.message || 'login_failed')
      this.applyLoginResponse(r.data)
      return r.data
    },
    async register (body) {
      const r = await apiRegister(body)
      if (r.code !== 0) throw new Error(r.message || 'register_failed')
      return r.data
    },
    async logout () {
      try { await apiLogout() } catch {}
      this.clearAuth()
    },
    /**
     * 用 refresh token 续签. http.js 拦截到 401 时会尝试调用,
     * 失败则回到 clearAuth.
     */
    async tryRefresh () {
      if (!this.refreshTokenValue) return false
      try {
        const r = await apiRefresh(this.refreshTokenValue)
        if (r.code === 0) {
          this.applyLoginResponse(r.data)
          return true
        }
      } catch {}
      return false
    },
    applyLoginResponse (data) {
      this.token = data.accessToken
      this.refreshTokenValue = data.refreshToken || ''
      this.profile = { ...data.user }
      this.userId = data.user.userId
      localStorage.setItem(TOKEN_KEY, this.token)
      if (this.refreshTokenValue) {
        localStorage.setItem(REFRESH_KEY, this.refreshTokenValue)
      }
      localStorage.setItem(USERID_KEY, this.userId)
    },
    clearAuth () {
      this.token = ''
      this.refreshTokenValue = ''
      this.profile = null
      this.userId = ensureGuestId()
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
    }
  }
})
