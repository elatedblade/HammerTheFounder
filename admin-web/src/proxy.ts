import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher(["/workspace(.*)"]);
const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
const authMode = process.env.NEXT_PUBLIC_AUTH_MODE ?? (publishableKey ? "clerk" : "unconfigured");

export default clerkMiddleware(async (auth, request) => {
  if (authMode === "clerk" && publishableKey && isProtectedRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/(api|trpc)(.*)",
    "/__clerk/:path*",
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
  ],
};
