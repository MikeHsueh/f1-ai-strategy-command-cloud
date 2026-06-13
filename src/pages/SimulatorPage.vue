<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import PitProbabilityGauge from '../components/PitProbabilityGauge.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import StrategyRecommendation from '../components/StrategyRecommendation.vue'
import TireHealthPanel from '../components/TireHealthPanel.vue'
import WeatherPanel from '../components/WeatherPanel.vue'
import WhatIfSimulator from '../components/WhatIfSimulator.vue'
import { useRaceStore } from '../stores/raceStore'
import { classifyRisk } from '../types'

const store = useRaceStore()
const {
  selection, seasons, races, drivers, laps, raceState, prediction,
  strategyOptions, simulationResult, loading,
} = storeToRefs(store)

onMounted(store.initialize)

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
        allow-initial-override
        @simulate="store.runSimulation"
        @reset="store.resetSimulation"
      />
      <PitProbabilityGauge
        class="simulator-gauge"
        :probability="simulationResult?.pit_probability ?? prediction.pit_probability"
        :risk="simulatedDecision.risk"
        :action="simulatedDecision.action"
      />
      <StrategyRecommendation class="simulator-strategy" :prediction="prediction" :options="strategyOptions" />
      <TireHealthPanel class="simulator-tire" :tire="raceState.tire" />
      <WeatherPanel class="simulator-weather" :weather="raceState.weather" />
    </div>
  </div>
</template>
