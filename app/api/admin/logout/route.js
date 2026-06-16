import { NextResponse } from "next/server";
import { clearSessionCookie } from "@/lib/auth";
import { getRedirectUrl } from "@/lib/url";

export const dynamic = "force-dynamic";

/** POST /api/admin/logout — destroy the admin session cookie. */
export async function POST(request) {
  const response = NextResponse.redirect(getRedirectUrl("/admin-portal", request), 303);
  return clearSessionCookie(response, request);
}
