export type AgentProgress = {
  status: "pending" | "running" | "completed" | "error" | string;
  duration_ms?: number | null;
  error?: string;
  input_summary?: string;
  output_summary?: string;
};

export type TaskStatus = {
  task_id: number;
  status: string;
  progress: Record<string, AgentProgress | string>;
  error_message: string;
  cancel_requested: boolean;
  run_attempt: number;
  queued_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
};

export type Task = {
  id: number;
  name: string;
  domain: string;
  platforms: string[];
  board: string;
  match_name: string;
  home_team: string;
  away_team: string;
  match_stage: string;
  match_date: string;
  thread_urls: string[];
  news_urls: string[];
  news_context: string;
  keywords: string[];
  semantic_query: string;
  time_range: Record<string, unknown>;
  max_comments: number;
  similarity_threshold: number;
  language: string;
  sentiment_focus: string;
  enable_llm: boolean;
  llm_mode: "mock" | "configured" | string;
  enable_image_analysis: boolean;
  max_image_comments: number;
  data_source: string;
  source_path?: string | null;
  upload_id?: string | null;
  field_mapping: Record<string, string>;
  status: string;
  progress: Record<string, AgentProgress | string>;
  error_message: string;
  cancel_requested: boolean;
  run_attempt: number;
  queued_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type CommentItem = {
  id: number;
  raw_comment_id: string;
  platform: string;
  content: string;
  cleaned_content: string;
  language: string;
  quality_score: number;
  is_duplicate: boolean;
  like_count: number;
  sentiment_label?: string | null;
  sentiment_score?: number | null;
  painpoint?: string | null;
  positive_attribution?: string | null;
  representative_reason?: string | null;
  cluster_id?: number | null;
  image_urls: string[];
  image_analysis: {
    status?: string;
    model?: string;
    summary?: string;
    ocr_text?: string;
    entities?: string[];
    relevance?: string;
    sentiment_cue?: string;
    error?: string;
  };
};

export type Cluster = {
  cluster_id: number;
  cluster_name: string;
  cluster_size: number;
  cluster_ratio: number;
  top_keywords: string[];
  sentiment_distribution: Record<string, number>;
  method: string;
  is_noise: boolean;
  representative_comments: string[];
};

export type DataQuality = {
  raw_count: number;
  clean_count: number;
  dedup_count: number;
  duplicate_ratio: number;
  noise_ratio: number;
  language_distribution: Record<string, number>;
  sample_confidence_level: "high" | "medium" | "low" | string;
  warning: string;
};

export type WordCloudItem = {
  word: string;
  weight: number;
};

export type WordClouds = {
  all_words: WordCloudItem[];
  positive_words: WordCloudItem[];
  negative_words: WordCloudItem[];
  explanations: Record<string, string>;
};

export type Insight = {
  summary: string;
  positive_insights: string[];
  negative_insights: string[];
  key_viewpoints: string[];
  controversies: string[];
  news_context_summary: string;
  context_alignment: string[];
  fact_opinion_gaps: string[];
  risks: string[];
  context_media: ContextMedia[];
};

export type ContextMedia = {
  source_id: string;
  source_kind: "hupu_thread" | "news" | string;
  title: string;
  text_context: string;
  source_url: string;
  image_urls: string[];
  authority_level: "official" | "official_reference" | "editorial" | "community_data" | string;
  information_score: number;
  selection_reasons: string[];
  status: string;
  model?: string;
  summary?: string;
  ocr_text?: string;
  entities?: string[];
  data_points?: string[];
  relevance?: string;
  information_value?: string;
  confidence?: string;
  included_in_summary: boolean;
  exclusion_reason?: string;
  error?: string;
};

export type ClassificationRow = {
  category: string;
  count: number;
  ratio: number;
  examples: string[];
};

export type UploadedDataset = {
  id: string;
  original_name: string;
  source_kind: "csv" | "json" | "mediacrawler" | string;
  file_format: string;
  size_bytes: number;
  row_count: number;
  columns: string[];
  preview_rows: Record<string, unknown>[];
  field_mapping: Record<string, string>;
  validation_errors: string[];
  status: "ready" | "needs_mapping" | string;
  created_at: string;
};

export type StrategyEvidence = {
  comment_id: string;
  content: string;
  source_url?: string;
  like_count?: number;
};

export type StrategyCard = {
  id: number;
  task_id: number;
  title: string;
  card_type: string;
  evidence_comment_ids: string[];
  evidence_comments: StrategyEvidence[];
  evidence_count: number;
  sample_size: number;
  affected_ratio: number;
  confidence: string;
  confidence_reason: string;
  suggested_actions: string[];
  expected_impact: string;
  ab_test_design: Record<string, unknown>;
  created_at: string;
};

export type ABTestDraft = {
  id: number;
  task_id: number;
  strategy_card_id: number;
  name: string;
  hypothesis: string;
  control: string;
  variant: string;
  primary_metric: string;
  guardrail_metrics: string[];
  sample_size_note: string;
  status: string;
  created_at: string;
};
