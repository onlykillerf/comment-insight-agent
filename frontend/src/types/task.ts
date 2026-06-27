export type AgentProgress = {
  status: "pending" | "running" | "completed" | "error" | string;
  duration_ms?: number | null;
  error?: string;
  input_summary?: string;
  output_summary?: string;
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
  enable_image_analysis: boolean;
  max_image_comments: number;
  data_source: string;
  source_path?: string | null;
  status: string;
  progress: Record<string, AgentProgress | string>;
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
};

export type ClassificationRow = {
  category: string;
  count: number;
  ratio: number;
  examples: string[];
};
