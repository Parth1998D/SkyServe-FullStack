import { defineStore } from 'pinia'
import { LocalStorage } from 'quasar'
import { authApi } from 'src/services/api'

export const authStore = defineStore('auth', {
  state: () => ({
    token: LocalStorage.getItem('access_token') || null,
    isAuthenticated: !!LocalStorage.getItem('access_token'),
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated,
  },

  actions: {
    async login(credentials) {
      try {
        const { data } = await authApi.login(credentials)
        this.setToken(data.access_token)
        return true
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },

    async register(credentials) {
      try {
        await authApi.register(credentials)
        return true
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },

    setToken(token) {
      this.token = token
      this.isAuthenticated = true
      LocalStorage.set('access_token', token)
    },

    clearAuth() {
      this.token = null
      this.isAuthenticated = false
      LocalStorage.remove('access_token')
    },

    logout() {
      this.clearAuth()
    },
  },
})
