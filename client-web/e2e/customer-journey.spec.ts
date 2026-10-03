import { expect, test } from "@playwright/test";

test("public landing explains services and preserves each chosen plan", async ({ page, request }) => {
  // Compile the target once: this suite uses Next's on-demand dev server.
  await request.get("/plans");
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const plans = [
    ["Normal Apply", "NORMAL_APPLY"],
    ["Cold Apply", "COLD_APPLY"],
    ["Full-Throttle Sprint", "FULL_THROTTLE"],
  ];
  for (const [name, id] of plans) {
    await expect(page.getByRole("link", { name: `Choose ${name}`, exact: true }))
       .toHaveAttribute("href", `/plans?plan=${id}`);
  }
  await expect(page.getByLabel("Full name")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Upload resume", exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: "Choose Cold Apply", exact: true }).click();
   // The dev server compiles this route on first navigation, including on CI.
   await expect(page).toHaveURL(/\/plans\?plan=COLD_APPLY$/, { timeout: 20000 });
  await expect(page.getByRole("heading", { name: "Connect Clerk to open your workspace" })).toBeVisible();
});

test("mobile menu and FAQ work without overflow or fake result claims", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByLabel("Open navigation").click();
  await expect(page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("link", { name: "Plans", exact: true })).toBeVisible();
  const faq = page.locator("details").filter({ has: page.getByText("Does choosing a plan activate a campaign?", { exact: true }) });
  await faq.locator("summary").click();
  await expect(faq.getByText(/No\. Your selection is saved as an inquiry/)).toBeVisible();
  const fits = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
  expect(fits).toBe(true);
  await expect(page.getByText("Most joined path", { exact: true })).toHaveCount(0);
});

test("legacy workspace redirects; profile remains separate from public marketing", async ({ page }) => {
  await page.goto("/workspace", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/profile", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Connect Clerk to open your workspace" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Three ways to put your search in motion." })).toHaveCount(0);
});
