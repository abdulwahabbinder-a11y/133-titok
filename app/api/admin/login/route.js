import { NextResponse } from "next/server";
import { validateCredentials, attachSessionCookie } from "@/lib/auth";
import { getRedirectUrl } from "@/lib/url";

export const dynamic = "force-dynamic";

/** Parse credentials from JSON or standard HTML form POST. */
async function parseCredentials(request) {
  const contentType = request.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const body = await request.json();
    return { username: body.username, password: body.password, isJson: true };
  }

  const formData = await request.formData();
  return {
    username: formData.get("username"),
    password: formData.get("password"),
    isJson: false,
  };
}

/** POST /api/admin/login — supports HTML form and JSON clients. */
export async function POST(request) {
  try {
    const { username, password, isJson } = await parseCredentials(request);

    if (!username || !password) {
      if (isJson) {
        return NextResponse.json(
          { error: "Username and password are required." },
          { status: 400 }
        );
      }
      return NextResponse.redirect(getRedirectUrl("/admin-portal?error=missing", request), 303);
    }

    if (!validateCredentials(String(username), String(password))) {
      if (isJson) {
        return NextResponse.json({ error: "Invalid credentials." }, { status: 401 });
      }
      return NextResponse.redirect(getRedirectUrl("/admin-portal?error=invalid", request), 303);
    }

    if (isJson) {
      const response = NextResponse.json({ success: true });
      return attachSessionCookie(response, request);
    }

    const response = NextResponse.redirect(getRedirectUrl("/admin-portal", request), 303);
    return attachSessionCookie(response, request);
  } catch (err) {
    console.error("[/api/admin/login]", err.message);
    return NextResponse.redirect(getRedirectUrl("/admin-portal?error=failed", request), 303);
  }
}

/** GET /api/admin/login — redirect stray visits to the portal. */
export async function GET() {
  return NextResponse.redirect(new URL("/admin-portal", process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"));
}
