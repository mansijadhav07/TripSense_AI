import type { Metadata } from "next";
import { Suspense } from "react";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "TripSense AI - Big Data Hotel Recommendations",
  description: "Production-grade AI hotel recommendations powered by Apache Spark ML, Collaborative Filtering, and NLP Sentiment Analysis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-slate-950 text-slate-100 antialiased" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col bg-slate-950 text-slate-100" suppressHydrationWarning>
        <AuthProvider>
          <Suspense fallback={<div className="h-16 bg-slate-950 border-b border-slate-800" />}>
            <Navbar />
          </Suspense>
          <main className="flex-1">{children}</main>
          <footer className="border-t border-slate-800/80 bg-slate-950/80 py-8 text-center text-xs text-slate-500">
            <p>© 2026 TripSense AI — Distributed Big Data Recommender System. Apache Spark 3.5 & FastAPI.</p>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
