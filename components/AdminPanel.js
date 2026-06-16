"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

/**
 * Configuration dashboard for managing ads, analytics, and credentials.
 */
export function AdminDashboard({ initialConfig }) {
  const [config, setConfig] = useState(initialConfig);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();

  useEffect(() => {
    fetch("/api/admin/config")
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) setConfig(data);
      })
      .catch(() => {});
  }, []);

  const handleChange = (field) => (e) => {
    setConfig((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");

    try {
      const res = await fetch("/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.error || "Save failed.");
        return;
      }

      setMessage("Configuration saved successfully.");
      router.refresh();
    } catch {
      setMessage("Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/admin/logout";
    document.body.appendChild(form);
    form.submit();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <h1 className="text-lg font-bold text-gray-900">Site Configuration</h1>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-50"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-4 py-8">
        <form onSubmit={handleSave} className="space-y-6">
          {/* Google Analytics */}
          <fieldset className="rounded-xl border border-gray-200 bg-white p-6">
            <legend className="px-2 text-sm font-semibold text-gray-900">
              Google Analytics (GA4)
            </legend>
            <label htmlFor="ga-id" className="mb-1 mt-3 block text-sm text-gray-600">
              Tracking ID (e.g. G-XXXXXXXXXX)
            </label>
            <input
              id="ga-id"
              type="text"
              value={config.googleAnalyticsId}
              onChange={handleChange("googleAnalyticsId")}
              placeholder="G-XXXXXXXXXX"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </fieldset>

          {/* Search Console */}
          <fieldset className="rounded-xl border border-gray-200 bg-white p-6">
            <legend className="px-2 text-sm font-semibold text-gray-900">
              Google Search Console
            </legend>
            <label htmlFor="sc-meta" className="mb-1 mt-3 block text-sm text-gray-600">
              Verification content string
            </label>
            <input
              id="sc-meta"
              type="text"
              value={config.searchConsoleMeta}
              onChange={handleChange("searchConsoleMeta")}
              placeholder="verification_token_here"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </fieldset>

          {/* ads.txt */}
          <fieldset className="rounded-xl border border-gray-200 bg-white p-6">
            <legend className="px-2 text-sm font-semibold text-gray-900">ads.txt</legend>
            <label htmlFor="ads-txt" className="mb-1 mt-3 block text-sm text-gray-600">
              Plain-text ads.txt content
            </label>
            <textarea
              id="ads-txt"
              rows={6}
              value={config.adsTxtContent}
              onChange={handleChange("adsTxtContent")}
              placeholder="google.com, pub-XXXXXXXX, DIRECT, f08c47fec0942fa0"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </fieldset>

          {/* Ad codes */}
          <fieldset className="rounded-xl border border-gray-200 bg-white p-6">
            <legend className="px-2 text-sm font-semibold text-gray-900">Ad Placements</legend>

            <label htmlFor="top-ad" className="mb-1 mt-3 block text-sm text-gray-600">
              Top Banner Ad Code (HTML/JS)
            </label>
            <textarea
              id="top-ad"
              rows={5}
              value={config.topBannerAdCode}
              onChange={handleChange("topBannerAdCode")}
              placeholder="<!-- Paste AdSense or ad network code here -->"
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />

            <label htmlFor="bottom-ad" className="mb-1 block text-sm text-gray-600">
              Bottom Banner Ad Code (HTML/JS)
            </label>
            <textarea
              id="bottom-ad"
              rows={5}
              value={config.bottomBannerAdCode}
              onChange={handleChange("bottomBannerAdCode")}
              placeholder="<!-- Paste AdSense or ad network code here -->"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </fieldset>

          {/* Credentials */}
          <fieldset className="rounded-xl border border-gray-200 bg-white p-6">
            <legend className="px-2 text-sm font-semibold text-gray-900">
              Admin Credentials
            </legend>
            <p className="mt-2 text-xs text-gray-400">
              Leave password blank to keep the current password unchanged.
            </p>

            <label htmlFor="admin-user" className="mb-1 mt-3 block text-sm text-gray-600">
              Username
            </label>
            <input
              id="admin-user"
              type="text"
              value={config.adminUsername || ""}
              onChange={handleChange("adminUsername")}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />

            <label htmlFor="admin-pass" className="mb-1 block text-sm text-gray-600">
              New Password
            </label>
            <input
              id="admin-pass"
              type="password"
              value={config.adminPassword || ""}
              onChange={handleChange("adminPassword")}
              placeholder="••••••••"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </fieldset>

          {message && (
            <p
              className={`rounded-lg px-4 py-3 text-sm ${
                message.includes("success")
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save Configuration"}
          </button>
        </form>
      </div>
    </div>
  );
}
