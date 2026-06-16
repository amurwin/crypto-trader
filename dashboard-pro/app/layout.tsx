import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ApolloWrapper } from "../lib/apollo-wrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Crypto Trader — Dashboard Pro",
  description: "Enterprise SSR/GraphQL dashboard for the crypto trading system",
};

const TABS = [
  { href: "/portfolio", label: "Portfolio" },
  { href: "/trades", label: "Trades" },
  { href: "/pnl", label: "P&L" },
  { href: "/chart", label: "Chart" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-900 text-white">
        <ApolloWrapper>
          <header className="border-b border-slate-800">
            <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-8">
              <span className="font-semibold text-lg">Dashboard Pro</span>
              <nav className="flex gap-1">
                {TABS.map((t) => (
                  <Link
                    key={t.href}
                    href={t.href}
                    className="px-3 py-1.5 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                  >
                    {t.label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="max-w-6xl mx-auto px-6 py-6 w-full flex-1">{children}</main>
        </ApolloWrapper>
      </body>
    </html>
  );
}
