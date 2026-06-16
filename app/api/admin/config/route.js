import { NextResponse } from "next/server";
import { isAuthenticated } from "@/lib/auth";
import { saveConfig } from "@/lib/config";

export const dynamic = "force-dynamic";

/** POST /api/admin/config — persist admin panel settings to data/config.json. */
export async function POST(request) {
  if (!(await isAuthenticated())) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  try {
    const body = await request.json();

    const updates = {
      googleAnalyticsId: String(body.googleAnalyticsId ?? ""),
      searchConsoleMeta: String(body.searchConsoleMeta ?? ""),
      adsTxtContent: String(body.adsTxtContent ?? ""),
      topBannerAdCode: String(body.topBannerAdCode ?? ""),
      bottomBannerAdCode: String(body.bottomBannerAdCode ?? ""),
    };

    if (body.adminUsername) updates.adminUsername = String(body.adminUsername);
    if (body.adminPassword) updates.adminPassword = String(body.adminPassword);

    const saved = saveConfig(updates);
    return NextResponse.json({ success: true, config: saved });
  } catch {
    return NextResponse.json({ error: "Failed to save configuration." }, { status: 500 });
  }
}

/** GET /api/admin/config — return current config for the admin dashboard. */
export async function GET() {
  if (!(await isAuthenticated())) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const { getConfig } = await import("@/lib/config");
  const config = getConfig();

  return NextResponse.json({
    googleAnalyticsId: config.googleAnalyticsId,
    searchConsoleMeta: config.searchConsoleMeta,
    adsTxtContent: config.adsTxtContent,
    topBannerAdCode: config.topBannerAdCode,
    bottomBannerAdCode: config.bottomBannerAdCode,
    adminUsername: config.adminUsername,
  });
}
