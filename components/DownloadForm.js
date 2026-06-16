"use client";

import { useState } from "react";
import AdSlot from "./AdSlot";

/**
 * Core download interaction — paste URL, fetch metadata, display results.
 */
export default function DownloadForm({ topBannerAdCode, bottomBannerAdCode }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setUrl(text);
    } catch {
      setError("Clipboard access denied. Please paste manually.");
    }
  };

  const handleDownload = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);

    if (!url.trim()) {
      setError("Please paste a TikTok video URL.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong. Please try again.");
        return;
      }

      setResult(data);
    } catch {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      {/* Input + CTA row */}
      <form
        onSubmit={handleDownload}
        className="flex w-full flex-col gap-3 md:flex-row md:items-stretch"
      >
        <div className="relative flex-1">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste TikTok video link here..."
            className="w-full rounded-xl border border-gray-300 bg-white py-4 pl-4 pr-24 text-base text-gray-900 shadow-sm outline-none transition-colors placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            aria-label="TikTok video URL"
          />
          <button
            type="button"
            onClick={handlePaste}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-200"
          >
            Paste
          </button>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-gradient-to-r from-blue-600 to-emerald-500 px-8 py-4 text-base font-semibold text-white shadow-md transition-all hover:from-blue-700 hover:to-emerald-600 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Processing..." : "Download"}
        </button>
      </form>

      {/* Error message */}
      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="mt-6 flex items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white p-8">
          <div className="spinner h-8 w-8 rounded-full border-4 border-gray-200 border-t-blue-600" />
          <span className="text-gray-600">Fetching video data...</span>
        </div>
      )}

      {/* Result box */}
      {result && !loading && (
        <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
            {result.thumbnail && (
              <img
                src={result.thumbnail}
                alt={result.title}
                className="h-32 w-32 shrink-0 rounded-lg object-cover"
                width={128}
                height={128}
                loading="lazy"
              />
            )}
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                {result.title}
              </h3>
              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                {result.mp4 && (
                  <a
                    href={result.mp4}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download Server 1 (MP4)
                  </a>
                )}
                {result.mp3 && (
                  <a
                    href={result.mp3}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-700"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                    </svg>
                    Download Server 2 (MP3/Audio)
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ad Slot 1 — directly below input container */}
      <AdSlot code={topBannerAdCode} className="mt-6" />

      {/* Ad Slot 2 — below results area */}
      <AdSlot code={bottomBannerAdCode} className="mt-6" />
    </div>
  );
}
