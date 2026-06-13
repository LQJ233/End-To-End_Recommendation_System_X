import http from './http'

export const refreshRecommendations = (body) => http.post('/recommendations/refresh', body)
export const getHomeFeed = (params) => http.get('/recommendations/home', { params })
export const confirmExposure = (body) => http.post('/recommendations/exposure', body)
