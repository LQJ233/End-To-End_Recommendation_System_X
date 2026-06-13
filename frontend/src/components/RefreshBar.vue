<template>
  <div class="refresh-bar">
    <div class="meta">
      <span>已展示 {{ shown }} / 候选 {{ candidate }}</span>
      <span v-if="requestId">requestId: {{ requestId }}</span>
      <span v-if="modelVersion">model: {{ modelVersion }}</span>
    </div>
    <el-button type="primary" :loading="refreshing" @click="$emit('refresh')">手动刷新</el-button>
  </div>
</template>

<script setup>
defineProps({
  shown: Number, candidate: Number,
  requestId: String, modelVersion: String,
  refreshing: Boolean
})
defineEmits(['refresh'])
</script>

<style scoped>
.refresh-bar { display: flex; align-items: center; justify-content: space-between; padding: 8px 4px 16px; }
.meta { display: flex; gap: 12px; color: #606266; font-size: 13px; }
</style>
