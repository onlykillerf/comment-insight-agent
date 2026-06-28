import type {
  ABTestDraft,
  ClassificationRow,
  Cluster,
  CommentItem,
  DataQuality,
  Insight,
  StrategyCard,
  Task,
  TaskStatus,
  UploadedDataset,
  WordClouds
} from "@/types/task";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    const text = await response.text();
    let detail = "";
    try {
      const payload = JSON.parse(text) as { detail?: string | { msg?: string }[] };
      detail = Array.isArray(payload.detail)
        ? payload.detail.map((item) => item.msg || "参数错误").join("；")
        : payload.detail || "";
    } catch {
      detail = "";
    }
    throw new Error(detail || text || `请求失败（${response.status}）`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  listTasks: () => request<Task[]>("/api/tasks"),
  createTask: (payload: Partial<Task> & Record<string, unknown>) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(payload) }),
  createDemo: (scenario: "basketball" | "football") =>
    request<Task>(`/api/demos/${scenario}`, { method: "POST" }),
  runTask: (taskId: number) =>
    request<{ task_id: number; status: string; summary: Record<string, unknown> }>(`/api/tasks/${taskId}/run`, { method: "POST" }),
  cancelTask: (taskId: number) =>
    request<{ task_id: number; status: string }>(`/api/tasks/${taskId}/cancel`, { method: "POST" }),
  retryTask: (taskId: number) =>
    request<{ task_id: number; status: string }>(`/api/tasks/${taskId}/retry`, { method: "POST" }),
  getTask: (taskId: number) => request<Task>(`/api/tasks/${taskId}`),
  getTaskStatus: (taskId: number) => request<TaskStatus>(`/api/tasks/${taskId}/status`),
  uploadDataset: (file: File, sourceKind: "csv" | "json" | "mediacrawler") => {
    const body = new FormData();
    body.append("file", file);
    body.append("source_kind", sourceKind);
    return request<UploadedDataset>("/api/uploads", { method: "POST", body });
  },
  updateUploadMapping: (uploadId: string, fieldMapping: Record<string, string>) =>
    request<UploadedDataset>(`/api/uploads/${uploadId}/mapping`, {
      method: "PATCH",
      body: JSON.stringify({ field_mapping: fieldMapping })
    }),
  getQuality: (taskId: number) => request<DataQuality>(`/api/tasks/${taskId}/quality`),
  getComments: (taskId: number) => request<CommentItem[]>(`/api/tasks/${taskId}/comments`),
  getClusters: (taskId: number) => request<Cluster[]>(`/api/tasks/${taskId}/clusters`),
  getWordclouds: (taskId: number) => request<WordClouds>(`/api/tasks/${taskId}/wordclouds`),
  getSentiment: (taskId: number) => request<{ distribution: Record<string, number>; average_score: number }>(`/api/tasks/${taskId}/sentiment`),
  getPainpoints: (taskId: number) => request<ClassificationRow[]>(`/api/tasks/${taskId}/painpoints`),
  getPositiveAttributions: (taskId: number) => request<ClassificationRow[]>(`/api/tasks/${taskId}/positive-attributions`),
  getInsights: (taskId: number) => request<Insight>(`/api/tasks/${taskId}/insights`),
  getStrategyCards: (taskId: number) => request<StrategyCard[]>(`/api/tasks/${taskId}/strategy-cards`),
  createABTestDraft: (cardId: number) =>
    request<ABTestDraft>(`/api/strategy-cards/${cardId}/ab-test-drafts`, { method: "POST" }),
  mediaUrl: (url: string) =>
    url.includes(".hoopchina.com.cn/") ? `${API_BASE}/api/media/proxy?url=${encodeURIComponent(url)}` : url,
  markdownUrl: (taskId: number) => `${API_BASE}/api/tasks/${taskId}/report/markdown`,
  strategyCardExportUrl: (cardId: number) => `${API_BASE}/api/strategy-cards/${cardId}/export`
};
