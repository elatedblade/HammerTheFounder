import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse, type NextFetchEvent, type NextRequest } from "next/server";
import { safeCustomerRedirect } from "./app/safe-redirect";

const isProtectedRoute = createRouteMatcher(["/workspace(.*)", "/profile(.*)", "/dashboard(.*)", "/plans(.*)"]);
const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
const authMode = process.env.NEXT_PUBLIC_AUTH_MODE ?? (publishableKey ? "clerk" : "unconfigured");

const authenticatedProxy = clerkMiddleware(async (auth, request) => {
  if (authMode === "clerk" && publishableKey && isProtectedRoute(request)) {
    const destination = `${request.nextUrl.pathname}${request.nextUrl.search}`;
    await auth.protect({ unauthenticatedUrl: new URL(`/sign-in?redirect_url=${encodeURIComponent(destination)}`, request.url).toString() });
  }
});

export default function proxy(request: NextRequest, event: NextFetchEvent) {
  if (request.nextUrl.pathname === "/dashboard" && request.nextUrl.searchParams.has("plan")) return NextResponse.redirect(new URL(safeCustomerRedirect(`/plans${request.nextUrl.search}`), request.url));
  if (authMode !== "clerk" || !publishableKey) return NextResponse.next();
  return authenticatedProxy(request, event);
}

export const config = {
  matcher: [
    "/(api|trpc)(.*)",
    "/__clerk/:path*",
    "/((?!_next|.*\\..*).*)",
  ],
};
