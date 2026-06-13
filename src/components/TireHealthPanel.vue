<script setup lang="ts">
import { CircleDot, Thermometer, TrendingDown } from '@lucide/vue'
import type { TireState } from '../types'

defineProps<{ tire: TireState }>()
</script>

<template>
  <section class="command-card tire-panel" data-tour="tire-state">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Stint condition</span>
        <h2>Tire Health</h2>
      </div>
      <span class="compound-pill" :data-compound="tire.compound">{{ tire.compound }}</span>
    </header>

    <div class="tire-health-main">
      <div class="health-ring" :style="{ '--health': `${tire.health * 3.6}deg` }">
        <div>
          <strong>{{ Math.round(tire.health) }}%</strong>
          <span>Health</span>
        </div>
      </div>
      <div class="tire-stats">
        <article><CircleDot :size="15" /><span>Tyre age</span><strong>{{ tire.life }} laps</strong></article>
        <article><TrendingDown :size="15" /><span>Degradation</span><strong>{{ tire.degradation.toFixed(3) }}</strong></article>
        <article><Thermometer :size="15" /><span>Temperature</span><strong>{{ tire.temperature_proxy.toFixed(1) }} C</strong></article>
      </div>
    </div>

    <div class="health-bar"><i :style="{ width: `${tire.health}%` }"></i></div>
  </section>
</template>
