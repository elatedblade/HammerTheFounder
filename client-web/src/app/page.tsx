import type { Metadata } from "next";
import MarketingPage from "../components/marketing/MarketingPage";

export const metadata: Metadata = {
  title: "Hammer The Founder | A considered job search",
  description: "Human-operated application and founder outreach support for ambitious professionals.",
};

export default function HomePage() {
  return <MarketingPage />;
}
