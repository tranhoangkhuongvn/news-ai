import { useState, useEffect, useCallback } from 'react';
import { newsAPI } from '../services/api';
import type { NewsArticle, DashboardData, NewsSource, EnhancedExtractionResponse } from '../types/news';

interface UseNewsAPIState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook for fetching dashboard data
 */
export function useDashboardData(): UseNewsAPIState<DashboardData> {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.getDashboardData();

    if (response.error) {
      setError(response.error);
      setData(null);
    } else if (response.data) {
      setData(response.data);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for fetching articles with filtering
 */
export function useArticles(params?: {
  category?: string;
  source?: string;
  limit?: number;
}): UseNewsAPIState<NewsArticle[]> {
  const [data, setData] = useState<NewsArticle[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.getArticles(params);

    if (response.error) {
      setError(response.error);
      setData(null);
    } else if (response.data) {
      setData(response.data);
    }

    setLoading(false);
  }, [params?.category, params?.source, params?.limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for fetching news sources
 */
export function useNewsSources(): UseNewsAPIState<NewsSource[]> {
  const [data, setData] = useState<NewsSource[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.getSources();

    if (response.error) {
      setError(response.error);
      setData(null);
    } else if (response.data) {
      setData(response.data.sources);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for extracting latest news
 */
export function useLatestNews() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractLatest = useCallback(async (params?: {
    sources?: string[];
    categories?: string[];
    max_articles?: number;
  }): Promise<NewsArticle[] | null> => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.getLatestArticles(params);

    setLoading(false);

    if (response.error) {
      setError(response.error);
      return null;
    }

    return response.data || null;
  }, []);

  return {
    extractLatest,
    loading,
    error,
  };
}

/**
 * Hook for triggering news extraction
 */
export function useNewsExtraction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractNews = useCallback(async (params?: {
    sources?: string[];
    categories?: string[];
    max_articles?: number;
  }) => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.extractNews({
      sources: params?.sources || ['abc', 'guardian', 'smh', 'news_com_au'],
      categories: params?.categories || ['sports', 'finance', 'lifestyle', 'music'],
      max_articles: params?.max_articles || 20,
    });

    setLoading(false);

    if (response.error) {
      setError(response.error);
      return null;
    }

    return response.data;
  }, []);

  return {
    extractNews,
    loading,
    error,
  };
}

/**
 * Hook for enhanced news extraction with intelligent prioritization
 */
export function useEnhancedNewsExtraction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<EnhancedExtractionResponse | null>(null);
  const [progress, setProgress] = useState<{
    phase: 'extraction' | 'similarity' | 'prioritization' | 'complete';
    message: string;
  } | null>(null);

  const extractEnhancedNews = useCallback(async (params?: {
    sources?: string[];
    categories?: string[];
    articles_per_category?: number;
  }): Promise<EnhancedExtractionResponse | null> => {
    setLoading(true);
    setError(null);
    setData(null);

    // Show progress updates
    setProgress({ phase: 'extraction', message: 'Extracting articles from news sources...' });

    try {
      const response = await newsAPI.getEnhancedLatestArticles(params);

      if (response.error) {
        setError(response.error);
        setProgress(null);
        setLoading(false);
        return null;
      }

      if (response.data) {
        setData(response.data);
        setProgress({ phase: 'complete', message: 'Enhanced extraction completed successfully!' });

        // Clear progress after a short delay
        setTimeout(() => setProgress(null), 3000);

        setLoading(false);
        return response.data;
      }

      setLoading(false);
      return null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setProgress(null);
      setLoading(false);
      return null;
    }
  }, []);

  const clearResults = useCallback(() => {
    setData(null);
    setError(null);
    setProgress(null);
  }, []);

  return {
    extractEnhancedNews,
    loading,
    error,
    data,
    progress,
    clearResults,
  };
}

/**
 * Hook for enhanced pipeline status monitoring
 */
export function useEnhancedPipelineStatus() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    setLoading(true);
    setError(null);

    const response = await newsAPI.getEnhancedPipelineStatus();

    if (response.error) {
      setError(response.error);
      setStatus(null);
    } else if (response.data) {
      setStatus(response.data);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return {
    status,
    loading,
    error,
    checkStatus,
  };
}

/**
 * Hook for API health check
 */
export function useAPIHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    const response = await newsAPI.healthCheck();
    setIsHealthy(!response.error);
    setLoading(false);
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return {
    isHealthy,
    loading,
    checkHealth,
  };
}