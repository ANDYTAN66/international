'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

import {
  fetchFilterOptions,
  fetchNews,
  fetchRetryMetrics,
  fetchSourceHealth,
  getWsUrl,
  type FilterOptions,
  type Lang,
  type NewsItem,
  type RetryMetrics,
  type SourceHealth,
} from '@/lib/api';
import { LanguageToggle } from './LanguageToggle';
import { NewsCard } from './NewsCard';
import { SourceHealthPanel } from './SourceHealthPanel';

type NewsFeedProps = {
  initialLang: Lang;
  initialChinaOnly: boolean;
  initialQ: string;
  initialCountry: string;
  initialTopic: string;
};

function pretty(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function NewsFeed({ initialLang, initialChinaOnly, initialQ, initialCountry, initialTopic }: NewsFeedProps) {
  const router = useRouter();

  const [lang, setLang] = useState<Lang>(initialLang);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [health, setHealth] = useState<SourceHealth[]>([]);
  const [retryMetrics, setRetryMetrics] = useState<RetryMetrics | null>(null);
  const [chinaOnly, setChinaOnly] = useState(initialChinaOnly);
  const [keywordInput, setKeywordInput] = useState(initialQ);
  const [keyword, setKeyword] = useState(initialQ);
  const [country, setCountry] = useState(initialCountry);
  const [topic, setTopic] = useState(initialTopic);
  const [options, setOptions] = useState<FilterOptions>({ countries: [], topics: [] });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function loadCurrent(current: {
    lang: Lang;
    chinaOnly: boolean;
    keyword: string;
    country: string;
    topic: string;
  }) {
    try {
      setErr(null);
      const [newsResp, healthResp, retryResp] = await Promise.all([
        fetchNews({
          lang: current.lang,
          chinaOnly: current.chinaOnly,
          q: current.keyword,
          country: current.country,
          topic: current.topic,
        }),
        fetchSourceHealth(),
        fetchRetryMetrics(),
      ]);
      setNews(newsResp.items);
      setHealth(healthResp);
      setRetryMetrics(retryResp);
    } catch (error) {
      setErr(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      try {
        setOptions(await fetchFilterOptions());
      } catch {
        setOptions({ countries: [], topics: [] });
      }
    })();
  }, []);

  useEffect(() => {
    setLoading(true);
    const current = { lang, chinaOnly, keyword, country, topic };
    void loadCurrent(current);

    const qp = new URLSearchParams({ lang });
    if (chinaOnly) qp.set('china', '1');
    if (keyword) qp.set('q', keyword);
    if (country) qp.set('country', country);
    if (topic) qp.set('topic', topic);
    router.replace(`/?${qp.toString()}`, { scroll: false });
  }, [lang, chinaOnly, keyword, country, topic, router]);

  useEffect(() => {
    const wsUrl = getWsUrl();
    if (!wsUrl) return;

    if (typeof window !== 'undefined' && window.location.protocol === 'https:' && wsUrl.startsWith('ws://')) {
      return;
    }

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
    } catch {
      return;
    }

    ws.onmessage = () => void loadCurrent({ lang, chinaOnly, keyword, country, topic });

    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 20000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [lang, chinaOnly, keyword, country, topic]);

  const chinaItems = useMemo(() => news.filter((item) => item.china_related), [news]);

  const i18n = {
    zh: {
      desc: '\u5b9e\u65f6\u805a\u5408\u56fd\u9645\u8d44\u8baf\uff0c\u652f\u6301\u5168\u6587\u9605\u8bfb\u3001\u68c0\u7d22\u4e0e\u7b5b\u9009\u3002',
      chinaOnly: '\u4ec5\u770b\u4e2d\u56fd\u76f8\u5173',
      search: '\u5173\u952e\u8bcd\u641c\u7d22',
      allCountries: '\u5168\u90e8\u56fd\u5bb6',
      allTopics: '\u5168\u90e8\u4e3b\u9898',
      apply: '\u5e94\u7528\u641c\u7d22',
      reset: '\u91cd\u7f6e\u7b5b\u9009',
      chinaSection: '\u4e2d\u56fd\u76f8\u5173\u4e13\u680f',
      latest: '\u6700\u65b0\u56fd\u9645\u8d44\u8baf',
    },
    en: {
      desc: 'Realtime international aggregation with source transparency, full-text reading, and advanced filters.',
      chinaOnly: 'China Focus Only',
      search: 'Search keywords',
      allCountries: 'All Countries',
      allTopics: 'All Topics',
      apply: 'Apply Search',
      reset: 'Reset Filters',
      chinaSection: 'China Focus',
      latest: 'Latest International Headlines',
    },
  }[lang];

  return (
    <main className="container-shell py-10 md:py-14">
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="glass-panel rounded-3xl p-8 md:p-10"
      >
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mint">Realtime Intelligence Desk</p>
            <h1 className="text-4xl md:text-6xl" style={{ fontFamily: 'var(--font-heading)' }}>
              Global Pulse
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-300 md:text-base">{i18n.desc}</p>
          </div>

          <div className="flex items-center gap-3">
            <LanguageToggle lang={lang} onChange={setLang} />
            <button
              className={`rounded-full border px-4 py-2 text-sm ${
                chinaOnly ? 'border-accent bg-accent text-slate-900' : 'border-slate-500/30 bg-slate-800/40 text-slate-100'
              }`}
              onClick={() => setChinaOnly((v) => !v)}
            >
              {i18n.chinaOnly}
            </button>
          </div>
        </div>

        <div className="mb-8 grid gap-3 rounded-2xl border border-slate-500/30 bg-slate-900/35 p-4 md:grid-cols-5">
          <input
            className="rounded-lg border border-slate-500/40 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 outline-none focus:border-mint"
            placeholder={i18n.search}
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') setKeyword(keywordInput.trim());
            }}
          />
          <select
            className="rounded-lg border border-slate-500/40 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 outline-none focus:border-mint"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          >
            <option value="">{i18n.allCountries}</option>
            {options.countries.map((entry) => (
              <option key={entry} value={entry}>
                {pretty(entry)}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-500/40 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 outline-none focus:border-mint"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          >
            <option value="">{i18n.allTopics}</option>
            {options.topics.map((entry) => (
              <option key={entry} value={entry}>
                {pretty(entry)}
              </option>
            ))}
          </select>
          <button
            className="rounded-lg border border-accent/60 bg-accent/85 px-3 py-2 text-sm text-slate-900 hover:bg-accent"
            onClick={() => setKeyword(keywordInput.trim())}
          >
            {i18n.apply}
          </button>
          <button
            className="rounded-lg border border-slate-500/40 bg-slate-800/60 px-3 py-2 text-sm text-slate-100 hover:border-mint"
            onClick={() => {
              setKeywordInput('');
              setKeyword('');
              setCountry('');
              setTopic('');
              setChinaOnly(false);
            }}
          >
            {i18n.reset}
          </button>
        </div>

        {err ? <p className="mb-5 text-sm text-red-300">{err}</p> : null}

        <SourceHealthPanel lang={lang} items={health} retryMetrics={retryMetrics} />

        <div className="mb-8">
          <h2 className="mb-4 text-xl" style={{ fontFamily: 'var(--font-heading)' }}>
            {i18n.chinaSection}
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {chinaItems.slice(0, 4).map((item) => (
              <NewsCard key={`china-${item.id}`} item={item} lang={lang} />
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-4 text-xl" style={{ fontFamily: 'var(--font-heading)' }}>
            {i18n.latest}
          </h2>
          {loading ? <p className="text-sm text-slate-300">Loading...</p> : null}
          <div className="grid gap-4 md:grid-cols-2">
            {news.map((item) => (
              <NewsCard key={item.id} item={item} lang={lang} />
            ))}
          </div>
        </div>
      </motion.section>
    </main>
  );
}
