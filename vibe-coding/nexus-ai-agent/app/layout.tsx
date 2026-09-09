import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { NexusProvider } from "../components/providers/NexusProvider";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "NEXUS — AI Chat Beyond Limits", template: "%s | NEXUS" },
  description: "NEXUS is an AI companion interface for creators, learners, builders, and curious minds.",
  alternates: { canonical: "/" },
  openGraph: { title: "NEXUS — AI Chat Beyond Limits", description: "A dark, technical AI companion interface for curious minds.", url: siteUrl, siteName: "NEXUS", images: [{ url: "/nexus-og.png", width: 1200, height: 630, alt: "NEXUS AI" }], type: "website" },
  twitter: { card: "summary_large_image", title: "NEXUS — AI Chat Beyond Limits", description: "A dark, technical AI companion interface for curious minds.", images: ["/nexus-og.png"] },
  icons: { icon: "/icon.svg" },
  robots: { index: true, follow: true },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "name": "NEXUS", "url": siteUrl ?? "/", "logo": "/icon.svg" },
    { "@type": "WebSite", "name": "NEXUS", "url": siteUrl ?? "/", "description": "AI companion interface for creators, learners, builders, and curious minds." },
    { "@type": "SoftwareApplication", "name": "NEXUS AI", "applicationCategory": "ProductivityApplication", "operatingSystem": "Web", "description": "An AI companion for conversation, coding, learning, and productive work." }
  ]
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="en"><body><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} /><NexusProvider>{children}</NexusProvider></body></html>;
}
