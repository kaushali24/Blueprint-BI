import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import React from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { BusinessProvider } from "@/providers/BusinessProvider";
import AppShell from "@/components/layout/AppShell";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  preload: true,
  display: "swap",
});

export const metadata: Metadata = {
  title: "ChatInsights",
  description: "ChatInsights Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased bg-ci-background text-ci-on-background`}>
        <NuqsAdapter>
          <BusinessProvider>
            <AppShell>{children}</AppShell>
            <Toaster />
          </BusinessProvider>
        </NuqsAdapter>
      </body>
    </html>
  );
}
