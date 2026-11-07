import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lesson Creation Tool",
  description: "AI-powered lesson creation with research, QC, and export — Kalvium AI Research Intern Task",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}

