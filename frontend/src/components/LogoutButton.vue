<template>
  <q-btn dense round color="red" icon="power_settings_new" @click="logoutConfirmation = true" />
  <q-dialog v-model="logoutConfirmation">
    <q-card>
      <div class="q-px-md q-pt-md">
        <div>
          <div class="text-h6">Confirm Logout</div>
          <div class="text-body2 q-mt-xs">Are you sure you want to logout?</div>
        </div>
        <q-card-actions align="right" class="q-mt-xs">
          <q-btn flat label="Cancel" color="primary" @click="logoutConfirmation = false" />
          <q-btn flat label="Logout" color="negative" @click="doLogout" />
        </q-card-actions>
      </div>
    </q-card>
  </q-dialog>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from 'stores/auth'

export default {
  components: {},
  setup() {
    const router = useRouter()
    const auth = authStore()
    const logoutConfirmation = ref(false)

    const doLogout = () => {
      auth.logout()
      router.push('/login')
    }

    return {
      doLogout,
      logoutConfirmation,
    }
  },
}
</script>

<style lang="scss" scoped></style>
