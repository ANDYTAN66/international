import type { Metadata } from 'next';
import { Bodoni_Moda, Manrope } from 'next/font/google';

import './globals.css';

const bodoni = Bodoni_Moda({ subsets: ['latin'], variable: '--font-heading' });
const manrope = Manrope({ subsets: ['latin'], variable: '--font-body' });

export const metadata: Metadata = {
  title: 'Global Pulse | Realtime International News',
  description: 'Realtime international news aggregation with source and timestamp transparency.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${bodoni.variable} ${manrope.variable}`}>
      <body style={{ fontFamily: 'var(--font-body)' }}>{children}</body>
    </html>
  );
}
