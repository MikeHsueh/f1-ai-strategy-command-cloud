<script setup lang="ts">
import type { DriverComparisonRow } from '../types'
import PanelStatus from './PanelStatus.vue'

defineProps<{
  rows: DriverComparisonRow[]
  selectedDriver: string
  compact?: boolean
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  select: [driver: string]
  retry: []
}>()

function probabilityClass(value: number) {
  if (value >= 0.85) return 'critical'
  if (value >= 0.65) return 'high'
  if (value >= 0.35) return 'medium'
  return 'low'
}
</script>

<template>
  <section class="command-card comparison-panel" data-tour="driver-comparison">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Field intelligence</span>
        <h2>Driver Comparison</h2>
      </div>
      <span class="panel-note">Select row to focus</span>
    </header>

    <div class="comparison-table" :class="{ compact }">
      <div class="comparison-head">
        <span>Pos</span><span>Driver</span><span>Team</span><span>Gap</span><span>Tyre</span><span>Age</span><span>Pit risk</span><span>Est. stop</span>
      </div>
      <button
        v-for="row in rows"
        :key="row.code"
        type="button"
        class="comparison-row"
        :class="{ selected: row.code === selectedDriver }"
        @click="emit('select', row.code)"
      >
        <span>P{{ row.position }}</span>
        <strong>{{ row.code }}</strong>
        <span>{{ row.team }}</span>
        <span>{{ row.gap }}</span>
        <b class="compound-dot" :data-compound="row.compound">{{ row.compound.slice(0, 1) }}</b>
        <span>{{ row.tyre_age }}</span>
        <i :class="probabilityClass(row.pit_probability)">{{ Math.round(row.pit_probability * 100) }}%</i>
        <span>{{ row.predicted_pit_lap ? `L${row.predicted_pit_lap}` : '--' }}</span>
      </button>
    </div>
    <PanelStatus :loading="loading" :error="error" @retry="emit('retry')" />
  </section>
</template>
