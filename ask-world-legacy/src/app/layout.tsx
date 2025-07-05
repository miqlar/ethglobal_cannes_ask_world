// src/app/layout.tsx
'use client';

import { initMiniKit } from '@/lib/minikit';
import { useEffect } from 'react';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    initMiniKit();
  }, []);

  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}