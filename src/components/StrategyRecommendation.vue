<script setup lang="ts">
import { ArrowRight, Target } from '@lucide/vue'
import type { Prediction, StrategyOption } from '../types'
import PanelStatus from './PanelStatus.vue'

defineProps<{
  prediction: Prediction
  options: StrategyOption[]
  currentCompound?: string
  loading?: boolean
  error?: string
}>()

defineEmits<{ retry: [] }>()
</script>

<template>
  <section class="command-card strategy-panel" data-tour="strategy-recommendation">
    <header class="card-heading">
      <div>
        <span class="eyebrow">AI decision support</span>
        <h2>Strategy Recommendation</h2>
      </div>
      <span class="risk-badge" :data-risk="prediction.risk">{{ prediction.action.replaceAll('_', ' ') }}</span>
    </header>

    <div class="strategy-primary">
      <div class="strategy-lap">
        <span>Target window</span>
        <strong>L{{ prediction.optimal_pit_lap }}</strong>
      </div>
      <div class="strategy-path">
        <span>Recommended sequence</span>
        <strong>{{ currentCompound || 'Current' }} <ArrowRight :size="16" /> {{ prediction.recommended_tire }}</strong>
        <small>Expected net gain {{ prediction.expected_gain.toFixed(2) }}s</small>
      </div>
      <div class="undercut-score">
        <Target :size="17" />
        <span>Undercut</span>
        <strong>{{ Math.round(prediction.undercut_probability * 100) }}%</strong>
      </div>
    </div>

    <div class="strategy-list">
      <article v-for="option in options" :key="option.label">
        <div>
          <span>{{ option.label }}</span>
          <strong>{{ option.path }}</strong>
          <small>{{ option.trigger }}</small>
        </div>
        <div class="strategy-projection">
          <strong>{{ option.projected_text }}</strong>
          <span>{{ Math.round(option.confidence * 100) }}% conf.</span>
        </div>
      </article>
    </div>
    <PanelStatus :loading="loading" :error="error" @retry="$emit('retry')" />
  </section>
</template>
