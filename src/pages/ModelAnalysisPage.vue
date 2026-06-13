<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import type { EChartsOption } from 'echarts'

import FeatureImportancePanel from '../components/FeatureImportancePanel.vue'
import ModelHealthPanel from '../components/ModelHealthPanel.vue'
import PanelStatus from '../components/PanelStatus.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import { useEChart } from '../composables/useEChart'
import { useRaceStore } from '../stores/raceStore'

const store = useRaceStore()
const {
  selection, seasons, races, drivers, laps, health, features,
  prediction, loading, lastUpdated, dataSource, panels,
} = storeToRefs(store)

const attentionOptions = computed<EChartsOption>(() => ({
  radar: {
    indicator: prediction.value.attention.map((_, index) => ({ name: `L-${prediction.value.attention.length - index - 1}`, max: 1 })),
    axisName: { color: '#8d9bac', fontSize: 10 },
    splitLine: { lineStyle: { color: '#26313b' } },
    splitArea: { areaStyle: { color: ['rgba(15,22,29,.2)', 'rgba(15,22,29,.5)'] } },
    axisLine: { lineStyle: { color: '#34414e' } },
  },
  series: [{
    type: 'radar',
    data: [{ value: prediction.value.attention, areaStyle: { color: 'rgba(36,199,217,.2)' }, lineStyle: { color: '#24c7d9', width: 2 } }],
  }],
}))
const { chartElement } = useEChart(attentionOptions)

onMounted(() => store.activatePage('model-analysis'))
</script>

<template>
  <div class="page analysis-page">
    <RaceSelectorBar
      :seasons="seasons" :races="races" :drivers="drivers" :laps="laps"
      :year="selection.year" :round-number="selection.roundNumber" :driver="selection.driver"
      :lap="selection.lap" :loading="loading"
      @year="store.setYear" @race="store.setRace" @driver="store.setDriver"
      @lap="store.setLap" @refresh="store.refreshDashboard"
    />

    <div class="model-analysis-grid">
      <FeatureImportancePanel
        class="analysis-features"
        :features="features"
        :limit="14"
        :loading="panels.features.loading"
        :error="panels.features.error"
        @retry="store.loadFeatures"
      />
      <ModelHealthPanel
        :health="health"
        :source="dataSource"
        :last-updated="lastUpdated"
        :loading="panels.health.loading"
        :error="panels.health.error"
        @retry="store.loadHealth"
      />
      <section class="command-card attention-panel" data-tour="attention-distribution">
        <header class="card-heading">
          <div><span class="eyebrow">Temporal explainability</span><h2>Attention Distribution</h2></div>
          <span class="panel-note">Sequence length {{ prediction.attention.length }}</span>
        </header>
        <div ref="chartElement" class="chart attention-chart"></div>
        <PanelStatus
          :loading="panels.prediction.loading"
          :error="panels.prediction.error"
          @retry="store.loadPrediction"
        />
      </section>
      <section class="command-card feature-ledger" data-tour="feature-ledger">
        <header class="card-heading">
          <div><span class="eyebrow">Current inference vector</span><h2>Feature Ledger</h2></div>
          <span class="panel-note">Normalized model inputs</span>
        </header>
        <div class="feature-ledger-grid">
          <article v-for="feature in features" :key="feature.name">
            <span>{{ feature.group }}</span>
            <strong>{{ feature.name }}</strong>
            <b>{{ feature.value.toFixed(3) }}</b>
          </article>
        </div>
        <PanelStatus
          :loading="panels.features.loading"
          :error="panels.features.error"
          @retry="store.loadFeatures"
        />
      </section>
    </div>
  </div>
</template>
