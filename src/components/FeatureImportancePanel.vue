<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useEChart } from '../composables/useEChart'
import type { FeatureItem } from '../types'
import PanelStatus from './PanelStatus.vue'

const props = defineProps<{
  features: FeatureItem[]
  limit?: number
  loading?: boolean
  error?: string
}>()

defineEmits<{ retry: [] }>()

const shown = computed(() => [...props.features]
  .sort((a, b) => b.importance - a.importance)
  .slice(0, props.limit ?? 10))

const options = computed<EChartsOption>(() => ({
  animationDuration: 350,
  grid: { top: 8, left: 118, right: 28, bottom: 22 },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: '#090e13',
    borderColor: '#34414e',
    textStyle: { color: '#f1f5f9', fontSize: 12 },
  },
  xAxis: {
    type: 'value',
    axisLabel: { color: '#8998a8', fontSize: 10, formatter: (value: number) => `${Math.round(value * 100)}%` },
    splitLine: { lineStyle: { color: '#1d2730' } },
  },
  yAxis: {
    type: 'category',
    inverse: true,
    data: shown.value.map((feature) => feature.name),
    axisLabel: { color: '#b8c3ce', fontSize: 10, width: 108, overflow: 'truncate' },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [{
    type: 'bar',
    data: shown.value.map((feature, index) => ({
      value: feature.importance,
      itemStyle: { color: index < 3 ? '#24c7d9' : '#3c5465' },
    })),
    barWidth: 8,
    itemStyle: { borderRadius: [0, 4, 4, 0] },
  }],
}))

const { chartElement } = useEChart(options)
</script>

<template>
  <section class="command-card feature-panel" data-tour="feature-importance">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Explainability</span>
        <h2>Feature Importance</h2>
      </div>
      <span class="panel-note">{{ features.length }} active features</span>
    </header>
    <div ref="chartElement" class="chart feature-chart"></div>
    <PanelStatus :loading="loading" :error="error" @retry="$emit('retry')" />
  </section>
</template>
