<template>
  <div class="chat-panel">
    <h2>{{ title }}</h2>
    <div class="messages" ref="msgBox">
      <div v-if="messages.length === 0" class="empty-hint">
        请先上传 PDF 文档，然后在下方输入问题
      </div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['msg', msg.role]"
      >
        <div class="bubble">{{ msg.content }}</div>
        <SourceList v-if="msg.sources" :sources="msg.sources" />
      </div>
      <div v-if="loading" class="msg assistant">
        <div class="bubble typing">思考中...</div>
      </div>
    </div>
    <form class="input-row" @submit.prevent="send">
      <textarea
        ref="inputEl"
        v-model="question"
        placeholder="输入问题，基于已上传文档提问..."
        :disabled="loading"
        rows="1"
        @input="autoResize"
        @keydown.enter.exact.prevent="send"
      />
      <button type="submit" :disabled="!question.trim() || loading">
        发送
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from "vue";
import { askQuestionStream } from "../api.js";
import SourceList from "./Source.vue";

const props = defineProps({
  title: { type: String, default: "问答" },
  activeDocId: { type: String, default: "" },
});

const question = ref("");
const messages = ref([]);
const loading = ref(false);
const msgBox = ref(null);
const inputEl = ref(null);

let flushTimer = null;
const tokenQueue = [];
const TYPING_INTERVAL = 30;

function flushTokenQueue(aiMsg) {
  if (tokenQueue.length === 0) {
    clearInterval(flushTimer);
    flushTimer = null;
    return;
  }
  aiMsg.content += tokenQueue.shift();
  scrollDown();
}

onBeforeUnmount(() => {
  if (flushTimer) clearInterval(flushTimer);
});

function autoResize() {
  if (!inputEl.value) return;
  inputEl.value.style.height = "auto";
  inputEl.value.style.height = inputEl.value.scrollHeight + "px";
}

async function send() {
  const q = question.value.trim();
  if (!q || loading.value) return;

  messages.value.push({ role: "user", content: q });
  question.value = "";
  if (inputEl.value) {
    inputEl.value.style.height = "auto";
  }
  loading.value = true;

  // 历史消息：当前对话中除最后一条 user + 空 assistant 之外的所有消息
  const history = messages.value.slice(0, -1).map(m => ({ role: m.role, content: m.content }));

  const aiMsg = { role: "assistant", content: "", sources: null };
  messages.value.push(aiMsg);
  await scrollDown();

  await askQuestionStream(
    q,
    3,
    props.activeDocId || "",
    history,
    (token) => {
      tokenQueue.push(token);
      if (!flushTimer) {
        flushTimer = setInterval(() => flushTokenQueue(aiMsg), TYPING_INTERVAL);
      }
    },
    (sources) => {
      aiMsg.sources = sources;
    },
    () => {
      if (flushTimer) {
        clearInterval(flushTimer);
        flushTimer = null;
        // 清空队列残余
        while (tokenQueue.length) {
          aiMsg.content += tokenQueue.shift();
        }
      }
      loading.value = false;
      scrollDown();
    },
    (errMsg) => {
      if (flushTimer) {
        clearInterval(flushTimer);
        flushTimer = null;
        tokenQueue.length = 0;
      }
      aiMsg.content = errMsg;
      loading.value = false;
    }
  );
}

async function scrollDown() {
  await nextTick();
  if (msgBox.value) {
    msgBox.value.scrollTop = msgBox.value.scrollHeight;
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  background: url('../assets/tupian.jpg') center / cover no-repeat;
}
.chat-panel h2 {
  font-size: 16px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 12px;
}
.empty-hint {
  text-align: center;
  color: #aaa;
  font-size: 14px;
  margin-top: 60px;
}
.msg {
  margin-bottom: 12px;
}
.msg.user .bubble {
  background: #4a90d9;
  color: #fff;
  margin-left: auto;
  max-width: 70%;
}
.msg.assistant .bubble {
  background: #f5f5f5;
  max-width: 85%;
}
.bubble {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.bubble.typing {
  color: #999;
}
.input-row {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.input-row textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  overflow-y: auto;
  line-height: 1.4;
}
.input-row button {
  padding: 10px 20px;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.input-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
