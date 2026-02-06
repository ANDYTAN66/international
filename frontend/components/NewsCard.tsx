'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';

import type { Lang, NewsItem } from '@/lib/api';

function fmtDate(input: string, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === 'zh' ? 'zh-CN' : 'en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(input));
}

function prettifyTag(tag: string): string {
  return tag
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function NewsCard({ item, lang }: { item: NewsItem; lang: Lang }) {
  const zhChina = '\u4e2d\u56fd\u76f8\u5173';
  const zhOriginal = '\u539f\u59cb\u94fe\u63a5';

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="glass-panel rounded-2xl p-5 shadow-glow"
    >
      <div className="mb-3 flex items-center justify-between text-xs text-slate-300">
        <span>{item.source_name}</span>
        <time dateTime={item.published_at}>{fmtDate(item.published_at, lang)}</time>
      </div>

      <Link href={`/news/${item.id}?lang=${lang}`}>
        <h3
          className="text-xl leading-snug text-ink hover:text-accent"
          style={{ fontFamily: 'var(--font-heading)' }}
        >
          {item.title}
        </h3>
      </Link>

      <p className="mt-3 max-h-24 overflow-hidden text-sm text-slate-200">{item.summary || item.content}</p>

      <div className="mt-3 flex flex-wrap gap-2">
        {(item.country_tags ?? []).slice(0, 2).map((tag) => (
          <span key={tag} className="rounded-full border border-mint/50 bg-mint/10 px-2 py-0.5 text-xs text-mint">
            {prettifyTag(tag)}
          </span>
        ))}
        {(item.topic_tags ?? []).slice(0, 2).map((tag) => (
          <span key={tag} className="rounded-full border border-accent/50 bg-accent/10 px-2 py-0.5 text-xs text-accent">
            {prettifyTag(tag)}
          </span>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-slate-300">
        <span>{item.china_related ? (lang === 'zh' ? zhChina : 'China Focus') : 'Global'}</span>
        <a className="hover:text-mint" href={item.article_url} target="_blank" rel="noreferrer">
          {lang === 'zh' ? zhOriginal : 'Original Link'}
        </a>
      </div>
    </motion.article>
  );
}
