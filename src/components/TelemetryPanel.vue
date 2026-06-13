<template>
  <div class="panel">

    <h2>📡 Telemetry</h2>

    <div class="grid">

      <div class="card">
        <label>Speed</label>
        <h3>{{ data.speed }}</h3>
      </div>

      <div class="card">
        <label>RPM</label>
        <h3>{{ data.rpm }}</h3>
      </div>

      <div class="card">
        <label>Throttle</label>
        <h3>{{ data.throttle }}%</h3>
      </div>

      <div class="card">
        <label>Brake</label>
        <h3>{{ data.brake }}%</h3>
      </div>

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
  background: #0f172a;
  padding: 20px;
  border-radius: 12px;
  color: white;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.card {
  background: #1e293b;
  padding: 15px;
  border-radius: 10px;
  text-align: center;
}

label {
  color: #9ca3af;
  font-size: 12px;
}

h3 {
  font-size: 24px;
  margin-top: 8px;
}
</style>