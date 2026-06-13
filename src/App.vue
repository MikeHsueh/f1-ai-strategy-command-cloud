<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Activity,
  ChartNoAxesCombined,
  CircleHelp,
  FlaskConical,
  Gauge,
  Radio,
} from '@lucide/vue'

import { useOnboardingTour } from './composables/useOnboardingTour'
import { useRaceStore } from './stores/raceStore'

const store = useRaceStore()
const {
  selectedRace,
  selection,
  prediction,
  dataSource,
  health,
  loading,
  error,
  panels,
} = storeToRefs(store)
const { startTour, startTourIfNeeded } = useOnboardingTour()

onMounted(async () => {
  await store.initialize()
  if (!error.value && !panels.value.raceState.error && !panels.value.prediction.error) {
    await startTourIfNeeded()
  }
})
</script>

<template>
  <div class="app-shell">
    <header class="top-command-bar" data-tour="app-welcome">
      <RouterLink class="brand-lockup" to="/">
        <span class="f1-mark">F1</span>
        <div>
          <small>Physics-informed BiLSTM</small>
          <strong>AI Strategy Command</strong>
        </div>
      </RouterLink>

      <nav class="primary-nav" aria-label="Primary">
        <RouterLink to="/" title="Dashboard"><Gauge :size="17" /><span>Dashboard</span></RouterLink>
        <RouterLink to="/replay" title="Replay"><ChartNoAxesCombined :size="17" /><span>Replay</span></RouterLink>
        <RouterLink to="/simulator" title="Simulator"><FlaskConical :size="17" /><span>Simulator</span></RouterLink>
        <RouterLink to="/model-analysis" title="Model Analysis"><Activity :size="17" /><span>Model</span></RouterLink>
      </nav>

      <div class="command-status">
        <div>
          <span>Session</span>
          <strong>R{{ selectedRace?.round || selection.roundNumber }} {{ selectedRace?.short || '---' }} · L{{ selection.lap }}</strong>
        </div>
        <div>
          <span>Driver</span>
          <strong>{{ selection.driver }} · {{ Math.round(prediction.pit_probability * 100) }}% PIT</strong>
        </div>
        <div>
          <span>Model</span>
          <strong>{{ health.model.weights_loaded ? 'READY' : 'STANDBY' }}</strong>
        </div>
        <span class="live-indicator" :class="{ mock: dataSource === 'mock', busy: loading }">
          <Radio :size="13" />
          {{ loading ? 'SYNCING' : dataSource === 'api' ? 'LIVE' : 'MOCK' }}
        </span>
        <button
          class="guide-button"
          data-tour="tour-replay"
          type="button"
          title="Replay onboarding tour"
          aria-label="Replay onboarding tour"
          @click="startTour(true)"
        >
          <CircleHelp :size="17" />
        </button>
      </div>
    </header>

    <div v-if="error" class="global-error">{{ error }}</div>
    <main class="app-content">
      <RouterView />
    </main>
  </div>
</template>
