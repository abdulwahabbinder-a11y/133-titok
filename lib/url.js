/**
 * Build a safe redirect URL using the client's Host header (never 0.0.0.0).
 */
export function getRedirectUrl(path, request) {
  const host = request.headers.get("x-forwarded-host") || request.headers.get("host");
  const proto =
    request.headers.get("x-forwarded-proto") ||
    (request.url.startsWith("https") ? "https" : "http");

  if (host && !host.startsWith("0.0.0.0")) {
    return new URL(path, `${proto}://${host}`);
  }

  try {
    const url = new URL(request.url);
    if (url.hostname === "0.0.0.0") {
      url.hostname = "localhost";
    }
    url.pathname = path;
    url.search = "";
    return url;
  } catch {
    return new URL(path, "http://localhost:3000");
  }
}
