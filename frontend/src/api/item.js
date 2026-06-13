import http from './http'

export const batchItems = (itemIds) => http.get('/items/batch', { params: { itemIds: itemIds.join(',') } })
export const mockOrder = (body) => http.post('/orders/mock', body)
