"use client";

import dynamic from "next/dynamic";

import { clerkConfigured } from "../lib/auth-config";
import { SetupState } from "./authenticated-home";

const AuthenticatedHome = dynamic(() => import("./authenticated-home"), { ssr: false });

export default function AuthGate() {
  return clerkConfigured ? <AuthenticatedHome /> : <SetupState />;
}
