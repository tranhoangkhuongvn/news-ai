export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: NewsCategory;
  source: string;
  author?: string;
  publishedAt: string;
  imageUrl?: string;
  url: string;
  highlights: string[];
}

export interface NewsSource {
  id: string;
  name: string;
  url: string;
  logo?: string;
}

export type NewsCategory = 'music' | 'lifestyle' | 'finance' | 'sports';

export interface CategoryFilterItem {
  category: NewsCategory;
  label: string;
  color: string;
}

export interface DashboardData {
  topArticles: NewsArticle[];
  categories: {
    [K in NewsCategory]: NewsArticle[];
  };
  sources: NewsSource[];
}

// Enhanced prioritized story types for the new intelligent feature
export interface PrioritizedStory {
  story_id: string;
  main_article_id: number;
  title: string;
  summary: string;
  category: NewsCategory;
  sources: string[];
  article_count: number;
  latest_published: string;
  first_published: string;
  priority_level: 'BREAKING' | 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  breaking_news_score: number;
  coverage_score: number;
  quality_score: number;
  time_description: string;
  coverage_description: string;
  is_breaking: boolean;
  similar_articles: NewsArticle[];
  representative_article: NewsArticle;
  urgency_keywords: string[];
  geographic_scope: string;
}

export interface EnhancedExtractionMetrics {
  total_articles_extracted: number;
  similar_pairs_found: number;
  clusters_created: number;
  stories_prioritized: number;
  top_stories_selected: number;
}

export interface EnhancedExtractionSummary {
  expected_articles: number;
  extraction_rate: number;
  sources_processed: number;
  categories_processed: number;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
}

export interface EnhancedExtractionResponse {
  success: boolean;
  message: string;
  processing_time: number;
  top_stories: PrioritizedStory[];
  metrics: EnhancedExtractionMetrics;
  extraction_summary: EnhancedExtractionSummary;
  similarity_summary: {
    total_comparisons: number;
    similarity_rate: number;
    average_similarity_score: number;
  };
  prioritization_summary: {
    total_stories_analyzed: number;
    average_priority_score: number;
    priority_distribution: Record<string, number>;
  };
}