"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

/**
 * Credential gate shown when the admin session is not active.
 */
export function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Login failed.");
        return;
      }

      // Hard redirect ensures the server reads the new session cookie
      window.location.assign("/admin-portal");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gray-900">
            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Admin Portal</h1>
          <p className="mt-1 text-sm text-gray-500">Sign in to manage site configuration</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              required
              autoComplete="username"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gray-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-gray-800 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

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

  const handleLogout = async () => {
    await fetch("/api/admin/logout", { method: "POST", credentials: "same-origin" });
    window.location.assign("/admin-portal");
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
