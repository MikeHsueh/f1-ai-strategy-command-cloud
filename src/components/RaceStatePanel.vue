<script setup lang="ts">
import { Flag, Gauge, Timer, Zap } from '@lucide/vue'
import type { RaceState } from '../types'
import PanelStatus from './PanelStatus.vue'

defineProps<{
  state: RaceState
  loading?: boolean
  error?: string
}>()

defineEmits<{ retry: [] }>()
</script>

<template>
  <section class="command-card race-state-panel" data-tour="race-state">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Live context</span>
        <h2>Race State</h2>
      </div>
      <span class="status-chip" :class="{ alert: state.safety_car }">
        {{ state.safety_car ? 'SAFETY CAR' : 'GREEN FLAG' }}
      </span>
    </header>

    <div class="race-state-hero">
      <div>
        <span>Focused driver</span>
        <strong>{{ state.driver }}</strong>
        <small>{{ state.team }}</small>
      </div>
      <div class="position-number">P{{ state.position }}</div>
    </div>

    <div class="metric-grid four">
      <article>
        <Timer :size="15" />
        <span>Lap</span>
        <strong>{{ state.lap }} / {{ state.total_laps }}</strong>
      </article>
      <article>
        <Flag :size="15" />
        <span>Gap Ahead</span>
        <strong>{{ state.gap_ahead.toFixed(2) }}s</strong>
      </article>
      <article>
        <Flag :size="15" />
        <span>Gap Behind</span>
        <strong>{{ state.gap_behind.toFixed(2) }}s</strong>
      </article>
      <article>
        <Gauge :size="15" />
        <span>Speed</span>
        <strong>{{ Math.round(state.speed) }} km/h</strong>
      </article>
    </div>

    <div class="telemetry-strip">
      <span class="current-tire-readout">
        <b>{{ state.tire.compound }}</b>
        {{ state.tire.life }}L · {{ Math.round(state.tire.health) }}%
      </span>
      <span><b>{{ Math.round(state.rpm) }}</b> RPM</span>
      <span><b>{{ Math.round(state.throttle) }}%</b> THR</span>
      <span><b>{{ Math.round(state.brake) }}%</b> BRK</span>
      <span><Zap :size="12" /><b>{{ Math.round(state.safety_car_incident_risk * 100) }}%</b> SC RISK</span>
    </div>
    <PanelStatus :loading="loading" :error="error" @retry="$emit('retry')" />
  </section>
</template>
