<script setup lang="ts">
import { CloudRain, Droplets, ThermometerSun, Wind } from '@lucide/vue'
import type { WeatherState } from '../types'

defineProps<{ weather: WeatherState }>()
</script>

<template>
  <section class="command-card weather-panel" data-tour="weather">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Track conditions</span>
        <h2>Weather</h2>
      </div>
      <span class="weather-condition">{{ weather.condition }}</span>
    </header>

    <div class="weather-radar">
      <span class="radar-sweep"></span>
      <div>
        <CloudRain :size="22" />
        <strong>{{ Math.round(weather.model_rain_risk) }}%</strong>
        <small>Model rain risk</small>
      </div>
    </div>

    <div class="metric-grid four weather-metrics">
      <article><ThermometerSun :size="15" /><span>Air</span><strong>{{ weather.air_temp.toFixed(1) }} C</strong></article>
      <article><ThermometerSun :size="15" /><span>Track</span><strong>{{ weather.track_temp.toFixed(1) }} C</strong></article>
      <article><Droplets :size="15" /><span>Humidity</span><strong>{{ Math.round(weather.humidity) }}%</strong></article>
      <article><Wind :size="15" /><span>Wind</span><strong>{{ weather.wind_speed.toFixed(1) }}</strong><small>km/h</small></article>
    </div>
  </section>
</template>
