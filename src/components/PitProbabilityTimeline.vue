<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useEChart } from '../composables/useEChart'
import type { TimelinePoint } from '../types'
import PanelStatus from './PanelStatus.vue'

const props = defineProps<{
  points: TimelinePoint[]
  currentLap: number
  loading?: boolean
  error?: string
}>()

defineEmits<{ retry: [] }>()

const options = computed<EChartsOption>(() => ({
  animationDuration: 350,
  grid: { top: 18, left: 42, right: 18, bottom: 32 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#090e13',
    borderColor: '#34414e',
    textStyle: { color: '#f1f5f9', fontSize: 12 },
    valueFormatter: (value) => `${Math.round(Number(value) * 100)}%`,
  },
  xAxis: {
    type: 'category',
    data: props.points.map((point) => point.lap),
    axisLine: { lineStyle: { color: '#2b3742' } },
    axisLabel: { color: '#8998a8', fontSize: 10 },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 1,
    axisLabel: { color: '#8998a8', fontSize: 10, formatter: (value: number) => `${Math.round(value * 100)}%` },
    splitLine: { lineStyle: { color: '#1d2730' } },
  },
  series: [
    {
      name: 'Pit probability',
      type: 'line',
      smooth: 0.3,
      showSymbol: false,
      data: props.points.map((point) => point.probability),
      lineStyle: { color: '#24c7d9', width: 3 },
      areaStyle: { color: 'rgba(36, 199, 217, .12)' },
      markArea: {
        silent: true,
        data: [
          [{ yAxis: 0.35, itemStyle: { color: 'rgba(244,196,48,.04)' } }, { yAxis: 0.65 }],
          [{ yAxis: 0.65, itemStyle: { color: 'rgba(255,122,26,.06)' } }, { yAxis: 0.85 }],
          [{ yAxis: 0.85, itemStyle: { color: 'rgba(255,36,56,.08)' } }, { yAxis: 1 }],
        ],
      },
      markLine: {
        silent: true,
        symbol: 'none',
        data: [
          { xAxis: props.currentLap, lineStyle: { color: '#ffffff', type: 'dashed' }, label: { formatter: 'NOW', color: '#ffffff' } },
          { yAxis: 0.65, lineStyle: { color: '#ff7a1a', type: 'dotted' }, label: { show: false } },
          { yAxis: 0.85, lineStyle: { color: '#ff2438', type: 'dotted' }, label: { show: false } },
        ],
      },
    },
    {
      name: 'Actual pit',
      type: 'scatter',
      symbolSize: 9,
      data: props.points.filter((point) => point.actual_pit).map((point) => [point.lap, point.probability]),
      itemStyle: { color: '#f4c430' },
    },
  ],
}))

const { chartElement } = useEChart(options)
</script>

<template>
  <section class="command-card timeline-panel" data-tour="pit-timeline">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Race horizon</span>
        <h2>Pit Probability Timeline</h2>
      </div>
      <span class="panel-note">Yellow dot = recorded stop</span>
    </header>
    <div ref="chartElement" class="chart timeline-chart"></div>
    <PanelStatus :loading="loading" :error="error" @retry="$emit('retry')" />
  </section>
</template>
