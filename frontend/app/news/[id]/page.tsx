import Link from 'next/link';

import { fetchNewsDetail, type Lang } from '@/lib/api';

function fmtDate(input: string, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === 'zh' ? 'zh-CN' : 'en-US', {
    dateStyle: 'full',
    timeStyle: 'short',
  }).format(new Date(input));
}

function pretty(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export default async function NewsDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ lang?: Lang }>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const lang: Lang = sp.lang === 'zh' ? 'zh' : 'en';
  const item = await fetchNewsDetail(id, lang);

  const zhBack = '\u8fd4\u56de\u9996\u9875';
  const zhLabel = '\u4e2d\u6587';
  const zhOpenSource = '\u67e5\u770b\u539f\u59cb\u94fe\u63a5';

  return (
    <main className="container-shell py-10">
      <article className="glass-panel rounded-3xl p-8 md:p-10">
        <div className="flex items-center justify-between gap-3">
          <Link href={`/?lang=${lang}`} className="text-sm text-mint hover:text-accent">
            {lang === 'zh' ? zhBack : 'Back'}
          </Link>
          <div className="inline-flex overflow-hidden rounded-full border border-slate-500/30 bg-slate-900/35 text-sm">
            <Link
              className={`px-4 py-2 ${lang === 'en' ? 'bg-accent text-slate-900' : 'text-slate-200'}`}
              href={`/news/${id}?lang=en`}
            >
              English
            </Link>
            <Link
              className={`px-4 py-2 ${lang === 'zh' ? 'bg-accent text-slate-900' : 'text-slate-200'}`}
              href={`/news/${id}?lang=zh`}
            >
              {zhLabel}
            </Link>
          </div>
        </div>

        <header className="mt-6 border-b border-slate-500/25 pb-5">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-300">{item.source_name}</p>
          <h1 className="mt-3 text-3xl md:text-5xl" style={{ fontFamily: 'var(--font-heading)' }}>
            {item.title}
          </h1>
          <p className="mt-3 text-sm text-slate-300">{fmtDate(item.published_at, lang)}</p>
          <a href={item.article_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm text-accent">
            {lang === 'zh' ? zhOpenSource : 'Open original source'}
          </a>
          <div className="mt-3 flex flex-wrap gap-2">
            {item.country_tags.map((tag) => (
              <span key={tag} className="rounded-full border border-mint/50 bg-mint/10 px-2 py-0.5 text-xs text-mint">
                {pretty(tag)}
              </span>
            ))}
            {item.topic_tags.map((tag) => (
              <span key={tag} className="rounded-full border border-accent/50 bg-accent/10 px-2 py-0.5 text-xs text-accent">
                {pretty(tag)}
              </span>
            ))}
          </div>
        </header>

        <div className="mt-8 whitespace-pre-wrap text-slate-100 leading-8">{item.content}</div>
      </article>
    </main>
  );
}
