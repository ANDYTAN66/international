import { NewsFeed } from '@/components/NewsFeed';
import type { Lang } from '@/lib/api';

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ lang?: Lang; china?: string; q?: string; country?: string; topic?: string }>;
}) {
  const sp = await searchParams;
  const initialLang: Lang = sp.lang === 'zh' ? 'zh' : 'en';
  return (
    <NewsFeed
      initialLang={initialLang}
      initialChinaOnly={sp.china === '1'}
      initialQ={sp.q ?? ''}
      initialCountry={sp.country ?? ''}
      initialTopic={sp.topic ?? ''}
    />
  );
}
