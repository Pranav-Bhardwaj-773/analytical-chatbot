import NextAuth from "next-auth";

import { authConfig } from "@/auth.config";
import { NextResponse } from "next/server";

const { auth } = NextAuth(authConfig);

const guestOnlyPaths = ["/login", "/register", "/verify-email", "/forgot-password"];
const publicPaths = [...guestOnlyPaths, "/reset-password"];

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLoggedIn = !!req.auth;

  const isPublicAuthApi =
    pathname.startsWith("/api/auth") || pathname.startsWith("/api/register");

  if (pathname.startsWith("/api/")) {
    if (isPublicAuthApi) {
      return NextResponse.next();
    }
    if (!isLoggedIn) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }
    return NextResponse.next();
  }

  const isPublicPage = publicPaths.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
  const isGuestOnlyPage = guestOnlyPaths.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );

  if (!isLoggedIn && !isPublicPage) {
    const login = new URL("/login", req.nextUrl);
    login.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(login);
  }

  // Allow /reset-password even when signed in (email link may open in an active session).
  if (isLoggedIn && isGuestOnlyPage) {
    return NextResponse.redirect(new URL("/", req.nextUrl));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
