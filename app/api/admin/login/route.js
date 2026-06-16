import { NextResponse } from "next/server";
import { validateCredentials, attachSessionCookie } from "@/lib/auth";

export const dynamic = "force-dynamic";

/** POST /api/admin/login — credential gate for the admin portal. */
export async function POST(request) {
  try {
    const { username, password } = await request.json();

    if (!username || !password) {
      return NextResponse.json(
        { error: "Username and password are required." },
        { status: 400 }
      );
    }

    if (!validateCredentials(username, password)) {
      return NextResponse.json({ error: "Invalid credentials." }, { status: 401 });
    }

    const response = NextResponse.json({ success: true });
    return attachSessionCookie(response);
  } catch {
    return NextResponse.json({ error: "Login failed." }, { status: 500 });
  }
}
