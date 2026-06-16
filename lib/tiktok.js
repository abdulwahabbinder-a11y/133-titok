/**
 * Validate that a string represents a recognizable TikTok URL.
 * Supports standard, mobile, and short-link formats.
 */
export function isValidTikTokUrl(input) {
  if (!input || typeof input !== "string") return false;

  const trimmed = input.trim();
  const pattern =
    /^https?:\/\/(?:(?:www|vm|vt)\.)?tiktok\.com\/(?:@[\w.-]+\/video\/\d+|[\w@./-]+|t\/[\w-]+)/i;

  return pattern.test(trimmed);
}

/** Normalize user input to a clean URL string. */
export function normalizeTikTokUrl(input) {
  let url = input.trim();
  if (!/^https?:\/\//i.test(url)) {
    url = `https://${url}`;
  }
  return url;
}
