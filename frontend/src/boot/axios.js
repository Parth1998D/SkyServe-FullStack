import { boot } from 'quasar/wrappers'
import axios from 'axios'
import { LocalStorage } from 'quasar'

// Create axios instance
const api = axios.create({
  baseURL: process.env.API_URL || 'http://localhost:8000',
})

// Request interceptor for API calls
api.interceptors.request.use((config) => {
  const token = LocalStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        LocalStorage.remove('access_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default boot(({ app }) => {
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }
