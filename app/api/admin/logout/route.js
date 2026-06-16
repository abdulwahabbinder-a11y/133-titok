import { NextResponse } from "next/server";
import { clearSessionCookie } from "@/lib/auth";

export const dynamic = "force-dynamic";

/** POST /api/admin/logout — destroy the admin session cookie. */
export async function POST() {
  const response = NextResponse.json({ success: true });
  return clearSessionCookie(response);
}
