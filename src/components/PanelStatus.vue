<script setup lang="ts">
import { RefreshCw } from '@lucide/vue'

defineProps<{
  loading?: boolean
  error?: string
}>()

defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="loading" class="panel-status panel-skeleton" aria-label="Loading data">
    <i></i>
    <i></i>
    <i></i>
    <i></i>
  </div>
  <div v-else-if="error" class="panel-status panel-load-error" role="status">
    <strong>Data loading failed</strong>
    <span>Please try again shortly.</span>
    <button type="button" title="Retry this panel" @click="$emit('retry')">
      <RefreshCw :size="14" />
      Retry
    </button>
  </div>
</template>
