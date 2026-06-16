import crypto from "crypto";
import { cookies } from "next/headers";
import { getConfig } from "./config";

export const COOKIE_NAME = "admin_session";
const SESSION_MAX_AGE = 60 * 60 * 24 * 7;

/** Derive a session token from current admin credentials. */
export function buildSessionToken(username, password) {
  const secret = process.env.ADMIN_SESSION_SECRET || "tiktok-downloader-session";
  return crypto
    .createHash("sha256")
    .update(`${username}:${password}:${secret}`)
    .digest("hex");
}

/** Detect HTTPS from proxy headers or request URL. */
function isSecureRequest(request) {
  if (!request) return process.env.NODE_ENV === "production";
  const proto = request.headers.get("x-forwarded-proto");
  if (proto === "https") return true;
  try {
    return new URL(request.url).protocol === "https:";
  } catch {
    return process.env.NODE_ENV === "production";
  }
}

/** Standard cookie options for the admin session. */
export function getSessionCookieOptions(request) {
  return {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  };
}

/** Build the current valid session token from config credentials. */
export function getCurrentSessionToken() {
  const { adminUsername, adminPassword } = getConfig();
  return buildSessionToken(adminUsername, adminPassword);
}

/** Check whether the incoming request carries a valid admin session cookie. */
export async function isAuthenticated() {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_NAME)?.value;
  if (!token) return false;
  return token === getCurrentSessionToken();
}

/** Attach session cookie to a NextResponse (preferred for Route Handlers). */
export function attachSessionCookie(response, request) {
  const token = getCurrentSessionToken();
  response.cookies.set(COOKIE_NAME, token, getSessionCookieOptions(request));
  return response;
}

/** Remove session cookie from a NextResponse. */
export function clearSessionCookie(response, request) {
  response.cookies.set(COOKIE_NAME, "", {
    ...getSessionCookieOptions(request),
    maxAge: 0,
  });
  return response;
}

/** Validate submitted credentials against config.json values. */
export function validateCredentials(username, password) {
  const { adminUsername, adminPassword } = getConfig();
  return (
    String(username).trim() === String(adminUsername).trim() &&
    String(password) === String(adminPassword)
  );
}
