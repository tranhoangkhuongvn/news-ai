import type { NewsArticle, DashboardData, NewsSource } from '../types/news';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API response interfaces that match backend
interface APIResponse<T> {
  data?: T;
  error?: string;
}

interface ExtractionRequest {
  sources?: string[];
  categories?: string[];
  max_articles?: number;
}

interface ExtractionResponse {
  success: boolean;
  message: string;
  total_articles: number;
  successful_saves: number;
  failed_saves: number;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
  extraction_time: number;
  errors: string[];
}

class NewsAPI {
  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<APIResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error(`API Error for ${url}:`, error);
      return { error: error instanceof Error ? error.message : 'Unknown error occurred' };
    }
  }

  /**
   * Test API connectivity
   */
  async healthCheck(): Promise<APIResponse<{ status: string }>> {
    return this.fetchWithErrorHandling('/health');
  }

  /**
   * Get all articles with optional filtering
   */
  async getArticles(params?: {
    category?: string;
    source?: string;
    limit?: number;
  }): Promise<APIResponse<NewsArticle[]>> {
    const searchParams = new URLSearchParams();

    if (params?.category) searchParams.append('category', params.category);
    if (params?.source) searchParams.append('source', params.source);
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const url = `/articles${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.fetchWithErrorHandling<NewsArticle[]>(url);
  }

  /**
   * Get dashboard data (top articles, categories, sources)
   */
  async getDashboardData(): Promise<APIResponse<DashboardData>> {
    return this.fetchWithErrorHandling<DashboardData>('/dashboard');
  }

  /**
   * Get available news sources
   */
  async getSources(): Promise<APIResponse<{ sources: NewsSource[] }>> {
    return this.fetchWithErrorHandling('/sources');
  }

  /**
   * Get available categories
   */
  async getCategories(): Promise<APIResponse<{ categories: Array<{ category: string; label: string; color: string }> }>> {
    return this.fetchWithErrorHandling('/categories');
  }

  /**
   * Trigger news extraction from sources
   */
  async extractNews(request: ExtractionRequest): Promise<APIResponse<ExtractionResponse>> {
    return this.fetchWithErrorHandling<ExtractionResponse>('/extract', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get latest articles by extracting fresh news
   */
  async getLatestArticles(params?: {
    sources?: string[];
    categories?: string[];
    max_articles?: number;
  }): Promise<APIResponse<NewsArticle[]>> {
    const searchParams = new URLSearchParams();

    if (params?.sources) {
      params.sources.forEach(source => searchParams.append('sources', source));
    }
    if (params?.categories) {
      params.categories.forEach(category => searchParams.append('categories', category));
    }
    if (params?.max_articles) {
      searchParams.append('max_articles', params.max_articles.toString());
    }

    const url = `/articles/latest${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.fetchWithErrorHandling<NewsArticle[]>(url);
  }
}

// Export singleton instance
export const newsAPI = new NewsAPI();

// Export types for use in components
export type { ExtractionRequest, ExtractionResponse, APIResponse };