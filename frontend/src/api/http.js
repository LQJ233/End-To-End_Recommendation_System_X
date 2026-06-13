import axios from 'axios'
import router from '../router'
import { useUserStore } from '../stores/user'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

http.interceptors.request.use((cfg) => {
  const user = useUserStore()
  if (user.token) {
    cfg.headers.Authorization = `Bearer ${user.token}`
  }
  return cfg
})

// 同一时刻只允许一个 refresh 请求, 其他 401 都挂起等结果
let refreshPromise = null

async function tryRefresh () {
  const user = useUserStore()
  if (!refreshPromise) {
    refreshPromise = user.tryRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

http.interceptors.response.use(
  (resp) => resp.data,
  async (err) => {
    const status = err.response?.status
    const body = err.response?.data
    const cfg = err.config || {}
    const user = useUserStore()

    if (status === 401 && !cfg.__isRetry) {
      // 不要对 refresh 请求本身做二次 refresh, 避免死循环
      if (cfg.url && cfg.url.includes('/auth/refresh')) {
        user.clearAuth()
        if (router.currentRoute.value.path !== '/login') router.push('/login')
        return Promise.reject(body || err)
      }
      const ok = await tryRefresh()
      if (ok) {
        // 用新 token 重放一次
        cfg.__isRetry = true
        cfg.headers = { ...(cfg.headers || {}), Authorization: `Bearer ${user.token}` }
        return http.request(cfg)
      }
      user.clearAuth()
      if (router.currentRoute.value.path !== '/login') router.push('/login')
      return Promise.reject(body || err)
    }
    if (status === 401) {
      user.clearAuth()
      if (router.currentRoute.value.path !== '/login') router.push('/login')
    }
    return Promise.reject(body || err)
  }
)

export default http
