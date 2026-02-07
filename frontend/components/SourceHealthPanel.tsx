'use client';

import type { Lang, RetryMetrics, SourceHealth } from '@/lib/api';

function statusClass(status: SourceHealth['last_status']): string {
  if (status === 'up') return 'text-mint border-mint/40 bg-mint/10';
  if (status === 'degraded') return 'text-amber-300 border-amber-300/40 bg-amber-300/10';
  if (status === 'down') return 'text-red-300 border-red-300/40 bg-red-300/10';
  return 'text-slate-300 border-slate-300/30 bg-slate-300/10';
}

function fmtDate(input: string | null, lang: Lang): string {
  const zhNone = '\u65e0';
  if (!input) return lang === 'zh' ? zhNone : 'N/A';
  return new Intl.DateTimeFormat(lang === 'zh' ? 'zh-CN' : 'en-US', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(input));
}

export function SourceHealthPanel({
  lang,
  items,
  retryMetrics,
}: {
  lang: Lang;
  items: SourceHealth[];
  retryMetrics: RetryMetrics | null;
}) {
  const text = {
    zh: {
      title: '\u6765\u6e90\u5065\u5eb7\u76d1\u63a7',
      retry: '\u91cd\u8bd5\u961f\u5217',
      pending: '\u5f85\u91cd\u8bd5',
      due: '\u5230\u671f\u5f85\u6267\u884c',
      lastCheck: '\u6700\u8fd1\u68c0\u67e5',
      lastSuccess: '\u6700\u8fd1\u6210\u529f',
      latency: '\u5ef6\u8fdf',
      failures: '\u8fde\u7eed\u5931\u8d25',
      error: '\u9519\u8bef',
      empty: '\u6682\u65e0\u6765\u6e90\u5065\u5eb7\u6570\u636e\uff0c\u53ef\u80fd\u4ecd\u5728\u521d\u59cb\u5316\u6216\u6293\u53d6\u4e2d\u3002',
    },
    en: {
      title: 'Source Health Monitor',
      retry: 'Retry Queue',
      pending: 'Pending',
      due: 'Due',
      lastCheck: 'Last Check',
      lastSuccess: 'Last Success',
      latency: 'Latency',
      failures: 'Consecutive Failures',
      error: 'Error',
      empty: 'No source health data yet. Backend may still be initializing or ingesting.',
    },
  }[lang];

  return (
    <div className="mb-8">
      <h2 className="mb-4 text-xl" style={{ fontFamily: 'var(--font-heading)' }}>
        {text.title}
      </h2>
      {retryMetrics ? (
        <div className="mb-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full border border-accent/50 bg-accent/10 px-2 py-1 text-accent">
            {text.retry}
          </span>
          <span className="rounded-full border border-slate-400/40 bg-slate-900/35 px-2 py-1 text-slate-100">
            {text.pending}: {retryMetrics.pending}
          </span>
          <span className="rounded-full border border-slate-400/40 bg-slate-900/35 px-2 py-1 text-slate-100">
            {text.due}: {retryMetrics.due}
          </span>
        </div>
      ) : null}
      {items.length === 0 ? <p className="mb-3 text-xs text-slate-300">{text.empty}</p> : null}
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <article key={item.source_name} className="rounded-xl border border-slate-600/35 bg-slate-900/35 p-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm text-slate-100">{item.source_name}</h3>
              <span className={`rounded-full border px-2 py-0.5 text-xs ${statusClass(item.last_status)}`}>{item.last_status}</span>
            </div>
            <p className="mt-2 text-xs text-slate-300">
              {text.lastCheck}: {fmtDate(item.last_checked_at, lang)}
            </p>
            <p className="mt-1 text-xs text-slate-300">
              {text.lastSuccess}: {fmtDate(item.last_success_at, lang)}
            </p>
            <p className="mt-1 text-xs text-slate-300">
              {text.latency}: {item.last_latency_ms ? `${item.last_latency_ms}ms` : 'N/A'}
            </p>
            <p className="mt-1 text-xs text-slate-300">
              {text.failures}: {item.consecutive_failures}
            </p>
            {item.last_error ? (
              <p className="mt-2 max-h-10 overflow-hidden text-xs text-red-300">
                {text.error}: {item.last_error}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}
