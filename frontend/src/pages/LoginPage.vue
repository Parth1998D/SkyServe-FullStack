<template>
  <q-page class="flex flex-center">
    <q-card class="auth-card">
      <q-card-section>
        <div class="text-h6">{{ mode === 'login' ? 'Login' : 'Sign Up' }}</div>
      </q-card-section>
      <div class="q-pa-md auth-form">
        <q-form @submit.prevent="onSubmit" class="fit">
          <div class="flex row justify-between"></div>

          <!-- Email Input -->
          <q-input
            type="email"
            v-model="formState.email"
            label="Email *"
            class="q-mb-lg"
            lazy-rules
            :rules="[(val) => (val && val.length > 0) || 'Please enter your Email']"
          />

          <!-- Password Input -->
          <q-input
            v-model="formState.password"
            label="Password *"
            :type="hidePassword ? 'password' : 'text'"
            lazy-rules
            :rules="[
              (val) => (val && val.length > 0) || 'Please enter your Password',
              (val) => isMinLength(val, 'Password', 8),
              (val) => isMaxLength(val, 'Password', 24),
            ]"
            autocomplete="current-password"
          >
            <template v-slot:append>
              <q-icon
                :name="hidePassword ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="hidePassword = !hidePassword"
              />
            </template>
          </q-input>

          <q-card-actions>
            <q-btn
              :label="mode === 'login' ? 'Login' : 'Sign Up'"
              type="submit"
              class="primary-btn q-mt-md"
              style="width: 100%; padding: 0px"
              no-caps
            />
          </q-card-actions>

          <p class="terms q-mt-lg" style="text-align: center">
            {{ mode === 'login' ? "Don't have an account?" : 'Already have an account?' }}
            <a href="#" class="q-mx-xs" @click.prevent="toggleMode">
              {{ mode === 'login' ? 'Sign Up' : 'Login' }}
            </a>
          </p>
        </q-form>
      </div>
    </q-card>
  </q-page>
</template>

<script>
import { useQuasar } from 'quasar'
import { onBeforeUnmount, reactive, ref } from 'vue'
import { authStore } from 'stores/auth'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const router = useRouter()
    const auth = authStore()

    console.log(auth.isAuthenticated)
    if (auth.isAuthenticated) {
      router.push('/')
    }

    const $q = useQuasar()
    const formState = reactive({
      email: '',
      password: '',
    })

    const mode = ref('login') // Toggle between 'login' and 'register'
    const hidePassword = ref(true)

    const resetFormState = () => {
      formState.email = ''
      formState.password = ''
    }

    onBeforeUnmount(() => {
      resetFormState()
      $q.loading.hide()
    })

    const onSubmit = (e) => {
      e.preventDefault()
      $q.loading.show({
        message: mode.value === 'login' ? 'Logging in...' : 'Signing up...',
      })
      const authAction = mode.value === 'login' ? auth.login : auth.register
      authAction(formState)
        .then(() => {
          if (mode.value === 'login') {
            router.push('/')
          } else {
            $q.notify({
              color: 'positive',
              message: 'Signed up successfully, please login now',
            })
            toggleMode()
          }
        })
        .catch((e) => {
          $q.notify({
            color: 'negative',
            message: 'An error occurred. Please try again.',
          })
          console.log(e)
        })
        .finally(() => {
          $q.loading.hide()
        })
    }

    const toggleMode = () => {
      mode.value = mode.value === 'login' ? 'register' : 'login'
      resetFormState()
    }

    return {
      formState,
      hidePassword,
      mode,
      onSubmit,
      toggleMode,
      isMinLength(val, name, length) {
        return val.length >= length || `${name} should not be less than ${length} characters.`
      },
      isMaxLength(val, name, length) {
        return val.length < length || `${name} should not be more than ${length} characters.`
      },
    }
  },
}
</script>

<style scoped>
.auth-card {
  width: 100%;
  max-width: 400px;
}
</style>
