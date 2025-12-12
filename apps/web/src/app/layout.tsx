import type { ReactNode } from 'react';
import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'Review UI',
  description: 'Job review UI',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header className="header">
            <Link className="brand" href="/jobs">
              Review UI
            </Link>
            <nav className="nav">
              <Link href="/jobs">Jobs</Link>
              <Link href="/jobs/new">Create job</Link>
            </nav>
          </header>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
