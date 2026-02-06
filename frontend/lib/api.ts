export type Lang = 'en' | 'zh';

export type NewsItem = {
  id: number;
  source_name: string;
  source_url: string;
  article_url: string;
  title: string;
  summary: string;
  content: string;
  language: Lang;
  published_at: string;
  fetched_at: string;
  china_related: boolean;
  image_url: string | null;
  country_tags: string[];
  topic_tags: string[];
};

type NewsListResponse = {
  total: number;
  items: NewsItem[];
};

type RawNewsItem = Partial<NewsItem> & {
  id: number;
  title: string;
};

function normalizeNewsItem(raw: RawNewsItem): NewsItem {
  return {
    id: raw.id,
    source_name: raw.source_name ?? 'Unknown Source',
    source_url: raw.source_url ?? '',
    article_url: raw.article_url ?? '',
    title: raw.title ?? '',
    summary: raw.summary ?? '',
    content: raw.content ?? '',
    language: raw.language === 'zh' ? 'zh' : 'en',
    published_at: raw.published_at ?? new Date().toISOString(),
    fetched_at: raw.fetched_at ?? new Date().toISOString(),
    china_related: Boolean(raw.china_related),
    image_url: raw.image_url ?? null,
    country_tags: Array.isArray(raw.country_tags) ? raw.country_tags : [],
    topic_tags: Array.isArray(raw.topic_tags) ? raw.topic_tags : [],
  };
}

export type SourceHealth = {
  source_name: string;
  feed_url: string;
  last_status: 'up' | 'degraded' | 'down' | 'unknown';
  consecutive_failures: number;
  last_error: string | null;
  last_latency_ms: number | null;
  last_items_count: number;
  last_checked_at: string;
  last_success_at: string | null;
};

type SourceHealthResponse = {
  items: SourceHealth[];
};

export type FilterOptions = {
  countries: string[];
  topics: string[];
};

export type RetryMetrics = {
  pending: number;
  due: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchNews(params: {
  lang: Lang;
  chinaOnly: boolean;
  q?: string;
  country?: string;
  topic?: string;
  limit?: number;
  offset?: number;
}): Promise<NewsListResponse> {
  const qp = new URLSearchParams({
    lang: params.lang,
    china_only: String(params.chinaOnly),
    limit: String(params.limit ?? 30),
    offset: String(params.offset ?? 0),
  });
  if (params.q?.trim()) {
    qp.set('q', params.q.trim());
  }
  if (params.country?.trim()) {
    qp.set('country', params.country.trim());
  }
  if (params.topic?.trim()) {
    qp.set('topic', params.topic.trim());
  }

  const resp = await fetch(`${API_BASE}/api/news?${qp.toString()}`, { next: { revalidate: 0 } });
  if (!resp.ok) {
    throw new Error(`Failed to fetch news: ${resp.status}`);
  }
  const data = await resp.json();
  return {
    total: Number(data.total ?? 0),
    items: Array.isArray(data.items) ? data.items.map((item: RawNewsItem) => normalizeNewsItem(item)) : [],
  };
}

export async function fetchNewsDetail(id: string, lang: Lang): Promise<NewsItem> {
  const resp = await fetch(`${API_BASE}/api/news/${id}?lang=${lang}`, { next: { revalidate: 0 } });
  if (!resp.ok) {
    throw new Error(`Failed to fetch detail: ${resp.status}`);
  }
  const data: RawNewsItem = await resp.json();
  return normalizeNewsItem(data);
}

export async function fetchSourceHealth(): Promise<SourceHealth[]> {
  const resp = await fetch(`${API_BASE}/api/sources/health`, { next: { revalidate: 0 } });
  if (!resp.ok) {
    throw new Error(`Failed to fetch source health: ${resp.status}`);
  }
  const data: SourceHealthResponse = await resp.json();
  return data.items;
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const resp = await fetch(`${API_BASE}/api/filters`, { next: { revalidate: 60 } });
  if (!resp.ok) {
    throw new Error(`Failed to fetch filters: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchRetryMetrics(): Promise<RetryMetrics> {
  const resp = await fetch(`${API_BASE}/api/retry/metrics`, { next: { revalidate: 0 } });
  if (!resp.ok) {
    throw new Error(`Failed to fetch retry metrics: ${resp.status}`);
  }
  return resp.json();
}

export function getWsUrl(): string {
  return API_BASE.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/news';
}
