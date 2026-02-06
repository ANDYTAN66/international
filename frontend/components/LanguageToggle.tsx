'use client';

import type { Lang } from '@/lib/api';

export function LanguageToggle({ lang, onChange }: { lang: Lang; onChange: (lang: Lang) => void }) {
  return (
    <div className="inline-flex overflow-hidden rounded-full border border-slate-500/30 bg-slate-900/35">
      <button
        className={`px-4 py-2 text-sm ${lang === 'en' ? 'bg-accent text-slate-900' : 'text-slate-200'}`}
        onClick={() => onChange('en')}
      >
        English
      </button>
      <button
        className={`px-4 py-2 text-sm ${lang === 'zh' ? 'bg-accent text-slate-900' : 'text-slate-200'}`}
        onClick={() => onChange('zh')}
      >
        中文
      </button>
    </div>
  );
}
