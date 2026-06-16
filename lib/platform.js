const PLATFORM_PATTERNS = {
  tiktok:
    /^https?:\/\/(?:(?:www|vm|vt)\.)?tiktok\.com\/(?:@[\w.-]+\/video\/\d+|[\w@./-]+|t\/[\w-]+)/i,
  instagram:
    /^https?:\/\/(?:(?:www|m)\.)?instagram\.com\/(?:p|reel|reels|tv|stories)\/[\w.-]+/i,
  facebook:
    /^https?:\/\/(?:(?:www|m|web)\.)?(?:facebook\.com|fb\.watch|fb\.com)\/(?:watch\/?\?v=\d+|[\w.-]+\/(?:videos|posts|reel|reels)\/[\w.-]+|reel\/\d+|share\/[rv]\/[\w]+|[\w.-]+\/videos\/\d+|\d+|[\w.-]+)/i,
};

/** Normalize user input to a clean HTTPS URL string. */
export function normalizeUrl(input) {
  let url = input.trim();
  if (!/^https?:\/\//i.test(url)) {
    url = `https://${url}`;
  }
  return url;
}

/**
 * Detect which social platform a URL belongs to.
 * Returns 'tiktok' | 'instagram' | 'facebook' | null
 */
export function detectPlatform(input) {
  if (!input || typeof input !== "string") return null;

  const url = normalizeUrl(input);

  if (PLATFORM_PATTERNS.tiktok.test(url)) return "tiktok";
  if (PLATFORM_PATTERNS.instagram.test(url)) return "instagram";
  if (PLATFORM_PATTERNS.facebook.test(url)) return "facebook";

  return null;
}

/** Validate that the input is a supported social media URL. */
export function isValidSocialUrl(input) {
  return detectPlatform(input) !== null;
}

/**
 * Resolve isolated API credentials for the detected platform from config.
 * Falls back to legacy env vars for TikTok when config keys are empty.
 */
export function getPlatformCredentials(platform, config) {
  const map = {
    tiktok: {
      apiKey: config.tiktokApiKey || process.env.RAPIDAPI_KEY || "",
      apiHost: config.tiktokApiHost || process.env.RAPIDAPI_HOST || "",
      apiUrl: config.tiktokApiUrl || "",
    },
    instagram: {
      apiKey: config.instagramApiKey || "",
      apiHost: config.instagramApiHost || "",
      apiUrl: config.instagramApiUrl || "",
    },
    facebook: {
      apiKey: config.facebookApiKey || "",
      apiHost: config.facebookApiHost || "",
      apiUrl: config.facebookApiUrl || "",
    },
  };

  return map[platform] || null;
}

/** Build the final request URL from config (apiUrl or derived from host). */
export function resolveApiEndpoint(apiUrl, apiHost) {
  if (apiUrl?.trim()) return apiUrl.trim();
  if (apiHost?.trim()) return `https://${apiHost.replace(/^https?:\/\//, "")}/`;
  return "";
}

/** Normalize heterogeneous API responses into a uniform client payload. */
export function normalizeApiResponse(platform, raw) {
  const payload = raw?.data || raw?.result || raw;

  if (!payload || typeof payload !== "object") {
    return null;
  }

  const pick = (...keys) => {
    for (const key of keys) {
      const val = key.split(".").reduce((obj, k) => obj?.[k], payload);
      if (val) return val;
    }
    return "";
  };

  switch (platform) {
    case "tiktok":
      return {
        platform,
        title: pick("title", "desc") || "TikTok Video",
        thumbnail: pick("cover", "origin_cover", "thumbnail"),
        mp4: pick("play", "hdplay", "wmplay", "video"),
        mp3: pick("music", "music_info.play", "audio"),
      };

    case "instagram":
      return {
        platform,
        title: pick("title", "caption", "description") || "Instagram Media",
        thumbnail: pick("thumbnail", "image", "display_url", "thumb"),
        mp4: pick("video_url", "media", "download_url", "url", "video"),
        mp3: pick("audio", "music"),
      };

    case "facebook":
      return {
        platform,
        title: pick("title", "description", "desc") || "Facebook Video",
        thumbnail: pick("thumbnail", "image", "thumb", "picture"),
        mp4: pick("hd", "sd", "download_url", "video", "url", "mp4"),
        mp3: pick("audio", "music"),
      };

    default:
      return null;
  }
}
