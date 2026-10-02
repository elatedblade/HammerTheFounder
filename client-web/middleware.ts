import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher(["/workspace(.*)"]);

export default clerkMiddleware(async (auth, request) => {
  if (process.env.NEXT_PUBLIC_AUTH_MODE === "clerk" && isProtectedRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/(api|trpc)(.*)", "/__clerk/:path*", "/((?!_next|.*\\..*).*)"],
};
