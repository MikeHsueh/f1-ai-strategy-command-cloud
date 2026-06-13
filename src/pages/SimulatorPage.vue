<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AsyncPanelPlaceholder from '../components/AsyncPanelPlaceholder.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import StrategyRecommendation from '../components/StrategyRecommendation.vue'
import TireHealthPanel from '../components/TireHealthPanel.vue'
import WeatherPanel from '../components/WeatherPanel.vue'
import WhatIfSimulator from '../components/WhatIfSimulator.vue'
import { useRaceStore } from '../stores/raceStore'
import { classifyRisk } from '../types'

const PitProbabilityGauge = defineAsyncComponent({
  loader: () => import('../components/PitProbabilityGauge.vue'),
  loadingComponent: AsyncPanelPlaceholder,
  delay: 0,
})

const store = useRaceStore()
const {
  selection, seasons, races, drivers, laps, raceState, prediction,
  strategyOptions, simulationResult, loading, panels,
} = storeToRefs(store)

onMounted(() => store.activatePage('simulator'))

const simulatedDecision = computed(() =>
  classifyRisk(simulationResult.value?.pit_probability ?? prediction.value.pit_probability),
)
</script>

<template>
  <div class="page simulator-page">
    <RaceSelectorBar
      :seasons="seasons" :races="races" :drivers="drivers" :laps="laps"
      :year="selection.year" :round-number="selection.roundNumber" :driver="selection.driver"
      :lap="selection.lap" :loading="loading"
      @year="store.setYear" @race="store.setRace" @driver="store.setDriver"
      @lap="store.setLap" @refresh="store.refreshDashboard"
    />

    <div class="simulator-page-grid">
      <WhatIfSimulator
        class="simulator-workbench"
        :race-state="raceState"
        :result="simulationResult"
        :request-error="panels.simulation.error"
        allow-initial-override
        @simulate="store.runSimulation"
        @reset="store.resetSimulation"
      />
      <PitProbabilityGauge
        class="simulator-gauge"
        :probability="simulationResult?.pit_probability ?? prediction.pit_probability"
        :risk="simulatedDecision.risk"
        :action="simulatedDecision.action"
        :loading="panels.prediction.loading"
        :error="panels.prediction.error"
        @retry="store.loadPrediction"
      />
      <StrategyRecommendation
        class="simulator-strategy"
        :prediction="prediction"
        :options="strategyOptions"
        :loading="panels.prediction.loading"
        :error="panels.prediction.error"
        @retry="store.loadPrediction"
      />
      <TireHealthPanel
        class="simulator-tire"
        :tire="raceState.tire"
        :loading="panels.raceState.loading"
        :error="panels.raceState.error"
        @retry="store.loadRaceState"
      />
      <WeatherPanel
        class="simulator-weather"
        :weather="raceState.weather"
        :loading="panels.raceState.loading"
        :error="panels.raceState.error"
        @retry="store.loadRaceState"
      />
    </div>
  </div>
</template>
