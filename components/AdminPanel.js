"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_PLATFORMS = [
  {
    id: "tiktok",
    label: "TikTok Setup",
    color: "text-pink-600",
    fields: [
      { key: "tiktokApiKey", label: "API Key", placeholder: "RapidAPI key for TikTok" },
      { key: "tiktokApiHost", label: "API Host", placeholder: "tiktok-video-no-watermark2.p.rapidapi.com" },
      { key: "tiktokApiUrl", label: "Base URL", placeholder: "https://tiktok-video-no-watermark2.p.rapidapi.com/" },
    ],
  },
  {
    id: "instagram",
    label: "Instagram Setup",
    color: "text-purple-600",
    fields: [
      { key: "instagramApiKey", label: "API Key", placeholder: "RapidAPI key for Instagram" },
      { key: "instagramApiHost", label: "API Host", placeholder: "instagram-downloader-....rapidapi.com" },
      { key: "instagramApiUrl", label: "Base URL", placeholder: "https://instagram-downloader-..../index" },
    ],
  },
  {
    id: "facebook",
    label: "Facebook Setup",
    color: "text-blue-600",
    fields: [
      { key: "facebookApiKey", label: "API Key", placeholder: "RapidAPI key for Facebook" },
      { key: "facebookApiHost", label: "API Host", placeholder: "facebook-reel-and-video-downloader.p.rapidapi.com" },
      { key: "facebookApiUrl", label: "Base URL", placeholder: "https://facebook-reel-..../app/main.php" },
    ],
  },
];

function Fieldset({ title, children }) {
  return (
    <fieldset className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <legend className="px-2 text-sm font-semibold text-gray-900">{title}</legend>
      {children}
    </fieldset>
  );
}

function TextInput({ id, label, value, onChange, placeholder, type = "text" }) {
  return (
    <div className="mb-4 last:mb-0">
      <label htmlFor={id} className="mb-1 block text-sm text-gray-600">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value || ""}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
      />
    </div>
  );
}

function TextArea({ id, label, value, onChange, placeholder, rows = 5 }) {
  return (
    <div className="mb-4 last:mb-0">
      <label htmlFor={id} className="mb-1 block text-sm text-gray-600">
        {label}
      </label>
      <textarea
        id={id}
        rows={rows}
        value={value || ""}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
      />
    </div>
  );
}

/**
 * Advanced admin dashboard — monetization, API hub, and site configuration.
 */
export function AdminDashboard({ initialConfig }) {
  const [config, setConfig] = useState(initialConfig);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [apiHubOpen, setApiHubOpen] = useState(false);
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
      <div className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-xs text-gray-500">Manage ads, APIs, and site settings</p>
          </div>
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
          {/* SEO & Analytics */}
          <Fieldset title="SEO &amp; Analytics">
            <TextInput
              id="ga-id"
              label="Google Analytics Tracking ID (GA4)"
              value={config.googleAnalyticsId}
              onChange={handleChange("googleAnalyticsId")}
              placeholder="G-XXXXXXXXXX"
            />
            <TextInput
              id="sc-meta"
              label="Google Search Console Verification String"
              value={config.searchConsoleMeta}
              onChange={handleChange("searchConsoleMeta")}
              placeholder="verification_token_here"
            />
            <TextArea
              id="ads-txt"
              label="ads.txt Plain Content"
              value={config.adsTxtContent}
              onChange={handleChange("adsTxtContent")}
              placeholder="google.com, pub-XXXXXXXX, DIRECT, f08c47fec0942fa0"
              rows={4}
            />
          </Fieldset>

          {/* Monetization */}
          <Fieldset title="Monetization">
            <TextArea
              id="top-ad"
              label="Top AdSense Banner (HTML/JS)"
              value={config.topBannerAdCode}
              onChange={handleChange("topBannerAdCode")}
              placeholder="<!-- Paste top banner AdSense code -->"
            />
            <TextArea
              id="bottom-ad"
              label="Bottom AdSense Banner (HTML/JS)"
              value={config.bottomBannerAdCode}
              onChange={handleChange("bottomBannerAdCode")}
              placeholder="<!-- Paste bottom banner AdSense code -->"
            />

            <div className="mt-2 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-800">Custom Promotional Ad</h3>
              <TextInput
                id="promo-image"
                label="Promo Image URL"
                value={config.promoImageUrl}
                onChange={handleChange("promoImageUrl")}
                placeholder="https://example.com/banner.png"
              />
              <TextInput
                id="promo-link"
                label="Promo Target Link"
                value={config.promoTargetUrl}
                onChange={handleChange("promoTargetUrl")}
                placeholder="https://example.com/offer"
              />
            </div>
          </Fieldset>

          {/* Dynamic API Hub */}
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <button
              type="button"
              onClick={() => setApiHubOpen((prev) => !prev)}
              className="flex w-full items-center justify-between px-6 py-4 text-left transition-colors hover:bg-gray-50"
              aria-expanded={apiHubOpen}
            >
              <span className="text-sm font-semibold text-gray-900">Configure Platform APIs</span>
              <svg
                className={`h-5 w-5 text-gray-500 transition-transform duration-300 ${apiHubOpen ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div
              className={`grid transition-all duration-300 ease-in-out ${
                apiHubOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
              }`}
            >
              <div className="overflow-hidden">
                <div className="space-y-4 border-t border-gray-200 px-6 pb-6 pt-4">
                  {API_PLATFORMS.map((platform) => (
                    <div
                      key={platform.id}
                      className="rounded-lg border border-gray-200 bg-gray-50 p-4"
                    >
                      <h4 className={`mb-3 text-sm font-semibold ${platform.color}`}>
                        {platform.label}
                      </h4>
                      {platform.fields.map((field) => (
                        <TextInput
                          key={field.key}
                          id={field.key}
                          label={field.label}
                          value={config[field.key]}
                          onChange={handleChange(field.key)}
                          placeholder={field.placeholder}
                        />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Admin Credentials */}
          <Fieldset title="Admin Credentials">
            <p className="mb-3 text-xs text-gray-400">
              Leave password blank to keep the current password unchanged.
            </p>
            <TextInput
              id="admin-user"
              label="Username"
              value={config.adminUsername}
              onChange={handleChange("adminUsername")}
            />
            <TextInput
              id="admin-pass"
              label="New Password"
              type="password"
              value={config.adminPassword || ""}
              onChange={handleChange("adminPassword")}
              placeholder="••••••••"
            />
          </Fieldset>

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
            className="w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save Configurations"}
          </button>
        </form>
      </div>
    </div>
  );
}
