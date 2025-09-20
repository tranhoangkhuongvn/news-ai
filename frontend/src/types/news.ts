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