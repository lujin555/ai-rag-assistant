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
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK, doc_id: docId, history }),
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

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
        else if (data.type === "error") onError(data.data);
        else if (data.type === "done") onDone();
      } catch (e) {
        // 跳过解析错误的行
      }
    }
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
