import { NextResponse } from "next/server";
import { clearAuthCookie } from "@/lib/auth";

export const dynamic = "force-dynamic";

/** POST /api/admin/logout — destroy the admin session cookie. */
export async function POST() {
  await clearAuthCookie();
  return NextResponse.json({ success: true });
}
