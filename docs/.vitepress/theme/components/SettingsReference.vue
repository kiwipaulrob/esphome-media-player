<template>
  <section class="settings-reference">
    <section
      v-for="section in sections"
      :key="section.title"
      class="settings-section"
    >
      <h2 :id="section.id">
        {{ section.title }}
        <span v-if="sectionBadge(section)" class="settings-badge">{{ sectionBadge(section) }}</span>
      </h2>

      <p v-if="section.summary">{{ section.summary }}</p>

      <table v-if="section.settings.length">
        <thead>
          <tr>
            <th>Setting</th>
            <th>Description</th>
            <th>Default</th>
            <th>Options</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="setting in section.settings" :key="setting.key">
            <td>
              <strong>{{ setting.docs.label }}</strong>
              <span v-if="setting.docs.badge" class="settings-badge">{{ setting.docs.badge }}</span>
            </td>
            <td>{{ setting.docs.description }}</td>
            <td>{{ defaultText(setting) }}</td>
            <td>{{ optionsText(setting) }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup>
import settingsCatalog from '../../../../product/settings.json'

const settingsWithDocs = settingsCatalog.settings.filter((setting) => setting.docs)
const sectionDefs = settingsCatalog.docs_sections || []
const browserState = settingsCatalog.browser_state || {}

const sections = sectionDefs
  .map((section) => ({
    ...section,
    id: slug(section.title),
    settings: settingsWithDocs
      .filter((setting) => setting.docs.section === section.title)
      .sort((a, b) => a.docs.order - b.docs.order),
  }))
  .filter((section) => section.summary || section.settings.length)

function slug(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function sectionBadge(section) {
  const badges = new Set(section.settings.map((setting) => setting.docs.badge).filter(Boolean))
  return badges.size === 1 ? [...badges][0] : ''
}

function defaultText(setting) {
  if (!Object.prototype.hasOwnProperty.call(setting, 'default')) return '-'
  const value = setting.default
  if (value === '') return 'Blank'
  if (value === true) return 'On'
  if (value === false) return 'Off'
  if (value == null) return '-'
  return formatValue(value, setting)
}

function optionsText(setting) {
  const options = setting.options || browserState[setting.entity?.optionsKey] || []
  if (!options.length) return '-'
  return options.map((option) => formatValue(option, setting)).join(', ')
}

function formatValue(value, setting) {
  if (setting.key === 'track_info_duration' && value === 0) return 'Always'
  if (typeof value === 'number' && setting.limits?.suffix === 's') {
    if (value === 60) return '1 minute'
    return `${value} seconds`
  }
  if (typeof value === 'number' && setting.limits?.suffix === '%') return `${value}%`
  if (typeof value === 'number' && setting.limits?.suffix === 'h') return `${value}:00`
  return String(value)
}
</script>

<style scoped>
.settings-section {
  margin-top: 32px;
}

.settings-section table {
  display: table;
  width: 100%;
}

.settings-section th:first-child {
  width: 22%;
}

.settings-section th:nth-child(3),
.settings-section th:nth-child(4) {
  width: 16%;
}

.settings-badge {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 999px;
  color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
</style>
