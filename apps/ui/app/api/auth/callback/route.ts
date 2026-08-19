import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { CONFIG } from "@/app/lib/config";

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");
  if (!code) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Exchange the authorization code for tokens (server-side).
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CONFIG.KC_CLIENT_ID,
    redirect_uri: CONFIG.KC_REDIRECT_URI,
    code,
  });

  let data: Record<string, unknown>;
  try {
    const res = await fetch(`${CONFIG.KC_ISSUER_INTERNAL}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`Token endpoint ${res.status}`);
    data = await res.json();
  } catch (e) {
    console.error("[OIDC] Token exchange failed:", e);
    return NextResponse.redirect(new URL("/login?error=token", req.url));
  }

  const cookieStore = await cookies();
  cookieStore.set("kappalake_token", String(data.access_token ?? ""), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: Number(data.expires_in ?? 300),
  });
  return NextResponse.redirect(new URL("/", req.url));
}
