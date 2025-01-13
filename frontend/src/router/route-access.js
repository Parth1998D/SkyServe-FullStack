import { authStore } from 'stores/auth'

const RouteAccess = {
  Home: {
    requireLogin: true,
  },
  Globe: {
    requireLogin: true,
  },
}

export default new (class {
  constructor() {
    this.authStore = null
  }

  Meta(routeName) {
    if (routeName in RouteAccess) {
      return RouteAccess[routeName]
    }
    return {}
  }

  MenuVisible(routeName) {
    const routeMeta = this.Meta(routeName)
    return this.ValidateAccess(
      {
        meta: routeMeta,
        name: routeName,
      },
      {},
    )
  }

  ValidateAccess(to) {
    if (!this.authStore) {
      this.authStore = authStore()
    }
    const meta = this.Meta(to.name)
    console.log(to.name, meta)
    if ('requireLogin' in meta && meta.requireLogin) {
      if (this.authStore.isAuthenticated) {
        return true
      } else {
        return false
      }
    }
    return true
  }
})()
