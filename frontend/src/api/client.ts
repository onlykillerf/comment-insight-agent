import type { ClassificationRow, Cluster, CommentItem, DataQuality, Insight, StrategyCard, Task, WordClouds } from "@/types/task";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  listTasks: () => request<Task[]>("/api/tasks"),
  createTask: (payload: Partial<Task> & Record<string, unknown>) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(payload) }),
  runTask: (taskId: number) => request<{ task_id: number; status: string; summary: Record<string, unknown> }>(`/api/tasks/${taskId}/run`, { method: "POST" }),
  getTask: (taskId: number) => request<Task>(`/api/tasks/${taskId}`),
  getQuality: (taskId: number) => request<DataQuality>(`/api/tasks/${taskId}/quality`),
  getComments: (taskId: number) => request<CommentItem[]>(`/api/tasks/${taskId}/comments`),
  getClusters: (taskId: number) => request<Cluster[]>(`/api/tasks/${taskId}/clusters`),
  getWordclouds: (taskId: number) => request<WordClouds>(`/api/tasks/${taskId}/wordclouds`),
  getSentiment: (taskId: number) => request<{ distribution: Record<string, number>; average_score: number }>(`/api/tasks/${taskId}/sentiment`),
  getPainpoints: (taskId: number) => request<ClassificationRow[]>(`/api/tasks/${taskId}/painpoints`),
  getPositiveAttributions: (taskId: number) => request<ClassificationRow[]>(`/api/tasks/${taskId}/positive-attributions`),
  getInsights: (taskId: number) => request<Insight>(`/api/tasks/${taskId}/insights`),
  getStrategyCards: (taskId: number) => request<StrategyCard[]>(`/api/tasks/${taskId}/strategy-cards`),
  markdownUrl: (taskId: number) => `${API_BASE}/api/tasks/${taskId}/report/markdown`
};
