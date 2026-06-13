import axios from 'axios'

// Nginx Lua track endpoint is configured at /track via vite proxy.
const tracker = axios.create({ baseURL: '/track', timeout: 3000 })

export const sendBehavior = (payload) =>
  tracker.post('/behavior', payload).catch(() => null) // swallow errors per spec: tracking must not block UX
