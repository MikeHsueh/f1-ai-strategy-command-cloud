<template>
  <div class="panel">
    <h2>🛞 Tire System</h2>

    <div class="tire-box">

      <div class="compound">
        {{ data.compound }}
      </div>

      <div class="life">
        Tire Age:
        <strong>{{ data.life }}</strong>
      </div>

      <div class="deg">
        Degradation:
        <strong :style="{ color: degradationColor }">
          {{ data.degradation }}
        </strong>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: Object
})

const degradationColor = computed(() => {

  if (!props.data?.degradation) return '#fff'

  if (props.data.degradation > 3)
    return '#ef4444'

  if (props.data.degradation > 1.5)
    return '#f59e0b'

  return '#10b981'
})
</script>

<style scoped>
.panel {
  background: #111827;
  padding: 20px;
  border-radius: 12px;
  color: white;
}

.compound {
  font-size: 28px;
  font-weight: bold;
  color: #ef4444;
}

.life,
.deg {
  margin-top: 10px;
}
</style>