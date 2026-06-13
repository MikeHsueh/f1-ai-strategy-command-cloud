<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Play, SkipBack, SkipForward } from '@lucide/vue'

import DriverComparisonTable from '../components/DriverComparisonTable.vue'
import PaceTrendChart from '../components/PaceTrendChart.vue'
import PitProbabilityTimeline from '../components/PitProbabilityTimeline.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import RaceStatePanel from '../components/RaceStatePanel.vue'
import { useRaceStore } from '../stores/raceStore'

const store = useRaceStore()
const { selection, seasons, races, drivers, laps, raceState, timeline, paceTrend, comparison, loading } = storeToRefs(store)
const lapIndex = computed(() => Math.max(0, laps.value.indexOf(selection.value.lap)))

function step(direction: number) {
  const next = laps.value[Math.max(0, Math.min(laps.value.length - 1, lapIndex.value + direction))]
  if (next) store.setLap(next)
}

onMounted(store.initialize)
</script>

<template>
  <div class="page replay-page">
    <RaceSelectorBar
      :seasons="seasons" :races="races" :drivers="drivers" :laps="laps"
      :year="selection.year" :round-number="selection.roundNumber" :driver="selection.driver"
      :lap="selection.lap" :loading="loading"
      @year="store.setYear" @race="store.setRace" @driver="store.setDriver"
      @lap="store.setLap" @refresh="store.refreshDashboard"
    />

    <section class="replay-control command-card" data-tour="replay-control">
      <header class="card-heading">
        <div><span class="eyebrow">Historical session</span><h2>Race Replay Control</h2></div>
        <span class="status-chip">LAP {{ selection.lap }}</span>
      </header>
      <div class="replay-scrubber">
        <button class="icon-button" type="button" title="Previous lap" @click="step(-1)"><SkipBack :size="17" /></button>
        <input
          :value="selection.lap"
          type="range"
          :min="laps[0] || 1"
          :max="laps[laps.length - 1] || 52"
          @change="store.setLap(Number(($event.target as HTMLInputElement).value))"
        >
        <button class="icon-button primary" type="button" title="Advance lap" @click="step(1)"><Play :size="17" /></button>
        <button class="icon-button" type="button" title="Next lap" @click="step(1)"><SkipForward :size="17" /></button>
      </div>
    </section>

    <div class="replay-grid">
      <RaceStatePanel :state="raceState" />
      <PitProbabilityTimeline class="replay-timeline" :points="timeline" :current-lap="selection.lap" />
      <PaceTrendChart class="replay-pace" :series="paceTrend" />
      <DriverComparisonTable
        class="replay-table"
        :rows="comparison"
        :selected-driver="selection.driver"
        @select="store.setDriver"
      />
    </div>
  </div>
</template>
