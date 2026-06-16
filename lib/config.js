import fs from "fs";
import path from "path";

const CONFIG_PATH = path.join(process.cwd(), "data", "config.json");

const DEFAULT_CONFIG = {
  googleAnalyticsId: "",
  searchConsoleMeta: "",
  adsTxtContent: "",
  topBannerAdCode: "",
  bottomBannerAdCode: "",
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
