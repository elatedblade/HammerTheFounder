"use client";

import dynamic from "next/dynamic";

import { clerkConfigured } from "./auth-provider";
import { SetupState } from "./authenticated-home";

const AuthenticatedHome = dynamic(() => import("./authenticated-home"), { ssr: false });

export default function AuthGate() {
  return clerkConfigured ? <AuthenticatedHome /> : <SetupState />;
}
