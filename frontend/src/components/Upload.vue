<template>
  <div class="upload-panel">
    <h2>文档上传</h2>
    <div
      class="drop-zone"
      :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="handleDrop"
    >
      <p v-if="!uploading && !error">拖拽 PDF 到此处，或点击选择</p>
      <p v-else-if="uploading">上传中...</p>
      <p v-else class="upload-error">{{ error }}</p>
      <input
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        @change="handleFile"
        :disabled="uploading"
      />
    </div>
    <ul class="doc-list" v-if="documents.length">
      <li v-for="doc in documents" :key="doc.doc_id">
        <div class="doc-info">
          <span class="doc-name">{{ doc.summary || doc.filename }}</span>
          <span class="doc-chunks">{{ doc.chunk_count }} 个片段</span>
        </div>
        <button class="doc-delete" @click="removeDoc(doc.doc_id)" title="删除">×</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { uploadPDF, listDocuments, deleteDocument } from "../api.js";

const dragging = ref(false);
const uploading = ref(false);
const error = ref("");
const documents = ref([]);

onMounted(() => {
  listDocuments().then((res) => {
    if (res.code === 200) documents.value = res.data;
  });
});

async function handleFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  await upload(file);
}

async function handleDrop(e) {
  dragging.value = false;
  const file = e.dataTransfer.files[0];
  if (!file) return;
  await upload(file);
}

async function upload(file) {
  uploading.value = true;
  error.value = "";
  try {
    const res = await uploadPDF(file);
    if (res.code === 200) {
      documents.value.push(res.data);
      emit("uploaded", res.data.doc_id);
    } else {
      error.value = res.detail || "上传失败，请重试";
    }
  } catch (e) {
    error.value = "网络异常，请稍后重试";
  }
  uploading.value = false;
}

async function removeDoc(docId) {
  const res = await deleteDocument(docId);
  if (res.code === 200) {
    documents.value = documents.value.filter((d) => d.doc_id !== docId);
  }
}

const emit = defineEmits(["uploaded"]);
</script>

<style scoped>
.upload-panel {
  padding: 20px;
  border-right: 1px solid #e0e0e0;
  height: 100%;
  overflow-y: auto;
  background: #fff;
}
.upload-panel h2 {
  font-size: 16px;
  margin-bottom: 16px;
}
.drop-zone {
  position: relative;
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}
.drop-zone.dragging {
  border-color: #4a90d9;
  background: #f0f7ff;
}
.drop-zone p {
  margin: 0;
  color: #888;
  pointer-events: none;
}
.upload-error {
  color: #e74c3c !important;
}
.drop-zone input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}
.doc-list {
  list-style: none;
  padding: 0;
  margin-top: 16px;
}
.doc-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #eee;
}
.doc-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}
.doc-chunks {
  font-size: 12px;
  color: #999;
}
.doc-delete {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #ccc;
  font-size: 18px;
  cursor: pointer;
  border-radius: 4px;
  line-height: 1;
  transition: color 0.2s, background 0.2s;
}
.doc-delete:hover {
  color: #e74c3c;
  background: #fce4e4;
}
</style>
