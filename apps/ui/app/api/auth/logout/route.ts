import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function GET(req: NextRequest) {
  const cookieStore = await cookies();
  cookieStore.set("kappalake_token", "", { httpOnly: true, path: "/", maxAge: 0 });
  return NextResponse.redirect(new URL("/login", req.url));
}
