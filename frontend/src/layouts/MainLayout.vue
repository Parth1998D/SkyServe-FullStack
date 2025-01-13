<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated v-if="!hideHeader()">
      <q-toolbar>
        <q-toolbar-title> SkyServe Assignment </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { useRoute } from 'vue-router'

export default {
  components: {},
  setup() {
    const route = useRoute()

    return {
      hideHeader: () => route.name === 'Globe',
    }
  },
}
</script>

<style lang="scss"></style>
