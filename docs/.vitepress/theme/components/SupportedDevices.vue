<template>
  <table v-if="mode === 'release'" class="supported-devices-table">
    <thead>
      <tr>
        <th>Device</th>
        <th>Release asset prefix</th>
        <th>Public firmware path</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="device in devices" :key="device.web_slug">
        <td>{{ device.display.name }}</td>
        <td><code>{{ device.asset_slug }}</code></td>
        <td><code>firmware/{{ device.web_slug }}/</code></td>
      </tr>
    </tbody>
  </table>

  <ul v-else class="supported-devices-list">
    <li v-for="device in devices" :key="device.web_slug">
      <a :href="withBase(device.docs_path)">{{ device.display.name }}</a>
      <span> - {{ device.display.size }}, {{ dimensions(device) }}, {{ layoutLabel(device) }}</span>
    </li>
  </ul>
</template>

<script setup>
import { computed } from 'vue'
import { withBase } from 'vitepress'
import deviceCatalog from '../../../../product/devices.json'

defineProps({
  mode: { type: String, default: 'list' },
})

const devices = computed(() => [...deviceCatalog.devices].sort((a, b) => a.docs.order - b.docs.order))

function dimensions(device) {
  const width = Number(device.display.width)
  const height = Number(device.display.height)
  if (layoutLabel(device) === 'landscape') return `${Math.max(width, height)} x ${Math.min(width, height)}`
  if (layoutLabel(device) === 'portrait') return `${Math.min(width, height)} x ${Math.max(width, height)}`
  return `${width} x ${height}`
}

function layoutLabel(device) {
  if (String(device.display.layout || '').startsWith('landscape')) return 'landscape'
  if (String(device.display.layout || '').startsWith('portrait')) return 'portrait'
  return device.display.shape === 'square' ? 'square' : device.display.shape
}
</script>

<style scoped>
.supported-devices-table {
  display: table;
  width: 100%;
}

.supported-devices-list {
  padding-left: 1.25rem;
}
</style>
