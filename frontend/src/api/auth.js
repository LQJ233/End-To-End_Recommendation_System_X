import http from './http'

export const register = (body) => http.post('/auth/register', body)
export const login = (body) => http.post('/auth/login', body)
export const logout = () => http.post('/auth/logout')
export const refreshToken = (token) => http.post('/auth/refresh', { refreshToken: token })
export const getMe = () => http.get('/users/me')
export const updateMe = (body) => http.put('/users/me', body)
export const changePassword = (body) => http.put('/users/me/password', body)

export const adminListUsers = (params) => http.get('/admin/users', { params })
export const adminSetStatus = (userId, status) => http.put(`/admin/users/${userId}/status`, { status })
export const adminResetPassword = (userId, newPassword) => http.put(`/admin/users/${userId}/password`, { newPassword })
export const adminSetRoles = (userId, roles) => http.put(`/admin/users/${userId}/roles`, { roles })
