import { NextResponse } from "next/server";
import { isAuthenticated } from "@/lib/auth";
import { saveConfig, getAdminConfig, CONFIG_STRING_FIELDS } from "@/lib/config";

export const dynamic = "force-dynamic";

/** POST /api/admin/config — persist admin panel settings to data/config.json. */
export async function POST(request) {
  if (!(await isAuthenticated())) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  try {
    const body = await request.json();
    const updates = {};

    for (const field of CONFIG_STRING_FIELDS) {
      updates[field] = String(body[field] ?? "");
    }

    if (body.adminUsername) updates.adminUsername = String(body.adminUsername);
    if (body.adminPassword) updates.adminPassword = String(body.adminPassword);

    const saved = saveConfig(updates);
    return NextResponse.json({ success: true, config: getAdminConfig() });
  } catch {
    return NextResponse.json({ error: "Failed to save configuration." }, { status: 500 });
  }
}

/** GET /api/admin/config — return current config for the admin dashboard. */
export async function GET() {
  if (!(await isAuthenticated())) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  return NextResponse.json(getAdminConfig());
}
