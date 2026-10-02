import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

import { AuthProvider } from "./auth-provider";

export const metadata: Metadata = {
  title: "Hammer The Founder | Admin",
  description: "Operations workspace for Hammer The Founder.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
