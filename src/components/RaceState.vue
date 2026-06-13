<template>
  <div class="panel">
    <h2>🏁 Race State</h2>

    <div class="item">
      <span>Current Lap</span>
      <strong>{{ data.lap }}</strong>
    </div>

    <div class="item">
      <span>Position</span>
      <strong>P{{ data.position }}</strong>
    </div>

    <div class="item">
      <span>Gap Ahead</span>
      <strong>{{ data.gap_ahead }} s</strong>
    </div>

    <div class="item">
      <span>Gap Behind</span>
      <strong>{{ data.gap_behind }} s</strong>
    </div>

    <div class="item">
      <span>Safety Car</span>
      <strong :class="data.safety_car ? 'red' : 'green'">
        {{ data.safety_car ? 'DEPLOYED' : 'CLEAR' }}
      </strong>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: Object
})
</script>

<style scoped>
.panel {
  background: #1f2937;
  padding: 20px;
  border-radius: 12px;
  color: white;
}

.item {
  display: flex;
  justify-content: space-between;
  margin: 12px 0;
}

.red {
  color: #ef4444;
}

.green {
  color: #10b981;
}
</style>