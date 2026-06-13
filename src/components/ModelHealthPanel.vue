<script setup lang="ts">
import { Activity, Database, Server, ShieldCheck } from '@lucide/vue'
import type { DataSource, HealthResponse } from '../types'

defineProps<{
  health: HealthResponse
  source: DataSource
  lastUpdated: Date | null
  loading: boolean
}>()
</script>

<template>
  <section class="command-card model-health-panel" data-tour="model-health">
    <header class="card-heading">
      <div>
        <span class="eyebrow">System telemetry</span>
        <h2>API / Model Status</h2>
      </div>
      <span class="status-chip" :class="{ warning: source === 'mock' }">{{ source === 'api' ? 'LIVE API' : 'MOCK MODE' }}</span>
    </header>

    <div class="health-list">
      <article>
        <Server :size="16" />
        <div><span>Backend</span><strong>{{ health.status.toUpperCase() }}</strong></div>
        <i :class="health.status"></i>
      </article>
      <article>
        <ShieldCheck :size="16" />
        <div><span>Weights</span><strong>{{ health.model.weights_loaded ? 'LOADED' : 'MISSING' }}</strong></div>
        <i :class="health.model.weights_loaded ? 'ok' : 'degraded'"></i>
      </article>
      <article>
        <Database :size="16" />
        <div><span>Feature pipeline</span><strong>{{ health.model.feature_count }} FEATURES</strong></div>
        <i class="ok"></i>
      </article>
      <article>
        <Activity :size="16" />
        <div><span>Inference</span><strong>{{ loading ? 'UPDATING' : health.model.device.toUpperCase() }}</strong></div>
        <i :class="loading ? 'busy' : 'ok'"></i>
      </article>
    </div>

    <footer class="health-footer">
      <span>{{ health.model.name }}</span>
      <span>{{ health.model.sequence_length }}x{{ health.model.input_dim }}</span>
      <span>{{ lastUpdated ? lastUpdated.toLocaleTimeString() : 'standby' }}</span>
    </footer>
  </section>
</template>
