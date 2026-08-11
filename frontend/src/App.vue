<template>
  <div class="app-layout">
    <aside class="sidebar">
      <Upload @uploaded="onUploaded" />
    </aside>
    <main class="main">
      <Chat ref="chatRef" :title="chatTitle" :activeDocId="activeDocId" />
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Upload from "./components/Upload.vue";
import Chat from "./components/Chat.vue";

const chatTitle = ref("RAG 文档问答");
const activeDocId = ref("");
const chatRef = ref(null);

function onUploaded(docId) {
  activeDocId.value = docId;
  chatTitle.value = "文档已就绪，开始提问吧";
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body, #app {
  height: 100%;
  font-family: "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.app-layout {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 280px;
  flex-shrink: 0;
}
.main {
  flex: 1;
  overflow: hidden;
}
</style>
