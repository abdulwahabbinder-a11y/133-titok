import fs from "fs";
import path from "path";

const CONFIG_PATH = path.join(process.cwd(), "data", "config.json");

const DEFAULT_CONFIG = {
  googleAnalyticsId: "",
  searchConsoleMeta: "",
  adsTxtContent: "",
  topBannerAdCode: "",
  bottomBannerAdCode: "",
  promoImageUrl: "",
  promoTargetUrl: "",
  tiktokApiKey: "",
  tiktokApiHost: "tiktok-video-no-watermark2.p.rapidapi.com",
  tiktokApiUrl: "https://tiktok-video-no-watermark2.p.rapidapi.com/",
  instagramApiKey: "",
  instagramApiHost: "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com",
  instagramApiUrl:
    "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index",
  facebookApiKey: "",
  facebookApiHost: "facebook-reel-and-video-downloader.p.rapidapi.com",
  facebookApiUrl: "https://facebook-reel-and-video-downloader.p.rapidapi.com/app/main.php",
  adminUsername: "admin",
  adminPassword: "password123",
};

/** In-memory cache with short TTL to avoid repeated disk reads under load. */
let cachedConfig = null;
let cacheTimestamp = 0;
const CACHE_TTL_MS = 3000;

/**
 * Read and parse the localized configuration file.
 * Falls back to safe defaults when keys are missing.
 */
export function getConfig() {
  const now = Date.now();
  if (cachedConfig && now - cacheTimestamp < CACHE_TTL_MS) {
    return cachedConfig;
  }

  try {
    const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
    const parsed = JSON.parse(raw);
    cachedConfig = { ...DEFAULT_CONFIG, ...parsed };
  } catch {
    cachedConfig = { ...DEFAULT_CONFIG };
  }

  cacheTimestamp = now;
  return cachedConfig;
}

/**
 * Persist updated configuration and refresh the in-memory cache instantly.
 */
export function saveConfig(updates) {
  const current = getConfig();
  const merged = { ...current, ...updates };

  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(merged, null, 2), "utf-8");

  cachedConfig = merged;
  cacheTimestamp = Date.now();
  return merged;
}

/** Force-clear cache so the next read pulls fresh data from disk. */
export function invalidateConfigCache() {
  cachedConfig = null;
  cacheTimestamp = 0;
}

/** All string config keys exposed to the admin dashboard. */
export const CONFIG_STRING_FIELDS = [
  "googleAnalyticsId",
  "searchConsoleMeta",
  "adsTxtContent",
  "topBannerAdCode",
  "bottomBannerAdCode",
  "promoImageUrl",
  "promoTargetUrl",
  "tiktokApiKey",
  "tiktokApiHost",
  "tiktokApiUrl",
  "instagramApiKey",
  "instagramApiHost",
  "instagramApiUrl",
  "facebookApiKey",
  "facebookApiHost",
  "facebookApiUrl",
];

/** Build a sanitized config object for the admin API response. */
export function getAdminConfig() {
  const config = getConfig();
  return {
    googleAnalyticsId: config.googleAnalyticsId,
    searchConsoleMeta: config.searchConsoleMeta,
    adsTxtContent: config.adsTxtContent,
    topBannerAdCode: config.topBannerAdCode,
    bottomBannerAdCode: config.bottomBannerAdCode,
    promoImageUrl: config.promoImageUrl,
    promoTargetUrl: config.promoTargetUrl,
    tiktokApiKey: config.tiktokApiKey,
    tiktokApiHost: config.tiktokApiHost,
    tiktokApiUrl: config.tiktokApiUrl,
    instagramApiKey: config.instagramApiKey,
    instagramApiHost: config.instagramApiHost,
    instagramApiUrl: config.instagramApiUrl,
    facebookApiKey: config.facebookApiKey,
    facebookApiHost: config.facebookApiHost,
    facebookApiUrl: config.facebookApiUrl,
    adminUsername: config.adminUsername,
  };
}
