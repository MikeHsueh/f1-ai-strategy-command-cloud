<script setup lang="ts">
import { RefreshCw } from '@lucide/vue'
import type { Driver, Race, Season } from '../types'

defineProps<{
  seasons: Season[]
  races: Race[]
  drivers: Driver[]
  laps: number[]
  year: number
  roundNumber: number
  driver: string
  lap: number
  loading: boolean
}>()

const emit = defineEmits<{
  year: [value: number]
  race: [value: number]
  driver: [value: string]
  lap: [value: number]
  refresh: []
}>()
</script>

<template>
  <section class="selector-bar">
    <label>
      <span>Season</span>
      <select :value="year" @change="emit('year', Number(($event.target as HTMLSelectElement).value))">
        <option v-for="season in seasons" :key="season.year" :value="season.year">{{ season.year }}</option>
      </select>
    </label>
    <label class="race-select">
      <span>Grand Prix</span>
      <select :value="roundNumber" @change="emit('race', Number(($event.target as HTMLSelectElement).value))">
        <option v-for="race in races" :key="race.round" :value="race.round">R{{ race.round }} · {{ race.label }}</option>
      </select>
    </label>
    <label data-tour="driver-selector">
      <span>Driver</span>
      <select :value="driver" @change="emit('driver', ($event.target as HTMLSelectElement).value)">
        <option v-for="item in drivers" :key="item.code" :value="item.code">
          {{ item.code }} — {{ item.team }} — {{ item.name }}
        </option>
      </select>
    </label>
    <label>
      <span>Lap</span>
      <select :value="lap" @change="emit('lap', Number(($event.target as HTMLSelectElement).value))">
        <option v-for="item in laps" :key="item" :value="item">Lap {{ item }}</option>
      </select>
    </label>
    <button class="icon-button" type="button" title="Refresh dashboard" :disabled="loading" @click="emit('refresh')">
      <RefreshCw :size="17" :class="{ spin: loading }" />
    </button>
  </section>
</template>
