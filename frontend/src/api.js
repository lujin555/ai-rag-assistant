const BASE_URL = "/api";

export async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function askQuestion(question, topK = 3) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
  return res.json();
}

export async function askQuestionStream(question, topK, docId, history, onToken, onSources, onDone, onError) {
  let res;
  try {
    res = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK, doc_id: docId, history }),
    });
  } catch (e) {
    // 连请求都没发出去（后端没启动 / 断网）
    onError("网络请求失败，请检查后端是否启动");
    onDone();
    return;
  }

  if (!res.ok) {
    // 后端返回了错误状态码
    let detail = `HTTP ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch {}
    onError("请求失败: " + detail);
    onDone();
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;   // 是否收到过 done 事件

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === "token") onToken(data.data);
          else if (data.type === "sources") onSources(data.data);
          else if (data.type === "error") { onError(data.data); finished = true; }
          else if (data.type === "done") { onDone(); finished = true; }
        } catch (e) {
          // 跳过解析错误的行
        }
      }
    }
  } catch (e) {
    // 读流中途出错（网络断开 / 服务器崩溃）
    onError("网络中断，回答未完成");
    onDone();
    return;
  }

  // 流正常结束了，但一直没收到 done（服务器没发完就关了连接）
  if (!finished) {
    onError("回答未完成：连接提前结束");
    onDone();
  }
}

export async function listDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/documents/${docId}`, {
    method: "DELETE",
  });
  return res.json();
}
