import crypto from "crypto";
import { cookies } from "next/headers";
import { getConfig } from "./config";

const COOKIE_NAME = "admin_session";

/** Derive a session token from current admin credentials. */
function buildSessionToken(username, password) {
  const secret = process.env.ADMIN_SESSION_SECRET || "tiktok-downloader-session";
  return crypto
    .createHash("sha256")
    .update(`${username}:${password}:${secret}`)
    .digest("hex");
}

/** Check whether the incoming request carries a valid admin session cookie. */
export async function isAuthenticated() {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_NAME)?.value;
  if (!token) return false;

  const { adminUsername, adminPassword } = getConfig();
  return token === buildSessionToken(adminUsername, adminPassword);
}

/** Issue an HTTP-only session cookie after successful login. */
export async function setAuthCookie() {
  const { adminUsername, adminPassword } = getConfig();
  const token = buildSessionToken(adminUsername, adminPassword);
  const cookieStore = await cookies();

  cookieStore.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
}

/** Remove the admin session cookie on logout. */
export async function clearAuthCookie() {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
}

/** Validate submitted credentials against config.json values. */
export function validateCredentials(username, password) {
  const { adminUsername, adminPassword } = getConfig();
  return username === adminUsername && password === adminPassword;
}
