<template>
  <details class="source-list" v-if="sources.length">
    <summary>检索来源（{{ sources.length }} 个片段）</summary>
    <div class="source-item" v-for="(s, i) in sources" :key="i">
      <div class="source-content">{{ s.content }}</div>
      <div class="source-path" v-if="s.source">{{ s.source }}</div>
    </div>
  </details>
</template>

<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
});
</script>

<style scoped>
.source-list {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  font-size: 12px;
}
.source-list summary {
  cursor: pointer;
  color: #888;
  margin-bottom: 8px;
}
.source-item {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.source-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}
.source-content {
  color: #333;
  line-height: 1.5;
}
.source-path {
  color: #aaa;
  margin-top: 4px;
  font-size: 11px;
}
</style>
