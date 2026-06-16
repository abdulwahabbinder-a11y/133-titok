import Script from "next/script";
import { getConfig } from "@/lib/config";
import "./globals.css";

export const metadata = {
  title: "TikTok Video Downloader Without Watermark – Free MP4 & MP3",
  description:
    "Download TikTok videos in high-quality MP4 or MP3 format for free. No watermark, no login required. Fast, secure, and unlimited downloads.",
  keywords: [
    "tiktok downloader",
    "tiktok video download",
    "download tiktok without watermark",
    "tiktok mp3",
    "tiktok mp4",
  ],
  robots: "index, follow",
  openGraph: {
    title: "TikTok Video Downloader Without Watermark",
    description:
      "Download TikTok videos in high-quality MP4 or MP3 format for free.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  const { googleAnalyticsId, searchConsoleMeta } = getConfig();

  return (
    <html lang="en">
      <head>
        {/* Google Search Console verification meta tag */}
        {searchConsoleMeta && (
          <meta name="google-site-verification" content={searchConsoleMeta} />
        )}
      </head>
      <body className="min-h-screen antialiased">
        {children}

        {/* Google Analytics GA4 — loaded after page becomes interactive */}
        {googleAnalyticsId && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${googleAnalyticsId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${googleAnalyticsId}');
              `}
            </Script>
          </>
        )}
      </body>
    </html>
  );
}
